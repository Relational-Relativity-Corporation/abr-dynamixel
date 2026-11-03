# ABR DYNAMIXEL — Relational Robotics Hardware Experiment

Status: **FOUNDATION / NOT YET EXPERIMENTALLY VERIFIED**

This repository will investigate whether a physical robot can observe and act upon declared relationships between its own mechanical state and its environment.

## Authority and evidence

Origin → IRRS admission → canonical `abr-kernel` V9 (Rust) → observable outcome → comparison with observation.

Only IRRS and the canonical ABR Kernel authorize relational mathematics. A passing build, synthetic fixture, or internally consistent trace is not verification of physical behavior. Verification requires comparison against independently observed outcomes.

## Initial hardware candidate

- Actuator: ROBOTIS DYNAMIXEL XM430-W350-R (**provisional; not yet purchased or connected**).
- Actuator observables to evaluate for admission: reported position, velocity, motor current, input voltage, temperature.
- Load-side torque: requires an **independent physical torque sensor**; torque derived from motor current is not a direct torque observation.
- Environmental sensor: RPLIDAR (**model, mounting, scan extent, and interface OPEN**).
- Actuator power, RS-485 interface, mounting, emergency stop, physical limits, and host connection: **OPEN**.

No actuator-specific bounds, calibration constants, physical edge directions, or observations are assumed.

## First bounded stage

1. Review the exact actuator and sensor hardware documentation.
2. Record the observable basis, units, extent, source, and provenance in `docs/m_declaration_self.md`.
3. Determine the IRRS admission contract and pin the exact canonical Kernel V9 revision.
4. Implement Rust acquisition and admitted operator calls **only after Origin and Verifier review**.
5. Compare actual observed behavior with calculated outcomes. Do not promote synthetic evidence to physical verification.

LiDAR coupling and R activation are separate future stages and remain OPEN.

## Relationship to existing work

`abr-robotics-demo` is a reference experiment, not a source of transferable physical observations or default limits. Do not import its simulation parameters or treat its trace identity as hardware verification.

## Repository discipline

- Rust canonical Kernel calls; no Python replacement of relational operators.
- No invented prior, topology, coupling constants, or measurement defaults.
- No smoothing, averaging, or statistical substitution in the relational path.
- No index-derived physical direction.
- Track DECLARED / CALCULATED / VERIFIED BY OBSERVATION / OPEN separately.
- One bounded increment per Origin/Verifier review.
