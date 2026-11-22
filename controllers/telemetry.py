import asyncio

from mavsdk.asyncio import Mavsdk, Configuration, ComponentType
from mavsdk.asyncio.plugins.telemetry import TelemetryAsync


drone_state = {
    "armed": False,
    "battery": 0.0,
    "latitude": 0.0,
    "longitude": 0.0,
    "absolute_altitude": 0.0,
    "relative_altitude": 0.0,
    "local_position_ok": False,
    "global_position_ok": False,
    "home_position_ok": False,
    "armable": False,
}

async def connect_to_drone():
    configuration = Configuration.create_with_component_type(
        ComponentType.GROUND_STATION
    )

    mavsdk = Mavsdk(configuration)

    print("Connecting to PX4...")

    await mavsdk.add_any_connection("udpin://0.0.0.0:14540")

    print("Discovering autopilot...")

    drone = await mavsdk.first_autopilot(10.0)

    if drone is None:
        raise RuntimeError("PX4 autopilot not discovered")

    print("Connected to PX4 successfully!")

    return mavsdk, drone


async def monitor_armed_state(telemetry):
    async for is_armed in telemetry.subscribe_armed():
        drone_state["armed"] = is_armed


async def monitor_battery(telemetry):
    async for battery in telemetry.subscribe_battery():
        drone_state["battery"] = battery.remaining_percent


async def monitor_position(telemetry):
    async for position in telemetry.subscribe_position():
        drone_state["latitude"] = position.latitude_deg
        drone_state["longitude"] = position.longitude_deg
        drone_state["absolute_altitude"] = (
            position.absolute_altitude_m
        )
        drone_state["relative_altitude"] = (
            position.relative_altitude_m
        )

async def monitor_health(telemetry):
    print("Monitoring vehicle health...")

    async for health in telemetry.subscribe_health():
        drone_state["local_position_ok"] = health.is_local_position_ok
        drone_state["global_position_ok"] = health.is_global_position_ok
        drone_state["home_position_ok"] = health.is_home_position_ok
        drone_state["armable"] = health.is_armable


async def display_dashboard():
    while True:
        armed_status = (
            "ARMED" if drone_state["armed"] else "DISARMED"
        )

        print("\033[2J\033[H", end="")

        print("=" * 45)
        print("          AUTOMOU DRONE DASHBOARD")
        print("=" * 45)

        print("\nFLIGHT STATUS")
        print("-" * 45)
        print(f"Connection:         CONNECTED")
        print(f"Armed state:        {armed_status}")

        print("\nBATTERY")
        print("-" * 45)
        print(f"Battery level:      {drone_state['battery']:.1f}%")

        print("\nGPS POSITION")
        print("-" * 45)
        print(f"Latitude:           {drone_state['latitude']:.6f}")
        print(f"Longitude:          {drone_state['longitude']:.6f}")

        print("\nPREFLIGHT HEALTH")
        print("-" * 45)

        print(
        f"Local position:     "
        f"{'OK' if drone_state['local_position_ok'] else 'NOT READY'}"
        )

        print(
        f"Global position:    "
        f"{'OK' if drone_state['global_position_ok'] else 'NOT READY'}"
        )

        print(
        f"Home position:      "
        f"{'OK' if drone_state['home_position_ok'] else 'NOT READY'}"
        )

        print(
        f"Armable:            "
        f"{'YES' if drone_state['armable'] else 'NO'}"
        )

        print("\nALTITUDE")
        print("-" * 45)
        print(
            f"Absolute altitude:  "
            f"{drone_state['absolute_altitude']:.2f} m"
        )
        print(
            f"Relative altitude:  "
            f"{drone_state['relative_altitude']:.2f} m"
        )

        print("\n" + "=" * 45)
        print("Press Ctrl+C to stop monitoring.")

        await asyncio.sleep(1)


async def main():
    mavsdk, drone = await connect_to_drone()

    telemetry = TelemetryAsync(drone)

    await asyncio.gather(
        monitor_health(telemetry),
        monitor_armed_state(telemetry),
        monitor_battery(telemetry),
        monitor_position(telemetry),
        display_dashboard(),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nAutomou telemetry stopped.")
