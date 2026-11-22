import asyncio

from mavsdk.asyncio import Mavsdk, Configuration, ComponentType
from mavsdk.asyncio.plugins.telemetry import TelemetryAsync
from mavsdk.asyncio.plugins.action import ActionAsync, ActionError


async def connect_to_drone():
    configuration = Configuration.create_with_component_type(
        ComponentType.GROUND_STATION
    )

    mavsdk = Mavsdk(configuration)

    print("Connecting to PX4...")

    await mavsdk.add_any_connection("udpin://0.0.0.0:14540")

    drone = await mavsdk.first_autopilot(10.0)

    if drone is None:
        raise RuntimeError("PX4 autopilot not discovered")

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

    if not health.is_armable:
        raise RuntimeError("Vehicle is not ready to arm.")

    print("\nVehicle health check passed!")


async def arm_drone(action, telemetry):
    print("\nRequesting PX4 to arm...")

    try:
        await action.arm()
        print("PX4 accepted the arming command.")

    except ActionError as error:
        print(f"Arming failed: {error.result}")
        return

    async def wait_for_armed():
        async for is_armed in telemetry.subscribe_armed():
            if is_armed:
                return

    try:
        await asyncio.wait_for(wait_for_armed(), timeout=5.0)
        print("SUCCESS: Automou armed the drone!")

    except asyncio.TimeoutError:
        print("Arming confirmation timed out.")
        return

    print("\nDisarming after successful test...")

    try:
        await action.disarm()
        print("Disarm command accepted.")

    except ActionError as error:
        print(f"Disarming failed: {error.result}")


async def main():
    mavsdk, drone = await connect_to_drone()

    telemetry = TelemetryAsync(drone)
    action = ActionAsync(drone)

    await check_vehicle_health(telemetry)

    await arm_drone(action, telemetry)


if __name__ == "__main__":
    asyncio.run(main())
