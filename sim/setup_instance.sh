#!/usr/bin/env bash
# setup_instance.sh — provision a GCP GPU instance and install Isaac Sim
#
# Run this from any machine with gcloud authenticated to the target project.
# The script creates the instance, waits for it to be ready, then SSHs in
# to install Isaac Sim pip packages.
#
# Prerequisites:
#   gcloud auth login
#   gcloud config set project <your-project-id>
#   export NGC_API_KEY=<your NGC API key>
#
# Status: OPEN — not yet executed. See environment_requirements.md.

set -euo pipefail

INSTANCE_NAME="abr-isaac-sim-phase1"
ZONE="us-central1-a"
MACHINE_TYPE="g2-standard-8"       # 1× NVIDIA L4 24 GB VRAM
DISK_SIZE="100GB"
DISK_TYPE="pd-ssd"
IMAGE_FAMILY="common-cu123-ubuntu-2204-py310"
IMAGE_PROJECT="deeplearning-platform-release"

: "${NGC_API_KEY:?NGC_API_KEY must be set}"

echo "=== Creating GCP instance: ${INSTANCE_NAME} in ${ZONE} ==="
gcloud compute instances create "${INSTANCE_NAME}" \
  --zone="${ZONE}" \
  --machine-type="${MACHINE_TYPE}" \
  --image-family="${IMAGE_FAMILY}" \
  --image-project="${IMAGE_PROJECT}" \
  --boot-disk-size="${DISK_SIZE}" \
  --boot-disk-type="${DISK_TYPE}" \
  --maintenance-policy=TERMINATE \
  --restart-on-failure \
  --metadata="install-nvidia-driver=True"

echo ""
echo "=== Waiting 60 s for instance to reach RUNNING state ==="
sleep 60

echo ""
echo "=== Verifying GPU is visible ==="
gcloud compute ssh "${INSTANCE_NAME}" --zone="${ZONE}" -- \
  nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader

echo ""
echo "=== Installing Isaac Sim 4.2.0 ==="
gcloud compute ssh "${INSTANCE_NAME}" --zone="${ZONE}" -- bash -s << EOF
set -euo pipefail

# Isaac Sim pip requires Python 3.10 exactly (pre-installed on this image)
PYTHON=python3.10

\${PYTHON} -m pip install --upgrade pip

# NGC token for pypi.nvidia.com
pip config set global.extra-index-url \
  "https://\${NGC_API_KEY}@pypi.nvidia.com"

\${PYTHON} -m pip install \
  isaacsim==4.2.0 \
  isaacsim-replicator==4.2.0 \
  isaacsim-robot-setup==4.2.0 \
  "numpy<2.0"

echo "Isaac Sim install complete."
\${PYTHON} -c "import isaacsim; print('Import OK')"
EOF

echo ""
echo "=== Copying experiment script to instance ==="
gcloud compute scp \
  --zone="${ZONE}" \
  sim/phase1_single_joint.py \
  "${INSTANCE_NAME}":~/phase1_single_joint.py

echo ""
echo "=== Setup complete. ==="
echo "To run Phase I:"
echo "  gcloud compute ssh ${INSTANCE_NAME} --zone=${ZONE} -- \\"
echo "    python3.10 ~/phase1_single_joint.py"
echo ""
echo "To retrieve observations:"
echo "  gcloud compute scp ${INSTANCE_NAME}:~/phase1_observations.json \\"
echo "    sim/phase1_observations.json --zone=${ZONE}"
echo ""
echo "To shut down the instance when done:"
echo "  gcloud compute instances delete ${INSTANCE_NAME} --zone=${ZONE}"
