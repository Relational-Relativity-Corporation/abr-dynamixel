"""
phase1_single_joint.py — Phase I: establish Isaac Sim execution environment.

Scope (Section 5 of the integration proposal):
  1. Isaac Sim starts successfully.
  2. A basic articulated robot scene loads.
  3. A simulated joint can receive a command.
  4. The joint's resulting state can be observed.
  5. Observations and commands can be exchanged with the external process.

This script is the external process. It drives Isaac Sim headlessly,
issues one position command to a single revolute joint, reads back the
resulting joint state, and writes the evidence to phase1_observations.json.

NO ABR mathematics are present here. This script only establishes that
the simulation environment works and produces accessible joint observations.
ABR kernel calls are authorised in Phase II only.

Authority: Section 5 / Section 13 of the integration proposal.
Status: OPEN — not yet executed. See environment_requirements.md.
"""

import json
import time
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# 1. Launch Isaac Sim in headless mode
# ---------------------------------------------------------------------------
# SimulationApp must be imported and constructed before any other omni import.

from isaacsim import SimulationApp

CONFIG = {
    "headless": True,
    "hide_ui": True,
    "renderer": "RayTracedLighting",
}

print("[Phase I] Launching Isaac Sim (headless)...")
simulation_app = SimulationApp(CONFIG)

# Record Isaac Sim version immediately after launch.
import carb
kit_version = carb.settings.get_settings().get("/app/version")
print(f"[Phase I] Isaac Sim version: {kit_version}")

# ---------------------------------------------------------------------------
# 2. Import Isaac Sim modules (only after SimulationApp is constructed)
# ---------------------------------------------------------------------------

import numpy as np
import omni.isaac.core
from omni.isaac.core import World
from omni.isaac.core.utils.stage import add_reference_to_stage
from omni.isaac.core.articulations import ArticulationView
import omni.kit.commands

# ---------------------------------------------------------------------------
# 3. Build the scene — one revolute joint
# ---------------------------------------------------------------------------
# We create a minimal USD stage programmatically:
#   - A fixed base cube (static)
#   - A moving arm cube
#   - A single revolute joint connecting them
#
# We do NOT load a URDF or external asset; this removes external file
# dependencies and keeps Phase I self-contained and reproducible.

print("[Phase I] Creating world...")
world = World(stage_units_in_meters=1.0)

from pxr import UsdGeom, UsdPhysics, Gf, Sdf

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

# --- Revolute joint ---
joint_path = f"{root_path}/RevoluteJoint"
joint = UsdPhysics.RevoluteJoint.Define(stage, joint_path)
joint.CreateBody0Rel().SetTargets([Sdf.Path(base_path)])
joint.CreateBody1Rel().SetTargets([Sdf.Path(arm_path)])
joint.CreateAxisAttr("Z")
joint.CreateLowerLimitAttr(-180.0)         # degrees
joint.CreateUpperLimitAttr(180.0)

# Drive API — position control
drive = UsdPhysics.DriveAPI.Apply(stage.GetPrimAtPath(joint_path), "angular")
drive.CreateTypeAttr("force")
drive.CreateTargetPositionAttr(0.0)        # start at 0 degrees
drive.CreateStiffnessAttr(1000.0)
drive.CreateDampingAttr(100.0)
drive.CreateMaxForceAttr(1000.0)

# --- Articulation root on the base ---
art_root_api = UsdPhysics.ArticulationRootAPI.Apply(
    stage.GetPrimAtPath(base_path)
)

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

print(f"[Phase I] Articulation DOF count: {art_view.num_dof}")

# ---------------------------------------------------------------------------
# 5. Record initial joint state (observation before command)
# ---------------------------------------------------------------------------

world.step(render=False)

pos_before = art_view.get_joint_positions()      # shape: (1, num_dof)
vel_before = art_view.get_joint_velocities()

obs_before = {
    "label": "initial_state",
    "step": 0,
    "joint_position_rad": float(pos_before[0, 0]),
    "joint_velocity_rad_s": float(vel_before[0, 0]),
    "command_sent": None,
}
print(f"[Phase I] Initial state: {obs_before}")

# ---------------------------------------------------------------------------
# 6. Issue a position command (45 degrees = π/4 rad)
# ---------------------------------------------------------------------------

TARGET_POSITION_RAD = np.pi / 4.0            # 45 degrees
TARGET_POSITION_DEG = np.degrees(TARGET_POSITION_RAD)

print(f"[Phase I] Sending position command: {TARGET_POSITION_DEG:.1f} deg "
      f"({TARGET_POSITION_RAD:.4f} rad)")

art_view.set_joint_position_targets(
    np.array([[TARGET_POSITION_RAD]], dtype=np.float32)
)

command_record = {
    "type": "position_target",
    "value_rad": TARGET_POSITION_RAD,
    "value_deg": TARGET_POSITION_DEG,
}

# ---------------------------------------------------------------------------
# 7. Step simulation and collect observations
# ---------------------------------------------------------------------------

N_STEPS = 60    # ~1 s at 60 Hz default physics rate
observations = [obs_before]

for step in range(1, N_STEPS + 1):
    world.step(render=False)

    pos = art_view.get_joint_positions()
    vel = art_view.get_joint_velocities()

    obs = {
        "label": "stepping",
        "step": step,
        "joint_position_rad": float(pos[0, 0]),
        "joint_velocity_rad_s": float(vel[0, 0]),
        "command_sent": command_record if step == 1 else None,
    }
    observations.append(obs)

final_pos = observations[-1]["joint_position_rad"]
final_pos_deg = np.degrees(final_pos)
print(f"[Phase I] Final joint position after {N_STEPS} steps: "
      f"{final_pos_deg:.3f} deg ({final_pos:.4f} rad)")

# ---------------------------------------------------------------------------
# 8. Write evidence file
# ---------------------------------------------------------------------------

evidence = {
    "phase": "I",
    "task": "1 — Establish Isaac Sim execution environment",
    "proposal_section": "5",
    "isaac_sim_version": kit_version,
    "python_version": sys.version,
    "scene_description": {
        "base": base_path,
        "arm": arm_path,
        "joint": joint_path,
        "joint_type": "revolute",
        "joint_axis": "Z",
        "control_mode": "position_target",
    },
    "command": command_record,
    "n_steps": N_STEPS,
    "observations": observations,
    "phase_i_success_conditions": {
        "1_isaac_sim_started": True,
        "2_scene_loaded": True,
        "3_joint_received_command": True,
        "4_joint_state_observed": True,
        "5_observations_recorded": True,
    },
    "status": "VERIFIED BY SIMULATION OBSERVATION"
             if abs(final_pos - TARGET_POSITION_RAD) < 0.1
             else "OPEN — joint did not reach target within tolerance",
    "notes": (
        "No ABR mathematics present in this script. "
        "This script establishes simulation execution only. "
        "ABR kernel calls are authorised in Phase II."
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
print("[Phase I] Done.")
