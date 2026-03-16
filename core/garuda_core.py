#!/usr/bin/env python3
"""
Garuda Core - Immutable Orchestration System
============================================
This is the heart of the Garuda Autonomous System.
It is designed to NEVER break - all updates happen through safe mechanisms.

Version: 0.1.0
Author: Tejas Agnihotri (COO)
Organization: Adhiratha Digital Solutions
"""

import os
import sys
import json
import yaml
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("GARUDA_CORE")


class LaneType(Enum):
    """Worker lanes in the Garuda system"""
    ORCHESTRATION = "orchestration"
    DEVELOPMENT = "development"
    MARKETING = "marketing"
    RESEARCH = "research"
    OPERATIONS = "operations"
    PERSONAL = "personal"


class WorkflowStage(Enum):
    """BMAD-style workflow lifecycle stages"""
    PLANNING = "PLANNING"
    INBOX = "INBOX"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    TESTING = "TESTING"
    REVIEW = "REVIEW"
    DONE = "DONE"


class Priority(Enum):
    """Task priority levels"""
    CRITICAL = 0  # P0 - System breaking issues
    HIGH = 1      # P1 - Important tasks
    MEDIUM = 2    # P2 - Normal tasks
    LOW = 3       # P3 - Nice to have


@dataclass
class Agent:
    """Represents an agent in the system"""
    id: str
    full_name: str
    short_name: str
    role: str
    email: str
    lane: str
    lane_role: str
    model: str
    persistent: bool = True
    capabilities: List[str] = field(default_factory=list)
    reports_to: str = ""
    bucket: int = 2  # Default to agency bucket


@dataclass
class Bead:
    """A bead is a structured work item (from Gas Town methodology)"""
    id: str
    title: str
    description: str
    lane: str
    assigned_agent: str
    stage: WorkflowStage
    priority: Priority
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_bead_id: Optional[str] = None
    child_bead_ids: List[str] = field(default_factory=list)


@dataclass
class Rig:
    """A rig is a project container (from Gas Town methodology)"""
    id: str
    name: str
    description: str
    bucket: int
    created_at: datetime
    github_repo: str
    status: str = "active"
    agents_assigned: List[str] = field(default_factory=list)
    beads: List[str] = field(default_factory=list)


class GarudaCore:
    """
    The immutable core of the Garuda Autonomous System.

    This class provides:
    - Agent management
    - Lane coordination
    - Bead (work item) management
    - Rig (project) management
    - Configuration loading

    CRITICAL: This core is IMMUTABLE. Do not modify directly.
    All updates must go through the state_manager module.
    """

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        """Singleton pattern - ensure only one core instance exists"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_path: str = None):
        """
        Initialize the Garuda Core.

        Args:
            config_path: Path to garuda.yaml configuration file
        """
        # Prevent re-initialization (singleton)
        if GarudaCore._initialized:
            return

        self.version = "0.1.0"
        self.started_at = datetime.now()

        # Set up paths
        if config_path:
            self.config_path = Path(config_path)
        else:
            # Default to relative path
            self.config_path = Path(__file__).parent.parent / "config" / "garuda.yaml"

        self.agents_path = self.config_path.parent / "agents.yaml"

        # Load configurations
        self.config = self._load_config()
        self.agents = self._load_agents()

        # Initialize state
        self.active_beads: Dict[str, Bead] = {}
        self.active_rigs: Dict[str, Rig] = {}

        GarudaCore._initialized = True
        logger.info(f"Garuda Core v{self.version} initialized")
        logger.info(f"Loaded {len(self.agents)} agents across {len(self.config.get("lanes", {}))} lanes")

    def _load_config(self) -> Dict:
        """Load garuda.yaml configuration"""
        try:
            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return {}

    def _load_agents(self) -> Dict[str, Agent]:
        """Load agent definitions from agents.yaml"""
        agents = {}
        try:
            with open(self.agents_path, "r") as f:
                data = yaml.safe_load(f)

            for agent_data in data.get("agents", []):
                agent = Agent(
                    id=agent_data.get("id", ""),
                    full_name=agent_data.get("full_name", ""),
                    short_name=agent_data.get("short_name", ""),
                    role=agent_data.get("role", ""),
                    email=agent_data.get("email", ""),
                    lane=agent_data.get("lane", ""),
                    lane_role=agent_data.get("lane_role", ""),
                    model=agent_data.get("model", "GLM-4.7-Flash"),
                    persistent=agent_data.get("persistent", True),
                    capabilities=agent_data.get("capabilities", []),
                    reports_to=agent_data.get("reports_to", ""),
                    bucket=agent_data.get("bucket", 2)
                )
                agents[agent.id] = agent

            logger.info(f"Loaded {len(agents)} agents from {self.agents_path}")
        except Exception as e:
            logger.error(f"Failed to load agents: {e}")

        return agents

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get an agent by ID"""
        return self.agents.get(agent_id)

    def get_agents_by_lane(self, lane: str) -> List[Agent]:
        """Get all agents in a specific lane"""
        return [a for a in self.agents.values() if a.lane == lane]

    def get_lane_head(self, lane: str) -> Optional[Agent]:
        """Get the head of a specific lane"""
        for agent in self.agents.values():
            if agent.lane == lane and agent.lane_role == "head":
                return agent
        return None

    def get_orchestrator(self) -> Optional[Agent]:
        """Get the main orchestrator (TEJAS)"""
        return self.get_agent("tejas")

    def get_model_for_task(self, task_type: str) -> str:
        """Get the recommended model for a task type"""
        routing = self.config.get("models", {}).get("routing", {})
        return routing.get(task_type, "GLM-4.7-Flash")

    def create_bead(self, title: str, description: str, lane: str, 
                    priority: Priority = Priority.MEDIUM,
                    assigned_agent: str = None) -> Bead:
        """Create a new bead (work item)"""
        import uuid

        bead_id = f"bead-{uuid.uuid4().hex[:8]}"
        now = datetime.now()

        bead = Bead(
            id=bead_id,
            title=title,
            description=description,
            lane=lane,
            assigned_agent=assigned_agent or "",
            stage=WorkflowStage.INBOX,
            priority=priority,
            created_at=now,
            updated_at=now
        )

        self.active_beads[bead_id] = bead
        logger.info(f"Created bead {bead_id}: {title}")
        return bead

    def create_rig(self, name: str, description: str, bucket: int = 2) -> Rig:
        """Create a new rig (project container)"""
        import uuid

        rig_id = f"rig-{uuid.uuid4().hex[:8]}"
        github_repo = f"github.com/garudaccs/{name.lower().replace(" ", "-")}"

        rig = Rig(
            id=rig_id,
            name=name,
            description=description,
            bucket=bucket,
            created_at=datetime.now(),
            github_repo=github_repo
        )

        self.active_rigs[rig_id] = rig
        logger.info(f"Created rig {rig_id}: {name}")
        return rig

    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            "version": self.version,
            "started_at": self.started_at.isoformat(),
            "uptime_seconds": (datetime.now() - self.started_at).total_seconds(),
            "agents_count": len(self.agents),
            "lanes_count": len(self.config.get("lanes", {})),
            "active_beads": len(self.active_beads),
            "active_rigs": len(self.active_rigs),
            "config_path": str(self.config_path)
        }

    def is_healthy(self) -> bool:
        """Check if the core system is healthy"""
        checks = [
            self.config is not None,
            len(self.agents) > 0,
            self.get_orchestrator() is not None
        ]
        return all(checks)


# Singleton instance for easy import
_core_instance = None

def get_core() -> GarudaCore:
    """Get the singleton Garuda Core instance"""
    global _core_instance
    if _core_instance is None:
        _core_instance = GarudaCore()
    return _core_instance


if __name__ == "__main__":
    # Test the core
    core = get_core()
    print(json.dumps(core.get_system_status(), indent=2, default=str))
    print(f"\nSystem healthy: {core.is_healthy()}")

    # Test getting agents
    tejas = core.get_orchestrator()
    print(f"\nOrchestrator: {tejas.full_name} ({tejas.role})")

    # Test creating a bead
    bead = core.create_bead(
        title="Test Task",
        description="This is a test bead",
        lane="development",
        priority=Priority.HIGH
    )
    print(f"Created bead: {bead.id} - {bead.title}")
