"""
phase1_single_joint.py — Phase I: establish Isaac Sim execution environment.

Scope (Section 5 of the integration proposal):
  1. Isaac Sim starts successfully.
  2. A basic articulated robot scene loads.
  3. A simulated joint can receive a command.
  4. The joint's resulting state can be observed.
  5. Observations and commands can be exchanged with the external process.

This script is the external process. It drives Isaac Sim headlessly, issues one
position command to a single revolute joint, reads back the resulting joint state
at each physics step, and writes the evidence to phase1_observations.json.

Observation provenance:
  simulation_internal_observations — joint position and velocity read from the
      Isaac Sim physics engine via ArticulationView. These values exist only
      inside the simulator during execution.
  external_record — the phase1_observations.json file written to disk after the
      simulation loop ends and before simulator shutdown. This is the only form
      of the observations accessible to an external process (Origin, Verifier,
      or any subsequent stage) after this script exits.

NO ABR mathematics are present here. This script only establishes that the
simulation environment works and produces accessible joint observations.
ABR kernel calls are authorised in Phase II only.

Status: OPEN — awaiting execution on a GPU instance.
See environment_requirements.md for hardware and software prerequisites.

Authority: Section 5 / Section 13 of the integration proposal.

Prerequisites:
  export OMNI_KIT_ACCEPT_EULA=Y   (must be set before running)
  Python 3.10 exactly
  isaacsim==4.2.0.2 installed via pip from https://pypi.nvidia.com
  NVIDIA GPU with RT Cores and driver 535+
"""

import json
import sys
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# 0. Pre-flight check: EULA acceptance
# ---------------------------------------------------------------------------
# Isaac Sim requires OMNI_KIT_ACCEPT_EULA=Y. Without it the process may hang
# or exit without a clear error. Check early so the error is explicit.

if os.environ.get("OMNI_KIT_ACCEPT_EULA", "").upper() not in ("Y", "YES", "1"):
    print(
        "[Phase I] ERROR: OMNI_KIT_ACCEPT_EULA is not set to Y.\n"
        "  Set it before running:\n"
        "    export OMNI_KIT_ACCEPT_EULA=Y\n"
        "  or prepend it to this command:\n"
        "    env OMNI_KIT_ACCEPT_EULA=Y python3.10 phase1_single_joint.py",
        file=sys.stderr,
    )
    sys.exit(1)

# ---------------------------------------------------------------------------
# 1. Launch Isaac Sim in headless mode
# ---------------------------------------------------------------------------
# SimulationApp must be imported and constructed before any other omni import.

from isaacsim import SimulationApp  # noqa: E402

CONFIG = {
    "headless": True,
    "hide_ui": True,
    "renderer": "RayTracedLighting",
}

print("[Phase I] Launching Isaac Sim (headless)...")
simulation_app = SimulationApp(CONFIG)

# Record Isaac Sim version immediately after launch.
import carb  # noqa: E402
kit_version = carb.settings.get_settings().get("/app/version")
print(f"[Phase I] Isaac Sim kit version: {kit_version}")

# ---------------------------------------------------------------------------
# 2. Import Isaac Sim modules (only after SimulationApp is constructed)
# ---------------------------------------------------------------------------

import numpy as np  # noqa: E402
from omni.isaac.core import World  # noqa: E402
from omni.isaac.core.articulations import ArticulationView  # noqa: E402

# ---------------------------------------------------------------------------
# 3. Build the scene — one revolute joint from USD primitives
# ---------------------------------------------------------------------------
# We create a minimal USD stage programmatically:
#   - A fixed base cube (kinematic rigid body — no dynamics)
#   - A moving arm cube (dynamic rigid body, 1 kg)
#   - A single revolute joint connecting them (Z axis)
#   - A position-control DriveAPI on the joint
#   - ArticulationRootAPI on the base
#
# No URDF or external asset is loaded; this keeps Phase I self-contained.

print("[Phase I] Creating world...")
world = World(stage_units_in_meters=1.0)

from pxr import UsdGeom, UsdPhysics, Gf, Sdf  # noqa: E402

stage = world.stage

# Root xform
root_path = "/World"
UsdGeom.Xform.Define(stage, root_path)

# --- Base (fixed rigid body) ---
base_path = f"{root_path}/Base"
base_cube = UsdGeom.Cube.Define(stage, base_path)
base_cube.GetSizeAttr().Set(0.1)
UsdGeom.XformCommonAPI(base_cube).SetTranslate(Gf.Vec3d(0.0, 0.0, 0.05))

base_rb = UsdPhysics.RigidBodyAPI.Apply(stage.GetPrimAtPath(base_path))
base_rb.CreateKinematicEnabledAttr(True)   # fixed — no dynamics

mass_api = UsdPhysics.MassAPI.Apply(stage.GetPrimAtPath(base_path))
mass_api.CreateMassAttr(0.0)               # kinematic, mass irrelevant

# --- Arm (dynamic rigid body) ---
arm_path = f"{root_path}/Arm"
arm_cube = UsdGeom.Cube.Define(stage, arm_path)
arm_cube.GetSizeAttr().Set(0.05)
UsdGeom.XformCommonAPI(arm_cube).SetTranslate(Gf.Vec3d(0.0, 0.0, 0.2))

arm_rb = UsdPhysics.RigidBodyAPI.Apply(stage.GetPrimAtPath(arm_path))
arm_mass = UsdPhysics.MassAPI.Apply(stage.GetPrimAtPath(arm_path))
arm_mass.CreateMassAttr(1.0)

# --- Revolute joint (Z axis) ---
joint_path = f"{root_path}/RevoluteJoint"
joint = UsdPhysics.RevoluteJoint.Define(stage, joint_path)
joint.CreateBody0Rel().SetTargets([Sdf.Path(base_path)])
joint.CreateBody1Rel().SetTargets([Sdf.Path(arm_path)])
joint.CreateAxisAttr("Z")
joint.CreateLowerLimitAttr(-180.0)         # degrees
joint.CreateUpperLimitAttr(180.0)

# Drive API — position control
# Units for DriveAPI angular drive: degrees for target position, N·m/deg for
# stiffness and damping in the Isaac Sim 4.x PhysX backend. These values are
# chosen only to produce visible motion in the simulation; they are not ABR
# control parameters and are not declared in any M structure.
drive = UsdPhysics.DriveAPI.Apply(stage.GetPrimAtPath(joint_path), "angular")
drive.CreateTypeAttr("force")
drive.CreateTargetPositionAttr(0.0)        # start at 0 degrees
drive.CreateStiffnessAttr(1000.0)
drive.CreateDampingAttr(100.0)
drive.CreateMaxForceAttr(1000.0)

# --- Articulation root on the base ---
UsdPhysics.ArticulationRootAPI.Apply(stage.GetPrimAtPath(base_path))

# ---------------------------------------------------------------------------
# 4. Reset world and get the ArticulationView
# ---------------------------------------------------------------------------

print("[Phase I] Resetting world...")
world.reset()

art_view = ArticulationView(
    prim_paths_expr=f"{root_path}/Base",
    name="single_joint_view",
)
world.scene.add(art_view)
world.reset()
art_view.initialize()

num_dof = art_view.num_dof
print(f"[Phase I] Articulation DOF count: {num_dof}")

# ---------------------------------------------------------------------------
# 5. Record initial joint state (observation before command)
# ---------------------------------------------------------------------------

world.step(render=False)

pos_before = art_view.get_joint_positions()      # shape: (1, num_dof)
vel_before = art_view.get_joint_velocities()

obs_initial = {
    "step": 0,
    "joint_position_rad": float(pos_before[0, 0]),
    "joint_velocity_rad_s": float(vel_before[0, 0]),
    "command_applied": None,
    "provenance": "simulation_internal",
}
print(f"[Phase I] Initial state: pos={obs_initial['joint_position_rad']:.4f} rad  "
      f"vel={obs_initial['joint_velocity_rad_s']:.4f} rad/s")

# ---------------------------------------------------------------------------
# 6. Issue a position command (45 degrees = π/4 rad)
# ---------------------------------------------------------------------------
# This target is supplied as the commanded position for Phase I demonstration.
# It is not a declared relational target. No tolerance or success criterion is
# asserted here; convergence assessment is left to Origin and Verifier.

TARGET_POSITION_RAD = np.pi / 4.0            # 45 degrees
TARGET_POSITION_DEG = np.degrees(TARGET_POSITION_RAD)

print(f"[Phase I] Sending position command: {TARGET_POSITION_DEG:.1f} deg "
      f"({TARGET_POSITION_RAD:.4f} rad)")

# ArticulationView.set_joint_position_targets expects radians.
art_view.set_joint_position_targets(
    np.array([[TARGET_POSITION_RAD]], dtype=np.float32)
)

command_record = {
    "type": "position_target",
    "value_rad": float(TARGET_POSITION_RAD),
    "value_deg": float(TARGET_POSITION_DEG),
}

# ---------------------------------------------------------------------------
# 7. Step simulation and collect observations
# ---------------------------------------------------------------------------
# Physics rate is 60 Hz by default. 60 steps ≈ 1 simulated second.
# All observations here are simulation-internal: they come from the physics
# engine via ArticulationView. They are recorded to become the external record
# written in Step 8.

N_STEPS = 60
simulation_internal_observations = [obs_initial]

for step in range(1, N_STEPS + 1):
    world.step(render=False)

    pos = art_view.get_joint_positions()
    vel = art_view.get_joint_velocities()

    simulation_internal_observations.append({
        "step": step,
        "joint_position_rad": float(pos[0, 0]),
        "joint_velocity_rad_s": float(vel[0, 0]),
        "command_applied": command_record if step == 1 else None,
        "provenance": "simulation_internal",
    })

final_pos_rad = simulation_internal_observations[-1]["joint_position_rad"]
final_pos_deg = np.degrees(final_pos_rad)
error_from_target_rad = final_pos_rad - TARGET_POSITION_RAD

print(f"[Phase I] Final joint position after {N_STEPS} steps: "
      f"{final_pos_deg:.4f} deg  ({final_pos_rad:.5f} rad)")
print(f"[Phase I] Error from target: {np.degrees(error_from_target_rad):.4f} deg  "
      f"({error_from_target_rad:.5f} rad)")

# ---------------------------------------------------------------------------
# 8. Write evidence file (the external record)
# ---------------------------------------------------------------------------
# This file is the boundary between the simulator and the external process.
# After this script exits, simulation_internal_observations exist only here.
# Origin and Verifier must review this file to determine Phase I outcome.

evidence = {
    "phase": "I",
    "task": "1 — Establish Isaac Sim execution environment",
    "proposal_section": "5",
    "isaac_sim_version": kit_version,
    "python_version": sys.version,
    "scene_description": {
        "base_prim": base_path,
        "arm_prim": arm_path,
        "joint_prim": joint_path,
        "joint_type": "revolute",
        "joint_axis": "Z",
        "control_mode": "position_target",
        "num_dof": num_dof,
    },
    "command": command_record,
    "n_steps": N_STEPS,
    "observation_provenance": (
        "All entries in simulation_internal_observations were read from the "
        "Isaac Sim physics engine via ArticulationView during the simulation "
        "loop. They become the external record only by being written to this "
        "file. No ABR mathematics were applied to these values."
    ),
    "simulation_internal_observations": simulation_internal_observations,
    "summary": {
        "initial_position_rad": obs_initial["joint_position_rad"],
        "final_position_rad": final_pos_rad,
        "target_position_rad": float(TARGET_POSITION_RAD),
        "error_from_target_rad": float(error_from_target_rad),
        "error_from_target_deg": float(np.degrees(error_from_target_rad)),
    },
    "phase_i_execution_evidence": {
        "1_isaac_sim_started": "see isaac_sim_version field — populated only if SimulationApp launched",
        "2_scene_loaded": "see num_dof field — populated only if ArticulationView initialised",
        "3_joint_received_command": "command field records what was sent to set_joint_position_targets()",
        "4_joint_state_observed": "simulation_internal_observations contains all step records",
        "5_external_record_written": "this file is the external record",
    },
    "phase_i_outcome": "OPEN — awaiting Origin and Verifier review of this file",
    "notes": (
        "No ABR mathematics are present in this script. "
        "This script establishes simulation execution only. "
        "No convergence tolerance is declared here; assessment of whether "
        "the final position is acceptable is left to Origin and Verifier. "
        "ABR kernel calls are authorised in Phase II only."
    ),
}

out_path = Path(__file__).parent / "phase1_observations.json"
out_path.write_text(json.dumps(evidence, indent=2))
print(f"[Phase I] Evidence written to: {out_path}")

# ---------------------------------------------------------------------------
# 9. Shut down
# ---------------------------------------------------------------------------

print("[Phase I] Shutting down Isaac Sim...")
simulation_app.close()
print("[Phase I] Done. Return phase1_observations.json to Origin and Verifier.")
