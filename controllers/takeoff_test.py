import asyncio

from mavsdk.asyncio import Mavsdk, Configuration, ComponentType
from mavsdk.asyncio.plugins.telemetry import TelemetryAsync
from mavsdk.asyncio.plugins.action import ActionAsync, ActionError


TAKEOFF_ALTITUDE = 2.0
HOVER_TIME = 5
ALTITUDE_TIMEOUT = 30


async def connect_to_drone():
    configuration = Configuration.create_with_component_type(
        ComponentType.GROUND_STATION
    )

    mavsdk = Mavsdk(configuration)

    print("Connecting to PX4...")

    await mavsdk.add_any_connection("udpin://0.0.0.0:14540")

    drone = await mavsdk.first_autopilot(10.0)

    if drone is None:
        raise RuntimeError("PX4 autopilot not discovered.")

    print("Connected to PX4!")

    return mavsdk, drone


async def check_vehicle_health(telemetry):
    print("\nChecking vehicle health...")

    health_stream = telemetry.subscribe_health()

    try:
        health = await asyncio.wait_for(
            anext(health_stream),
            timeout=10.0
        )
    finally:
        await health_stream.aclose()

    print(f"Local position: {health.is_local_position_ok}")
    print(f"Global position: {health.is_global_position_ok}")
    print(f"Home position: {health.is_home_position_ok}")
    print(f"Armable: {health.is_armable}")

    if not (
        health.is_local_position_ok
        and health.is_global_position_ok
        and health.is_home_position_ok
        and health.is_armable
    ):
        raise RuntimeError("Vehicle health check failed.")

    print("Vehicle health check passed!")


async def wait_for_armed(telemetry):
    print("Waiting for armed confirmation...")

    async def check():
        async for is_armed in telemetry.subscribe_armed():
            if is_armed:
                return

    await asyncio.wait_for(check(), timeout=5.0)

    print("Drone armed successfully!")


async def monitor_altitude(telemetry):
    print("\nMonitoring altitude...")

    async for position in telemetry.subscribe_position():

        altitude = position.relative_altitude_m

        print(f"Relative altitude: {altitude:.2f} m")

        if altitude >= TAKEOFF_ALTITUDE:
            return

    raise RuntimeError("Altitude monitoring stopped unexpectedly.")


async def main():
    mavsdk, drone = await connect_to_drone()

    telemetry = TelemetryAsync(drone)
    action = ActionAsync(drone)

    takeoff_command_accepted = False

    await check_vehicle_health(telemetry)

    print(
        f"\nSetting takeoff altitude to "
        f"{TAKEOFF_ALTITUDE} metres..."
    )

    try:
        await action.set_takeoff_altitude(TAKEOFF_ALTITUDE)

        print("Takeoff altitude configured.")

        print("\nArming drone...")

        await action.arm()

        await wait_for_armed(telemetry)

        print("\nSending takeoff command...")

        await action.takeoff()

        takeoff_command_accepted = True

        print("Takeoff command accepted!")

        await asyncio.wait_for(
            monitor_altitude(telemetry),
            timeout=ALTITUDE_TIMEOUT
        )

        print(
            f"\nTarget altitude of "
            f"{TAKEOFF_ALTITUDE:.2f} m reached!"
        )

        print(
            f"Hovering for {HOVER_TIME} seconds..."
        )

        await asyncio.sleep(HOVER_TIME)

    except ActionError as error:
        print(f"\nFlight operation failed: {error}")

    except asyncio.TimeoutError:
        print("\nOperation timed out.")

    except RuntimeError as error:
        print(f"\nRuntime error: {error}")

    finally:

        if takeoff_command_accepted:

            print("\nRequesting landing...")

            try:
                await action.land()

                print("Landing command accepted.")

            except ActionError as error:
                print(
                    f"Landing command failed: {error.result}"
                )

        else:
            print(
                "\nTakeoff was not accepted. "
                "No landing command will be sent."
            )


if __name__ == "__main__":
    asyncio.run(main())
