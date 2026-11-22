# M3: Multi-Waypoint Autonomous Flight Experiment

**Date:** 22 November 2026
**Project:** Automou Autonomous Drone
**Status:** SUCCESSFUL

## 1. Objective

Demonstrate autonomous execution of a sequential three-waypoint mission using PX4 SITL, Gazebo Sim, and MAVSDK.

The drone must:
- Connect to PX4.
- Complete vehicle health checks.
- Arm and take off to approximately 2 metres.
- Navigate through three local NED waypoints.
- Return to its starting horizontal position.
- Land and disarm.
- Automatically enter Hold mode after landing.

## 2. Environment

| Component | Version / Configuration |
|---|---|
| PX4 Autopilot | v1.17.0 |
| Gazebo Sim | 10.5.0 (Jetty) |
| MAVSDK | 4.2.1 |
| Python | 3.14.4 |
| Vehicle | X500 |
| Simulation | PX4 SITL |
| Control interface | MAVSDK native asyncio API |

## 3. Mission Configuration

Takeoff altitude: 2.0 metres.

Waypoint offsets relative to the actual starting position:

| Waypoint | North offset | East offset |
|---|---:|---:|
| 1 | +2.0 m | 0.0 m |
| 2 | +2.0 m | +2.0 m |
| 3 | 0.0 m | 0.0 m |

The mission maintained the starting altitude and yaw throughout navigation.

One Offboard session was used for all three waypoints.

## 4. Starting Position

Measured after takeoff:

| Coordinate | Value |
|---|---:|
| North | 0.03 m |
| East | -0.01 m |
| Down | -1.67 m |
| Yaw | 95.84° |

The measured takeoff altitude stabilized at approximately 1.86 m.

## 5. Navigation Results

### Waypoint 1

Target:
- North: 2.03 m
- East: -0.01 m
- Down: -1.67 m

Final reported distance: approximately 0.07 m.

**Result: SUCCESSFUL**

### Waypoint 2

Target:
- North: 2.03 m
- East: 1.99 m
- Down: -1.67 m

Final reported distance: approximately 0.15 m.

**Result: SUCCESSFUL**

### Waypoint 3

Target:
- North: 0.03 m
- East: -0.01 m
- Down: -1.67 m

This waypoint returned the vehicle to its starting horizontal position.

Final reported distance: approximately 0.05 m.

**Result: SUCCESSFUL**

## 6. Landing and Post-Flight Verification

After all waypoints were completed:

1. MAVSDK issued the landing command.
2. PX4 accepted the command.
3. PX4 entered LAND mode.
4. Landing was detected.
5. PX4 automatically disarmed the vehicle.
6. The controller confirmed ON_GROUND and DISARMED.
7. The controller detected that the vehicle remained in Offboard mode.
8. MAVSDK requested Hold mode.
9. Hold mode was confirmed.

Final PX4 checks:

| Check | Result |
|---|---|
| Armed state | Disarmed |
| Navigation mode | Hold |
| Failsafe | No |
| Preflight check | OK |
| Landing state | ON_GROUND |

## 7. Offboard Failsafe Configuration

| Parameter | Observed value | Meaning |
|---|---:|---|
| COM_OBL_RC_ACT | 4 | Land on Offboard control loss |
| COM_OF_LOSS_T | 1.0 s | Offboard-loss timeout |

COM_OBL_RC_ACT displayed the saved marker during verification. COM_OF_LOSS_T showed the correct active value, although no saved marker was displayed.

## 8. Final Outcome

**MISSION SUCCESSFUL**

All three waypoints were reached within the configured arrival tolerance.

The vehicle successfully:
- Armed.
- Took off.
- Navigated autonomously through three waypoints.
- Returned to its starting horizontal position.
- Landed.
- Disarmed.
- Automatically returned to Hold mode.

PX4 post-flight verification returned:

`Preflight check: OK`

## 9. Engineering Significance

This experiment demonstrates that Automou can execute a multi-stage autonomous navigation sequence using local NED coordinates and MAVSDK.

It also validates:
- Sequential waypoint execution.
- Position and velocity-based arrival detection.
- Continuous Offboard control across multiple waypoints.
- Autonomous landing and disarming.
- Post-flight mode cleanup.

This is a simulation milestone. It does not yet establish real-world flight readiness or validate physical hardware.

## 10. Next Development Direction

M3 establishes the foundation for more advanced autonomy.

The next development stage should build on this navigation capability by introducing higher-level mission planning and autonomous decision-making, while preserving the separation between the autonomy software and PX4 flight-control firmware.
