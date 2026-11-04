# Phase I — Execution Environment Requirements

**Status: OPEN — environment not yet provisioned.**

## Why this document exists

The Generator (Claude Chat session) prepared this configuration from a CPU-only
cloud container. That container has no NVIDIA GPU, no NVIDIA drivers, and no
NVIDIA container runtime. Isaac Sim cannot execute there.

This document records the exact environment required so the Executor can
provision it. All hardware and software specifications are derived from the
official Isaac Sim 4.2.0 documentation:
<https://docs.isaacsim.omniverse.nvidia.com/4.2.0/installation/requirements.html>
<https://docs.isaacsim.omniverse.nvidia.com/4.2.0/installation/install_python.html>

## GPU requirement — RT Cores mandatory

Isaac Sim 4.2.0 requires a GPU with RT Cores. The official documentation
explicitly states: "GPUs without RT Cores (A100, H100) are not supported."

| Tier | GPU | VRAM | RT Cores |
| --- | --- | --- | --- |
| Minimum (official) | GeForce RTX 3070 | 8 GB | Yes (Ampere, 2nd gen) |
| Good (official) | GeForce RTX 4080 | 16 GB | Yes (Ada, 3rd gen) |
| Ideal (official) | RTX Ada 6000 | 48 GB | Yes (Ada, 3rd gen) |
| NOT supported | A100 | any | No |
| NOT supported | H100 | any | No |

**NVIDIA L4 (GCP g2 instance):** The L4 is Ada Lovelace architecture with 3rd-gen
RT Cores. It is not in the official compatibility table. Forum reports confirm it
runs Isaac Sim 4.2.0 on Ubuntu 22.04 with driver 535. It is selected here as the
nearest available cloud GPU with RT Cores and adequate VRAM (24 GB).

**OPEN condition SIM-01:** L4 compatibility with Isaac Sim 4.2.0 is not officially
listed. Executor must confirm `nvidia-smi` shows the L4 and that Isaac Sim
launches without GPU device errors before proceeding to Phase I experiment.

## Minimum hardware requirements

| Resource | Official minimum | Selected configuration |
| --- | --- | --- |
| GPU | RTX 3070, 8 GB VRAM, with RT Cores | NVIDIA L4, 24 GB VRAM |
| NVIDIA driver (Linux) | 535.129.03 | 535+ (pre-installed on image) |
| CPU | not specified | 8 vCPU (g2-standard-8) |
| RAM | not specified | 32 GB |
| Disk | 50 GB SSD | 100 GB SSD |
| OS | Ubuntu 20.04 or 22.04 | Ubuntu 22.04 LTS |
| Python | 3.10 exactly | 3.10 (pre-installed on image) |

Isaac Sim pip requires Python 3.10 exactly. It is not compatible with 3.11, 3.12,
or later. The selected GCP image ships with Python 3.10.

## Software stack

| Component | Version | Source |
| --- | --- | --- |
| Isaac Sim | 4.2.0.2 | `pip install isaacsim==4.2.0.2 --extra-index-url https://pypi.nvidia.com` |
| numpy | <2.0 | pip |

The Isaac Sim pip index (`https://pypi.nvidia.com`) is a public index. No NGC API
key or other credential is required to install packages from it.

The `isaacsim==4.2.0.2` metapackage installs the full runtime. Additional
subpackages (`isaacsim-replicator`, `isaacsim-robot-setup`) are not required for
Phase I and must not be added without explicit scope expansion.

Isaac Sim 4.2.0 disk footprint after pip install: approximately 25 GB.
The 100 GB boot disk provides adequate headroom.

## EULA acceptance

Isaac Sim requires explicit EULA acceptance. Set the following environment
variable before running any Isaac Sim process:

```bash
export OMNI_KIT_ACCEPT_EULA=Y
```

Without this, the process may hang waiting for interactive input or exit with an
error. The variable must be set in every shell session that runs Isaac Sim.

## Recommended GCP instance

```
Machine type : g2-standard-8   (8 vCPU, 32 GB RAM, 1× NVIDIA L4 24 GB)
Zone         : us-central1-a
OS image     : projects/deeplearning-platform-release/global/images/family/
               common-cu123-ubuntu-2204-py310
               (pre-installed: Python 3.10, CUDA 12.3, driver 535+)
Boot disk    : 100 GB SSD (pd-ssd)
```

The NVIDIA deep learning image ships with the correct Python, CUDA, and driver
versions. Driver 535+ satisfies the Isaac Sim 4.2.0 Linux requirement (535.129.03).

**Provisioning creates a billable cloud resource and must not occur without
explicit Origin approval. See setup_instance.sh for the two-step procedure.**

## What the Executor must confirm before Phase I is complete

1. `nvidia-smi` shows the NVIDIA L4 with driver 535+. (Confirms OPEN SIM-01.)
2. `python3.10 -c "import isaacsim; print('import ok')"` returns `import ok`
   with `OMNI_KIT_ACCEPT_EULA=Y` set.
3. `python3.10 sim/phase1_single_joint.py` completes without Python exception or
   Isaac Sim device error.
4. `sim/phase1_observations.json` is written and contains the `isaac_sim_version`
   string and at least one joint-state record under `simulation_internal_observations`.
5. Origin and Verifier have reviewed `phase1_observations.json` and declared
   Phase I complete before any Phase II work begins.

No ABR mathematics are involved in Phase I. The Executor must not add them.
