import asyncio

from mavsdk.asyncio import Mavsdk, Configuration, ComponentType
from mavsdk.asyncio.plugins.telemetry import TelemetryAsync


async def main():
    print("Connecting to PX4...")

    sdk = Mavsdk(
        Configuration.create_with_component_type(
            ComponentType.GROUND_STATION
        )
    )

    await sdk.add_any_connection("udpin://0.0.0.0:14540")

    drone = await sdk.first_autopilot(10.0)

    print("Connected to PX4!")

    telemetry = TelemetryAsync(drone)

    print("\nReading local position...")
    print("Press Ctrl+C to stop.\n")

    async for position in telemetry.subscribe_position_velocity_ned():

        pos = position.position
        vel = position.velocity

        print("-" * 40)

        print("LOCAL POSITION (NED)")
        print(f"North: {pos.north_m:.2f} m")
        print(f"East:  {pos.east_m:.2f} m")
        print(f"Down:  {pos.down_m:.2f} m")

        print("\nVELOCITY (NED)")
        print(f"North: {vel.north_m_s:.2f} m/s")
        print(f"East:  {vel.east_m_s:.2f} m/s")
        print(f"Down:  {vel.down_m_s:.2f} m/s")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nPosition monitoring stopped.")
