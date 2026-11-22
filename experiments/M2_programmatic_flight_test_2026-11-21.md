# M2: Programmatic Flight Control Test

**Project:** Automou
**Date:** 21 November 2026
**Status:** PASSED
**Environment:** PX4 SITL + Gazebo Sim 10.5.0
**Vehicle:** PX4 X500

## Objective

Verify that Automou's Python control software can communicate with PX4, monitor vehicle health, and execute a controlled takeoff, altitude verification, hover, and landing sequence.

## Software

- PX4 Autopilot v1.17.0
- MAVSDK Python v4.2.1
- Python 3.14.4
- Gazebo Sim 10.5.0
- Ubuntu 26.04.1 LTS

## Test Procedure

The controller executed the following sequence:

1. Connected to PX4 through MAVSDK over UDP.
2. Discovered the autopilot.
3. Checked vehicle health.
4. Verified local position, global position, home position, and armability.
5. Configured a takeoff altitude of 2.0 metres.
6. Armed the vehicle.
7. Issued the takeoff command.
8. Monitored relative altitude until the 2.0-metre target was reached.
9. Hovered for 5 seconds.
10. Issued the landing command.

## Results

| Test | Expected result | Observed result |
|---|---|---|
| PX4 connection | Successful | PASS |
| Vehicle health | All required checks true | PASS |
| Arming | Vehicle arms | PASS |
| Takeoff | Vehicle climbs | PASS |
| Altitude target | Reach 2.0 m | PASS |
| Hover | Hold for 5 seconds | PASS |
| Landing command | Accepted by PX4 | PASS |
| Final vehicle state | Disarmed | PASS |
| Failsafe | Not active | PASS |

## Final PX4 Status

```text
INFO [commander] Disarmed
INFO [commander] navigation mode: Hold
INFO [commander] in failsafe: no
INFO [commander] preflight check: ...
```

The final status confirmed that the vehicle was disarmed and not in failsafe.

## Conclusion

The M2 programmatic flight-control demonstration was successful.

Automou can now communicate with PX4, inspect vehicle telemetry and health, and execute a scripted flight sequence involving arming, takeoff, altitude monitoring, hovering, and landing.

This is a foundational flight-control capability. It does not yet demonstrate autonomous waypoint navigation, obstacle avoidance, or perception-based decision-making.

## Next Milestone

**M3: Waypoint Navigation**

Develop the ability to define navigation targets, determine the drone's current position, travel to specified waypoints, and verify arrival.
