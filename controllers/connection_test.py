import asyncio

from mavsdk.asyncio import Mavsdk, Configuration, ComponentType


async def main():
    configuration = Configuration.create_with_component_type(
        ComponentType.GROUND_STATION
    )

    mavsdk = Mavsdk(configuration)

    print("Connecting to PX4 SITL...")

    await mavsdk.add_any_connection("udpin://0.0.0.0:14540")

    print("Waiting for PX4 autopilot...")

    drone = await mavsdk.first_autopilot(10.0)

    if drone is None:
        print("FAILED: No PX4 autopilot discovered.")
        return

    print("SUCCESS: Connected to PX4!")
    print("Automou communication link established.")


if __name__ == "__main__":
    asyncio.run(main())
