#!/usr/bin/env python3
"""
Garuda Base Lane - Shared Lane Functionality
=============================================
Base class for all worker lanes in the Garuda system.

Version: 0.1.0
Author: Tejas Agnihotri (COO)
"""

import os
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("GARUDA_LANES")


class LaneStatus(Enum):
    IDLE = "idle"
    PROCESSING = "processing"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class LaneTask:
    """A task assigned to a lane"""
    id: str
    title: str
    description: str
    lane: str
    priority: str
    assigned_agent: str
    status: str = "pending"
    created_at: datetime = None
    updated_at: datetime = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()


class BaseLane(ABC):
    """
    Abstract base class for all worker lanes.

    Each lane handles specific types of tasks:
    - Development: Code, APIs, deployments
    - Marketing: Campaigns, content, social media
    - Research: Analysis, documentation
    - Operations: Support, automation, monitoring
    """

    def __init__(self, lane_name: str, core=None, state_manager=None):
        self.lane_name = lane_name
        self.core = core
        self.state_manager = state_manager
        self.status = LaneStatus.IDLE
        self.agents: List[Dict] = []
        self.current_tasks: Dict[str, LaneTask] = {}
        self.completed_tasks: List[str] = []
        self.config = {}

        self._load_config()
        self._load_agents()

        logger.info(f"{self.lane_name.capitalize()} Lane initialized")

    def _load_config(self):
        """Load lane-specific configuration"""
        if self.core and self.core.config:
            lanes_config = self.core.config.get("lanes", {})
            self.config = lanes_config.get(self.lane_name, {})

    def _load_agents(self):
        """Load agents assigned to this lane"""
        if self.core:
            self.agents = [
                {"id": a.id, "name": a.full_name, "role": a.role, "email": a.email}
                for a in self.core.get_agents_by_lane(self.lane_name)
            ]

    def get_head(self) -> Optional[Dict]:
        """Get the lane head (manager)"""
        for agent in self.agents:
            if "Head" in agent.get("role", "") or "Manager" in agent.get("role", ""):
                return agent
        return self.agents[0] if self.agents else None

    def assign_task(self, task: LaneTask) -> bool:
        """Assign a task to this lane"""
        if task.assigned_agent:
            # Verify agent is in this lane
            agent_ids = [a["id"] for a in self.agents]
            if task.assigned_agent not in agent_ids:
                logger.warning(f"Agent {task.assigned_agent} not in {self.lane_name} lane")
                # Assign to lane head instead
                head = self.get_head()
                if head:
                    task.assigned_agent = head["id"]
        else:
            # Auto-assign to lane head
            head = self.get_head()
            if head:
                task.assigned_agent = head["id"]

        task.lane = self.lane_name
        task.updated_at = datetime.now()
        self.current_tasks[task.id] = task

        logger.info(f"Task {task.id} assigned to {task.assigned_agent} in {self.lane_name} lane")
        return True

    def complete_task(self, task_id: str, result: Dict = None) -> bool:
        """Mark a task as completed"""
        if task_id in self.current_tasks:
            task = self.current_tasks.pop(task_id)
            task.status = "completed"
            task.updated_at = datetime.now()
            if result:
                task.metadata["result"] = result
            self.completed_tasks.append(task_id)

            # Save to state if available
            if self.state_manager:
                self.state_manager.save_bead(task.__dict__)

            logger.info(f"Task {task_id} completed in {self.lane_name} lane")
            return True
        return False

    def get_status(self) -> Dict:
        """Get lane status summary"""
        return {
            "lane": self.lane_name,
            "status": self.status.value,
            "agents_count": len(self.agents),
            "agents": self.agents,
            "current_tasks": len(self.current_tasks),
            "completed_tasks": len(self.completed_tasks),
            "head": self.get_head()
        }

    @abstractmethod
    def process_task(self, task: LaneTask) -> Dict:
        """Process a task - must be implemented by each lane"""
        pass

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return list of lane capabilities"""
        pass

    def preflight_check(self) -> Dict:
        """Run lane-specific pre-flight checks"""
        checks = {
            "agents_loaded": len(self.agents) > 0,
            "head_present": self.get_head() is not None,
            "config_loaded": bool(self.config)
        }

        all_passed = all(checks.values())

        return {
            "lane": self.lane_name,
            "all_passed": all_passed,
            "checks": checks,
            "timestamp": datetime.now().isoformat()
        }
