#!/usr/bin/env bash
# setup_instance.sh — Phase I: GCP instance provisioning and Isaac Sim installation.
#
# THIS SCRIPT IS DIVIDED INTO TWO STEPS.
#
# STEP 1 (instance provisioning) creates a billable cloud resource.
# It must NOT be run without explicit Origin approval.
# The script stops after Step 1 and waits for the Executor to confirm
# Origin approval before proceeding to Step 2.
#
# STEP 2 (software installation) may be run only after the instance
# created in Step 1 has been reviewed and approved by Origin.
#
# To run only Step 2 against a pre-existing instance, comment out Step 1
# and set INSTANCE_NAME and ZONE to match the existing instance.
#
# Prerequisites (Step 1):
#   gcloud auth login
#   gcloud config set project <your-project-id>
#
# Prerequisites (Step 2):
#   The instance created in Step 1 must be RUNNING.
#   No NGC API key or other credential is required.
#
# Status: OPEN — not yet executed. See environment_requirements.md.
#
# Official Isaac Sim 4.2.0 requirements:
#   https://docs.isaacsim.omniverse.nvidia.com/4.2.0/installation/requirements.html
#   https://docs.isaacsim.omniverse.nvidia.com/4.2.0/installation/install_python.html

set -euo pipefail

INSTANCE_NAME="abr-isaac-sim-phase1"
ZONE="us-central1-a"
MACHINE_TYPE="g2-standard-8"       # 1× NVIDIA L4 24 GB VRAM
DISK_SIZE="100GB"
DISK_TYPE="pd-ssd"
IMAGE_FAMILY="common-cu123-ubuntu-2204-py310"
IMAGE_PROJECT="deeplearning-platform-release"

# ===========================================================================
# STEP 1 — INSTANCE PROVISIONING
# This step creates a billable resource. Stop here and obtain Origin approval
# before proceeding to Step 2.
# ===========================================================================

echo "=== STEP 1: Instance provisioning ==="
echo ""
echo "WARNING: This step creates a billable GCP resource."
echo "Instance : ${INSTANCE_NAME}"
echo "Zone     : ${ZONE}"
echo "Type     : ${MACHINE_TYPE} (1x NVIDIA L4, 24 GB VRAM)"
echo "Disk     : ${DISK_SIZE} ${DISK_TYPE}"
echo "Image    : ${IMAGE_FAMILY} (Ubuntu 22.04, CUDA 12.3, Python 3.10, driver 535)"
echo ""
echo "This step must NOT proceed without explicit Origin approval."
echo "If you have Origin approval, remove the exit line below and re-run."
echo ""

# REMOVE THIS EXIT TO PROCEED WITH PROVISIONING (requires Origin approval):
echo "EXIT: provisioning is gated. Remove the exit call in setup_instance.sh after Origin approval." >&2
exit 1

# --- Provisioning commands (run only after removing the exit above) ---

gcloud compute instances create "${INSTANCE_NAME}" \
  --zone="${ZONE}" \
  --machine-type="${MACHINE_TYPE}" \
  --image-family="${IMAGE_FAMILY}" \
  --image-project="${IMAGE_PROJECT}" \
  --boot-disk-size="${DISK_SIZE}" \
  --boot-disk-type="${DISK_TYPE}" \
  --maintenance-policy=TERMINATE \
  --restart-on-failure

echo ""
echo "=== Instance created. ==="
echo ""
echo "Before proceeding to Step 2, obtain Origin approval and confirm:"
echo "  1. The instance is listed as RUNNING in the GCP console."
echo "  2. Origin has reviewed the instance configuration above."
echo ""
echo "Then run Step 2 manually (copy the commands below into a new shell)."
echo ""
echo "=== STEP 2 is not run automatically. ==="
echo "=== Exiting after provisioning. ==="
exit 0

# ===========================================================================
# STEP 2 — SOFTWARE INSTALLATION
# Run this manually after Step 1 is complete and Origin has approved.
# Copy from here to the end into a shell with gcloud authenticated.
# ===========================================================================

# 2a. Confirm the GPU is visible.
echo "=== Step 2a: Verifying GPU ==="
gcloud compute ssh "${INSTANCE_NAME}" --zone="${ZONE}" -- \
  nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader

# 2b. Install Isaac Sim 4.2.0.2.
#
# pypi.nvidia.com is a public index; no API key or credential is required.
# OMNI_KIT_ACCEPT_EULA=Y is required; without it the process may hang.
#
# isaacsim==4.2.0.2 is the correct package version for Isaac Sim 4.2.0.
# (The pip version string includes a build suffix: 4.2.0.2, not 4.2.0.)
#
# numpy<2.0 is required; Isaac Sim 4.2.0 is not compatible with NumPy 2.x.
echo ""
echo "=== Step 2b: Installing Isaac Sim 4.2.0.2 ==="
gcloud compute ssh "${INSTANCE_NAME}" --zone="${ZONE}" -- bash -s << 'EOF'
set -euo pipefail

PYTHON=python3.10

${PYTHON} -m pip install --upgrade pip

${PYTHON} -m pip install \
  isaacsim==4.2.0.2 \
  "numpy<2.0" \
  --extra-index-url https://pypi.nvidia.com

echo ""
echo "=== Verifying import ==="
OMNI_KIT_ACCEPT_EULA=Y ${PYTHON} -c "import isaacsim; print('isaacsim import ok')"
EOF

# 2c. Copy the experiment script.
echo ""
echo "=== Step 2c: Copying experiment script ==="
gcloud compute scp \
  --zone="${ZONE}" \
  sim/phase1_single_joint.py \
  "${INSTANCE_NAME}":~/phase1_single_joint.py

echo ""
echo "=== Step 2 complete. ==="
echo ""
echo "To run Phase I experiment:"
echo "  gcloud compute ssh ${INSTANCE_NAME} --zone=${ZONE} -- \\"
echo "    env OMNI_KIT_ACCEPT_EULA=Y python3.10 ~/phase1_single_joint.py"
echo ""
echo "To retrieve observations after the run:"
echo "  gcloud compute scp \\"
echo "    ${INSTANCE_NAME}:~/phase1_observations.json \\"
echo "    sim/phase1_observations.json \\"
echo "    --zone=${ZONE}"
echo ""
echo "To shut down the instance when Phase I is complete:"
echo "  gcloud compute instances delete ${INSTANCE_NAME} --zone=${ZONE}"
