#!/usr/bin/env python3
"""
Garuda State Manager - Git-Backed Persistence
==============================================
Implements the "Hook" concept from Gas Town methodology.
All state is persisted to Git, ensuring:
- No data loss on restart
- Full rollback capability
- Audit trail of all changes

Version: 0.1.0
Author: Tejas Agnihotri (COO)
"""

import os
import json
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import asdict
import shutil

logger = logging.getLogger("GARUDA_STATE")


class StateManager:
    """
    Manages persistent state using Git as the backing store.

    This implements the "Hook" concept from Gas Town:
    - All beads (work items) are stored in git
    - All rigs (projects) are stored in git
    - All agent states are stored in git
    - Full history and rollback capability
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, base_path: str = None):
        """
        Initialize the State Manager.

        Args:
            base_path: Base directory for garuda-system repository
        """
        if hasattr(self, "_initialized") and self._initialized:
            return

        if base_path:
            self.base_path = Path(base_path)
        else:
            self.base_path = Path(__file__).parent.parent

        self.beads_path = self.base_path / "beads"
        self.projects_path = self.base_path / "projects"
        self.state_path = self.base_path / ".garuda_state"

        # Ensure directories exist
        self.beads_path.mkdir(parents=True, exist_ok=True)
        self.projects_path.mkdir(parents=True, exist_ok=True)
        self.state_path.mkdir(parents=True, exist_ok=True)

        self._initialized = True
        logger.info(f"State Manager initialized at {self.base_path}")

    def _run_git_command(self, *args, cwd=None) -> tuple:
        """Run a git command and return (success, output)"""
        try:
            result = subprocess.run(
                ["git"] + list(args),
                cwd=cwd or self.base_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0, result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return False, "Git command timed out"
        except Exception as e:
            return False, str(e)

    def _ensure_git_repo(self):
        """Ensure we're in a git repository"""
        git_dir = self.base_path / ".git"
        if not git_dir.exists():
            logger.warning("Not in a git repository. State persistence will be local only.")
            return False
        return True

    # ==================== BEAD MANAGEMENT ====================

    def save_bead(self, bead_data: Dict[str, Any]) -> str:
        """
        Save a bead (work item) to persistent storage.

        Args:
            bead_data: Bead data dictionary

        Returns:
            Bead ID
        """
        bead_id = bead_data.get("id", f"bead-{datetime.now().strftime("%Y%m%d%H%M%S")}")
        bead_file = self.beads_path / f"{bead_id}.json"

        # Add timestamp
        bead_data["updated_at"] = datetime.now().isoformat()

        with open(bead_file, "w") as f:
            json.dump(bead_data, f, indent=2, default=str)

        logger.info(f"Saved bead: {bead_id}")
        return bead_id

    def load_bead(self, bead_id: str) -> Optional[Dict[str, Any]]:
        """Load a bead by ID"""
        bead_file = self.beads_path / f"{bead_id}.json"
        if bead_file.exists():
            with open(bead_file, "r") as f:
                return json.load(f)
        return None

    def list_beads(self, lane: str = None, stage: str = None) -> List[Dict[str, Any]]:
        """List all beads, optionally filtered by lane or stage"""
        beads = []
        for bead_file in self.beads_path.glob("*.json"):
            with open(bead_file, "r") as f:
                bead = json.load(f)
                if lane and bead.get("lane") != lane:
                    continue
                if stage and bead.get("stage") != stage:
                    continue
                beads.append(bead)
        return beads

    def update_bead_stage(self, bead_id: str, new_stage: str) -> bool:
        """Update the stage of a bead"""
        bead = self.load_bead(bead_id)
        if bead:
            bead["stage"] = new_stage
            bead["updated_at"] = datetime.now().isoformat()
            self.save_bead(bead)
            logger.info(f"Updated bead {bead_id} to stage {new_stage}")
            return True
        return False

    # ==================== RIG (PROJECT) MANAGEMENT ====================

    def save_rig(self, rig_data: Dict[str, Any]) -> str:
        """Save a rig (project) to persistent storage"""
        rig_id = rig_data.get("id", f"rig-{datetime.now().strftime("%Y%m%d%H%M%S")}")
        rig_file = self.projects_path / f"{rig_id}.json"

        rig_data["updated_at"] = datetime.now().isoformat()

        with open(rig_file, "w") as f:
            json.dump(rig_data, f, indent=2, default=str)

        logger.info(f"Saved rig: {rig_id}")
        return rig_id

    def load_rig(self, rig_id: str) -> Optional[Dict[str, Any]]:
        """Load a rig by ID"""
        rig_file = self.projects_path / f"{rig_id}.json"
        if rig_file.exists():
            with open(rig_file, "r") as f:
                return json.load(f)
        return None

    def list_rigs(self, status: str = None) -> List[Dict[str, Any]]:
        """List all rigs, optionally filtered by status"""
        rigs = []
        for rig_file in self.projects_path.glob("*.json"):
            with open(rig_file, "r") as f:
                rig = json.load(f)
                if status and rig.get("status") != status:
                    continue
                rigs.append(rig)
        return rigs

    # ==================== AGENT STATE MANAGEMENT ====================

    def save_agent_state(self, agent_id: str, state: Dict[str, Any]) -> bool:
        """Save an agent's state"""
        state_file = self.state_path / f"agent_{agent_id}.json"
        state["updated_at"] = datetime.now().isoformat()

        with open(state_file, "w") as f:
            json.dump(state, f, indent=2, default=str)

        logger.debug(f"Saved state for agent: {agent_id}")
        return True

    def load_agent_state(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Load an agent's state"""
        state_file = self.state_path / f"agent_{agent_id}.json"
        if state_file.exists():
            with open(state_file, "r") as f:
                return json.load(f)
        return None

    # ==================== GIT OPERATIONS ====================

    def commit_state(self, message: str = "State update") -> bool:
        """
        Commit current state to git.

        This implements the Gas Town pattern of git-backed persistence.
        """
        if not self._ensure_git_repo():
            return False

        # Stage all changes
        success, output = self._run_git_command("add", "beads/", "projects/", ".garuda_state/")
        if not success:
            logger.error(f"Failed to stage changes: {output}")
            return False

        # Commit
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        commit_message = f"{message} [{timestamp}]"
        success, output = self._run_git_command("commit", "-m", commit_message)

        if success:
            logger.info(f"Committed state: {commit_message}")
            return True
        elif "nothing to commit" in output:
            logger.debug("No changes to commit")
            return True
        else:
            logger.error(f"Failed to commit: {output}")
            return False

    def push_state(self) -> bool:
        """Push state to remote repository"""
        if not self._ensure_git_repo():
            return False

        success, output = self._run_git_command("push")
        if success:
            logger.info("Pushed state to remote")
            return True
        else:
            logger.error(f"Failed to push: {output}")
            return False

    def pull_state(self) -> bool:
        """Pull latest state from remote repository"""
        if not self._ensure_git_repo():
            return False

        success, output = self._run_git_command("pull")
        if success:
            logger.info("Pulled latest state from remote")
            return True
        else:
            logger.error(f"Failed to pull: {output}")
            return False

    def get_commit_history(self, limit: int = 10) -> List[Dict[str, str]]:
        """Get recent commit history"""
        if not self._ensure_git_repo():
            return []

        success, output = self._run_git_command(
            "log", f"-{limit}", "--pretty=format:%H|%s|%ai|%an"
        )

        if not success:
            return []

        commits = []
        for line in output.strip().split("
"):
            if "|" in line:
                parts = line.split("|")
                if len(parts) >= 4:
                    commits.append({
                        "hash": parts[0],
                        "message": parts[1],
                        "date": parts[2],
                        "author": parts[3]
                    })
        return commits

    def rollback_to_commit(self, commit_hash: str) -> bool:
        """
        Rollback to a specific commit.

        WARNING: This is a destructive operation.
        """
        if not self._ensure_git_repo():
            return False

        success, output = self._run_git_command("reset", "--hard", commit_hash)
        if success:
            logger.warning(f"Rolled back to commit {commit_hash}")
            return True
        else:
            logger.error(f"Failed to rollback: {output}")
            return False

    # ==================== SYSTEM STATE ====================

    def get_full_state_summary(self) -> Dict[str, Any]:
        """Get a summary of the full system state"""
        return {
            "beads_count": len(list(self.beads_path.glob("*.json"))),
            "rigs_count": len(list(self.projects_path.glob("*.json"))),
            "agents_with_state": len(list(self.state_path.glob("agent_*.json"))),
            "last_commit": self.get_commit_history(1),
            "timestamp": datetime.now().isoformat()
        }


# Singleton instance
_state_instance = None

def get_state_manager() -> StateManager:
    """Get the singleton State Manager instance"""
    global _state_instance
    if _state_instance is None:
        _state_instance = StateManager()
    return _state_instance


if __name__ == "__main__":
    # Test the state manager
    sm = get_state_manager()
    print(json.dumps(sm.get_full_state_summary(), indent=2, default=str))

    # Test creating a bead
    test_bead = {
        "id": "test-bead-001",
        "title": "Test Bead",
        "description": "Testing state persistence",
        "lane": "development",
        "stage": "INBOX"
    }
    sm.save_bead(test_bead)
    print(f"
Saved test bead: {test_bead['id']}")
