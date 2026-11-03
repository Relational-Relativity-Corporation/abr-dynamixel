# Phase I — Execution Environment Requirements

**Status: OPEN — environment not yet provisioned.**

## Why this document exists

The Generator (Claude Chat session) prepared this configuration from a CPU-only
cloud container. That container has no NVIDIA GPU, no NVIDIA drivers, and no
NVIDIA container runtime. Isaac Sim cannot execute there.

This document records the exact environment required so the Executor can
provision it and run `phase1_single_joint.py`.

## Minimum hardware requirements

| Resource | Minimum | Recommended |
| --- | --- | --- |
| GPU | NVIDIA T4 (16 GB VRAM) | NVIDIA L4 (24 GB VRAM) |
| NVIDIA driver | 525.85.12 | 535+ |
| CUDA | 12.0 | 12.3 |
| CPU | 4 vCPU | 8 vCPU |
| RAM | 16 GB | 32 GB |
| Disk | 60 GB SSD | 100 GB SSD |
| OS | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |
| Python | 3.10 exactly | 3.10 exactly |

Isaac Sim pip requires Python 3.10. It will not install on 3.11, 3.12, or 3.13.

## Software stack

| Component | Version | Source |
| --- | --- | --- |
| Isaac Sim | 4.2.0 | `pip install isaacsim==4.2.0 --extra-index-url https://pypi.nvidia.com` |
| isaacsim-replicator | 4.2.0 | same index |
| isaacsim-robot-setup | 4.2.0 | same index |
| numpy | <2.0 | pip |

Isaac Sim 4.2.0 disk footprint after pip install: approximately 25 GB.

## Recommended GCP instance

```
Machine type : g2-standard-8   (8 vCPU, 32 GB RAM, 1× NVIDIA L4 24 GB)
Zone         : us-central1-a
OS image     : projects/deeplearning-platform-release/global/images/family/
               common-cu123-ubuntu-2204-py310
               (pre-installed: Python 3.10, CUDA 12.3, driver 535+)
Boot disk    : 100 GB SSD (pd-ssd)
```

The NVIDIA deep learning image ships with the correct Python and CUDA version
and does not require manual driver installation.

## NGC credentials (required for NVIDIA packages)

An NGC API key is required to access `pypi.nvidia.com` and, if using Docker,
`nvcr.io`. Obtain one at https://ngc.nvidia.com/setup/api-key.

Set before running the install script:

```bash
export NGC_API_KEY=<your key>
```

## What the Executor must confirm before Phase I is complete

1. `python3.10 -c "import isaacsim; print('ok')"` returns `ok`.
2. `python3.10 sim/phase1_single_joint.py` completes without error.
3. `sim/phase1_observations.json` is written and contains at least one
   joint-state record.
4. The Isaac Sim version string is recorded in that file.

No ABR mathematics are involved in Phase I. The Executor must not add them.
