# Self-region measurement declaration — DRAFT

**Status: OPEN — not authorized for operator evaluation.**

## Candidate physical system

ROBOTIS DYNAMIXEL XM430-W350-R (provisional), mounted as a single-axis joint with a lightweight arm. No actual hardware observation has been admitted.

| Candidate measurement | Unit | Source | Status |
| --- | --- | --- | --- |
| Joint position | device ticks; conversion to radians to be declared | DYNAMIXEL position feedback | OPEN: device mode, conversion, zero and direction |
| Joint velocity | device units; conversion to rad/s to be declared | DYNAMIXEL velocity feedback | OPEN: mode, scaling and provenance |
| Motor current | device units; conversion to A to be declared | DYNAMIXEL current feedback | OPEN: scaling, sampling and provenance |
| Supply voltage | V after documented scaling | DYNAMIXEL voltage feedback | OPEN: scaling and sampling |
| Temperature | degrees C after documented scaling | DYNAMIXEL temperature feedback | OPEN: sampling |
| Load-side torque | N·m | independent load-side torque sensor, not yet selected | OPEN: sensor absent |
| Commanded position/current | documented device units | issued command record, distinct from measured output | OPEN: command semantics |

Motor current must **not** be labeled direct measured torque. Derived torque, if later permitted, must retain its provenance and derivation.

## Unresolved declarations

- Domain D: physical joint, observed extent and operating envelope.
- M: exact sensor identity, observable basis, calibration, units, sample alignment and provenance.
- Topology: loci, edges, physical direction basis, and dimensional compatibility.
- Admission: hardware-specific bounds and rejected/missing-data behavior.
- Canonical Kernel V9 commit and IRRS interface contract.
- Hardware safety envelope and independent shutdown path.

**No A, B, R, Δ, Σ, or C result is claimed here.**
