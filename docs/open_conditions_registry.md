# OPEN conditions — initial foundation

| ID | Condition | Required resolution |
| --- | --- | --- |
| SIM-01 | NVIDIA L4 compatibility with Isaac Sim 4.2.0 | Executor confirms `nvidia-smi` and Isaac Sim launches without GPU device error on the provisioned instance; L4 is not in the official 4.2.0 GPU table |
| HW-01 | Exact DYNAMIXEL actuator and firmware | Origin hardware selection and documented feedback interface |
| HW-02 | Independent load-side torque sensor | Origin sensor selection, calibration and physical measurement |
| HW-03 | Power, RS-485 adapter, mounting, safety | Physical hardware design and review |
| IRRS-01 | Admission schema and provenance | Canonical IRRS contract reviewed |
| K-01 | Exact canonical ABR Kernel V9 revision and APIs | Pinned Rust dependency, interface review |
| M-SELF-01 | Self-region D and M | Observable units, extent, calibration, basis and direction declared |
| M-ENV-01 | LiDAR model and D/M | Physical observation provenance and declared extent |
| M-CROSS-01 | Cross-region topology and coupling | Observational basis and Origin declaration |
| R-01 | R admissibility and semantics | Canonical V9 source review and Origin declaration |
| OBS-01 | Physical observation and independent comparison | Actual acquired data and observable result |

All conditions are **OPEN**. This is a documentation foundation only; no build, hardware execution, or physical verification has occurred.

SIM-01 was added when Phase I preparation identified that the NVIDIA L4 GPU (Ada Lovelace, RT Cores present) is not in the official Isaac Sim 4.2.0 compatibility table, though forum evidence suggests it functions with driver 535 on Ubuntu 22.04.
