import asyncio
import math

from mavsdk.asyncio import Mavsdk, Configuration, ComponentType

from mavsdk.asyncio.plugins.telemetry import TelemetryAsync
from mavsdk.asyncio.plugins.action import ActionAsync

from mavsdk.asyncio.plugins.offboard import (
    OffboardAsync,
    PositionNedYaw,
)

from mavsdk.plugins.telemetry import LandedState, FlightMode


# ==========================================
# FLIGHT CONFIGURATION
# ==========================================

TAKEOFF_ALTITUDE = 2.0
NORTH_DISTANCE = 2.0

TAKEOFF_ALTITUDE_TOLERANCE = 0.2
VERTICAL_VELOCITY_TOLERANCE = 0.2

ARRIVAL_TOLERANCE = 0.3
VELOCITY_TOLERANCE = 0.3

TAKEOFF_TIMEOUT = 40
NAVIGATION_TIMEOUT = 45
LANDING_TIMEOUT = 40

ARM_COMMAND_TIMEOUT = 10
TAKEOFF_COMMAND_TIMEOUT = 10
OFFBOARD_START_TIMEOUT = 10
LAND_COMMAND_TIMEOUT = 5

TELEMETRY_TIMEOUT = 5
CONNECTION_TIMEOUT = 10

STABILITY_TIME = 1.5

YAW_OFFSET = 0.0

CONNECTION_CHECK_INTERVAL = 0.5


# ==========================================
# CONNECTION
# ==========================================

async def connect_to_drone():

    configuration = Configuration.create_with_component_type(
        ComponentType.GROUND_STATION
    )

    sdk = Mavsdk(configuration)

    print("Connecting to PX4...")

    await sdk.add_any_connection(
        "udpin://0.0.0.0:14540"
    )

    drone = await asyncio.wait_for(
        sdk.first_autopilot(CONNECTION_TIMEOUT),
        timeout=CONNECTION_TIMEOUT + 2
    )

    if drone is None:
        raise RuntimeError("PX4 autopilot not discovered.")

    connected = await drone.is_connected()

    if not connected:
        raise RuntimeError("PX4 connection is not active.")

    print("Connected to PX4!")

    return sdk, drone


# ==========================================
# CONNECTION MONITORING
# ==========================================

async def monitor_connection(drone, stop_event):

    print("Connection monitor started.")

    while not stop_event.is_set():

        connected = await drone.is_connected()

        if not connected:

            raise RuntimeError(
                "CRITICAL: PX4 connection lost! "
                "Check QGroundControl immediately."
            )

        await asyncio.sleep(
            CONNECTION_CHECK_INTERVAL
        )

    print("Connection monitor stopped.")


# ==========================================
# FLIGHT SUPERVISION
# ==========================================

async def supervise_flight(drone, flight_coroutine):

    stop_event = asyncio.Event()

    flight_task = asyncio.create_task(
        flight_coroutine
    )

    monitor_task = asyncio.create_task(
        monitor_connection(drone, stop_event)
    )

    try:

        done, pending = await asyncio.wait(
            {flight_task, monitor_task},
            return_when=asyncio.FIRST_COMPLETED
        )

        if monitor_task in done:

            if monitor_task.cancelled():

                raise RuntimeError(
                    "Connection monitor unexpectedly cancelled."
                )

            error = monitor_task.exception()

            if error is not None:
                raise error

            raise RuntimeError(
                "Connection monitor stopped unexpectedly."
            )

        return flight_task.result()

    finally:

        stop_event.set()

        for task in (flight_task, monitor_task):

            if not task.done():
                task.cancel()

        await asyncio.gather(
            flight_task,
            monitor_task,
            return_exceptions=True
        )


# ==========================================
# TELEMETRY HELPERS
# ==========================================

async def get_local_position(telemetry):

    stream = telemetry.subscribe_position_velocity_ned()

    try:

        return await asyncio.wait_for(
            anext(stream),
            timeout=TELEMETRY_TIMEOUT
        )

    finally:
        await stream.aclose()


async def get_armed_state(telemetry):

    stream = telemetry.subscribe_armed()

    try:

        return await asyncio.wait_for(
            anext(stream),
            timeout=TELEMETRY_TIMEOUT
        )

    finally:
        await stream.aclose()


async def get_landed_state(telemetry):

    stream = telemetry.subscribe_landed_state()

    try:

        return await asyncio.wait_for(
            anext(stream),
            timeout=TELEMETRY_TIMEOUT
        )

    finally:
        await stream.aclose()


async def get_current_yaw(telemetry):

    stream = telemetry.subscribe_attitude_euler()

    try:

        attitude = await asyncio.wait_for(
            anext(stream),
            timeout=TELEMETRY_TIMEOUT
        )

        return attitude.yaw_deg

    finally:
        await stream.aclose()


# ==========================================
# VEHICLE HEALTH
# ==========================================

async def check_vehicle_health(telemetry):

    print("\nChecking vehicle health...")

    stream = telemetry.subscribe_health()

    try:

        health = await asyncio.wait_for(
            anext(stream),
            timeout=10
        )

    finally:
        await stream.aclose()

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

        raise RuntimeError(
            "Vehicle health check failed. Flight aborted."
        )

    armed = await get_armed_state(telemetry)

    if armed:
        raise RuntimeError("Vehicle is already armed.")

    landed = await get_landed_state(telemetry)

    if landed != LandedState.ON_GROUND:

        raise RuntimeError(
            f"Vehicle is not confirmed on ground: {landed}"
        )

    print("Vehicle health check passed!")
    print("Vehicle confirmed disarmed and on ground.")


# ==========================================
# ARMING
# ==========================================

async def wait_for_armed(telemetry):

    print("Waiting for armed confirmation...")

    async def monitor():

        async for armed in telemetry.subscribe_armed():

            if armed:
                return

    await asyncio.wait_for(
        monitor(),
        timeout=5
    )

    print("Drone armed successfully!")


# ==========================================
# TAKEOFF STABILITY
# ==========================================

async def monitor_takeoff_stability(
    telemetry,
    ground_down
):

    print("\nMonitoring takeoff and altitude stability...")

    target_down = ground_down - TAKEOFF_ALTITUDE

    stable_since = None
    last_print = 0

    async for state in telemetry.subscribe_position_velocity_ned():

        position = state.position
        velocity = state.velocity

        altitude = ground_down - position.down_m

        altitude_error = abs(
            position.down_m - target_down
        )

        vertical_speed = abs(
            velocity.down_m_s
        )

        now = asyncio.get_running_loop().time()

        if now - last_print >= 0.5:

            print(
                f"Altitude: {altitude:.2f} m | "
                f"Vertical speed: {vertical_speed:.2f} m/s"
            )

            last_print = now

        altitude_stable = (
            altitude_error <= TAKEOFF_ALTITUDE_TOLERANCE
        )

        velocity_stable = (
            vertical_speed <= VERTICAL_VELOCITY_TOLERANCE
        )

        if altitude_stable and velocity_stable:

            if stable_since is None:
                stable_since = now

            elif now - stable_since >= STABILITY_TIME:

                print("\nTakeoff altitude stabilized!")
                return

        else:
            stable_since = None

    raise RuntimeError(
        "Takeoff telemetry stream stopped unexpectedly."
    )


# ==========================================
# WAYPOINT NAVIGATION
# ==========================================

async def navigate_to_waypoint(
    telemetry,
    offboard,
    target_north,
    target_east,
    target_down,
    target_yaw
):

    print("\nStarting waypoint navigation...")

    target = PositionNedYaw(
        north_m=target_north,
        east_m=target_east,
        down_m=target_down,
        yaw_deg=target_yaw
    )

    await offboard.set_position_ned(target)

    print("Waypoint target sent.")

    arrival_start = None
    last_print = 0

    async for state in telemetry.subscribe_position_velocity_ned():

        position = state.position
        velocity = state.velocity

        north_error = target_north - position.north_m
        east_error = target_east - position.east_m
        down_error = target_down - position.down_m

        distance = math.sqrt(
            north_error ** 2
            + east_error ** 2
            + down_error ** 2
        )

        speed = math.sqrt(
            velocity.north_m_s ** 2
            + velocity.east_m_s ** 2
            + velocity.down_m_s ** 2
        )

        now = asyncio.get_running_loop().time()

        if now - last_print >= 0.5:

            print(
                f"Distance: {distance:.2f} m | "
                f"Speed: {speed:.2f} m/s"
            )

            last_print = now

        if (
            distance <= ARRIVAL_TOLERANCE
            and speed <= VELOCITY_TOLERANCE
        ):

            if arrival_start is None:
                arrival_start = now

            elif now - arrival_start >= STABILITY_TIME:

                print("\nWaypoint reached and stabilized!")
                return

        else:
            arrival_start = None

    raise RuntimeError(
        "Waypoint telemetry stream stopped unexpectedly."
    )


# ==========================================
# LANDING VERIFICATION
# ==========================================

async def wait_for_landed_state(telemetry):

    async for state in telemetry.subscribe_landed_state():

        if state == LandedState.ON_GROUND:
            return


async def wait_for_disarmed(telemetry):

    async for armed in telemetry.subscribe_armed():

        if not armed:
            return


async def wait_for_landing_and_disarming(telemetry):

    print("\nVerifying landing and disarming...")

    await asyncio.wait_for(
        asyncio.gather(
            wait_for_landed_state(telemetry),
            wait_for_disarmed(telemetry)
        ),
        timeout=LANDING_TIMEOUT
    )

    print("Landing confirmed: ON_GROUND.")
    print("Disarming confirmed: vehicle is DISARMED.")

    return True


# ==========================================
# FLIGHT MODE MONITORING
# ==========================================

async def wait_for_land_mode(telemetry):

    async for mode in telemetry.subscribe_flight_mode():

        if mode == FlightMode.LAND:
            return True


async def wait_for_offboard_mode(telemetry):

    async for mode in telemetry.subscribe_flight_mode():

        if mode == FlightMode.OFFBOARD:
            return True


# ==========================================
# LANDING / RECOVERY
# ==========================================

async def recover_and_land(action, telemetry):

    print("\nStarting landing procedure...")

    try:

        await asyncio.wait_for(
            action.land(),
            timeout=LAND_COMMAND_TIMEOUT
        )

        print("PX4 accepted the landing command.")

    except Exception as error:

        print(f"\nCRITICAL: Landing request failed: {error}")

        print(
            "Use QGroundControl immediately to command landing."
        )

        print(
            "PX4 Offboard-loss failsafe is configured to request "
            "Land after the configured timeout if Offboard "
            "setpoints are lost."
        )

        return False

    try:

        await asyncio.wait_for(
            wait_for_land_mode(telemetry),
            timeout=5
        )

        print("PX4 entered LAND mode.")

    except asyncio.TimeoutError:

        print("WARNING: LAND mode was not confirmed.")

    try:

        await wait_for_landing_and_disarming(telemetry)

        print("\nLANDING PROCEDURE COMPLETED SUCCESSFULLY.")

        return True

    except asyncio.TimeoutError:

        print("\nCRITICAL: Landing was not confirmed!")

        print("Check QGroundControl immediately.")
        print("Inspect PX4 commander status.")

        return False

    except Exception as error:

        print(
            f"\nCRITICAL: Landing verification failed: {error}"
        )

        print("Check QGroundControl immediately.")

        return False


# ==========================================
# FLIGHT SEQUENCE
# ==========================================

async def flight_sequence(
    telemetry,
    action,
    offboard
):

    # 1. Preflight checks.

    await check_vehicle_health(telemetry)

    # 2. Capture actual ground position.

    ground_state = await get_local_position(telemetry)

    ground_down = ground_state.position.down_m

    # 3. Configure takeoff altitude.

    await action.set_takeoff_altitude(
        TAKEOFF_ALTITUDE
    )

    # 4. Arm.

    print("\nArming drone...")

    await asyncio.wait_for(
        action.arm(),
        timeout=ARM_COMMAND_TIMEOUT
    )

    await wait_for_armed(telemetry)

    # 5. Takeoff.

    print("\nSending takeoff command...")

    await asyncio.wait_for(
        action.takeoff(),
        timeout=TAKEOFF_COMMAND_TIMEOUT
    )

    print("Takeoff command accepted!")

    await asyncio.wait_for(
        monitor_takeoff_stability(
            telemetry,
            ground_down
        ),
        timeout=TAKEOFF_TIMEOUT
    )

    # 6. Capture actual position and heading.

    state = await get_local_position(telemetry)

    position = state.position

    yaw = await get_current_yaw(telemetry)

    yaw = ((yaw + 180) % 360) - 180

    start_north = position.north_m
    start_east = position.east_m
    start_down = position.down_m

    print("\nStarting position:")

    print(f"North: {start_north:.2f} m")
    print(f"East:  {start_east:.2f} m")
    print(f"Down:  {start_down:.2f} m")
    print(f"Yaw:   {yaw:.2f} degrees")

    # 7. Calculate waypoint.

    target_north = start_north + NORTH_DISTANCE
    target_east = start_east
    target_down = start_down

    target_yaw = (
        (yaw + YAW_OFFSET + 180) % 360
    ) - 180

    print("\nDestination:")

    print(f"North: {target_north:.2f} m")
    print(f"East:  {target_east:.2f} m")
    print(f"Down:  {target_down:.2f} m")
    print(f"Yaw:   {target_yaw:.2f} degrees")

    # 8. Set initial position before Offboard.

    initial_position = PositionNedYaw(
        north_m=start_north,
        east_m=start_east,
        down_m=start_down,
        yaw_deg=yaw
    )

    await offboard.set_position_ned(
        initial_position
    )

    # 9. Start Offboard.

    print("\nStarting Offboard mode...")

    await asyncio.wait_for(
        offboard.start(),
        timeout=OFFBOARD_START_TIMEOUT
    )

    # 10. Verify Offboard mode.

    await asyncio.wait_for(
        wait_for_offboard_mode(telemetry),
        timeout=5
    )

    # IMPORTANT: is_active() is asynchronous in MAVSDK 4.2.1.

    active = await offboard.is_active()

    if not active:

        raise RuntimeError(
            "PX4 reports Offboard mode, but MAVSDK "
            "reports it inactive."
        )

    print(
        "Offboard mode confirmed by PX4 and MAVSDK!"
    )

    # 11. Navigate.

    await asyncio.wait_for(
        navigate_to_waypoint(
            telemetry,
            offboard,
            target_north,
            target_east,
            target_down,
            target_yaw
        ),
        timeout=NAVIGATION_TIMEOUT
    )

    print("\nWaypoint navigation successful!")

    # 12. Explicitly land after successful navigation.

    landing_success = await recover_and_land(
        action,
        telemetry
    )

    if not landing_success:

        raise RuntimeError(
            "Waypoint reached, but landing "
            "could not be confirmed."
        )

    print("\nAUTONOMOUS MISSION COMPLETED!")
    print("Takeoff: successful")
    print("Waypoint navigation: successful")
    print("Landing: successful")
    print("Disarming: confirmed")


# ==========================================
# MAIN CONTROLLER
# ==========================================

async def main():

    sdk, drone = await connect_to_drone()

    telemetry = TelemetryAsync(drone)
    action = ActionAsync(drone)
    offboard = OffboardAsync(drone)

    try:

        print("\nStarting supervised flight sequence...")

        await supervise_flight(
            drone,
            flight_sequence(
                telemetry,
                action,
                offboard
            )
        )

    except asyncio.CancelledError:

        print("\nCRITICAL: Flight controller cancelled!")

        raise

    except Exception as error:

        print(f"\nFLIGHT ERROR: {error}")

    finally:

        print("\nChecking vehicle state...")

        armed_now = None
        landed_now = None

        try:

            armed_now = await get_armed_state(telemetry)

            landed_now = await get_landed_state(telemetry)

            print(f"Armed: {armed_now}")
            print(f"Landed state: {landed_now}")

        except Exception as error:

            print(
                "\nWARNING: Cannot determine vehicle state: "
                f"{error}"
            )

            print(
                "Vehicle state is UNKNOWN. "
                "Do not assume the aircraft is safe."
            )

        already_safe = (
            armed_now is False
            and landed_now == LandedState.ON_GROUND
        )

        if already_safe:

            print(
                "\nVehicle confirmed on the ground "
                "and disarmed."
            )

        else:

            print(
                "\nWARNING: Vehicle safety state "
                "is not fully confirmed."
            )

            await recover_and_land(
                action,
                telemetry
            )

        # Keep SDK alive until recovery has been attempted.
        _ = sdk


# ==========================================
# ENTRY POINT
# ==========================================

if __name__ == "__main__":

    try:

        asyncio.run(main())

    except KeyboardInterrupt:

        print("\nController interrupted.")

        print(
            "If the aircraft is airborne, use QGroundControl "
            "to command landing immediately."
        )
