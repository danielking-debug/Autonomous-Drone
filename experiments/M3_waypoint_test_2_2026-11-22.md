# M3 Autonomous Waypoint Navigation Test 2

**Date:** 22 November 2026
**Project:** Automou Autonomous Drone
**Status:** SUCCESSFUL

## 1. Test Environment

- Flight controller: PX4 v1.17.0
- Simulator: Gazebo Sim 10.5.0 (Jetty)
- Simulated vehicle: X500
- Control interface: MAVSDK 4.2.1
- Python: 3.14.4
- Flight mode: Offboard
- Coordinate system: Local NED

## 2. Mission Objective

Execute an autonomous single-waypoint mission:

1. Arm the vehicle.
2. Take off to approximately 2 metres.
3. Navigate 2 metres north.
4. Maintain east position, altitude and yaw.
5. Stabilize at the destination.
6. Land automatically.
7. Confirm disarming.

## 3. Flight Results

### Takeoff

- Takeoff successful.
- Stabilized altitude: approximately 1.87 m.

### Waypoint Navigation

Starting position:
- North: 1.96 m
- East: 0.02 m
- Down: -1.73 m
- Yaw: 101.04°

Destination:
- North: 3.96 m
- East: 0.02 m
- Down: -1.73 m
- Yaw: 101.04°

Results:
- Offboard mode confirmed by PX4 and MAVSDK.
- Waypoint reached successfully.
- Final distance to target: approximately 0.10 m.
- Position stabilization successful.

### Landing

- PX4 accepted the landing command.
- LAND mode confirmed.
- Landing detected.
- Vehicle disarmed automatically.
- Landed state confirmed as ON_GROUND.

## 4. Final Vehicle Verification

Immediately after landing:
- Armed: False
- Landed state: ON_GROUND
- Navigation mode: Offboard
- Failsafe: No

Post-flight cleanup:
- Switched navigation mode to Hold through QGroundControl.
- Final commander status: Disarmed.
- Final navigation mode: Hold.
- Failsafe: No.
- Preflight check: OK.

## 5. Conclusion

The second autonomous waypoint mission completed successfully.

The test demonstrated:
- Programmatic arming and takeoff.
- Local NED waypoint positioning.
- Autonomous navigation.
- Destination stabilization.
- Automated landing and disarming.

The post-landing Offboard mode was manually returned to Hold. This remains a controller cleanup improvement to investigate.

**M3 single-waypoint navigation: SUCCESSFUL.**
