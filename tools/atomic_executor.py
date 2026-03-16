"""
Garuda Atomic Execution System

Implements atomic task execution to prevent double-work.
Based on Paperclip Mission Control pattern.

Features:
- Lock-based execution (only one agent per task)
- Budget tracking per agent and project
- Execution history and audit trail
- Automatic timeout and lock release
"""

import os
import json
import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib

logger = logging.getLogger("GARUDA_ATOMIC")

class ExecutionStatus(Enum):
    PENDING = "pending"
    LOCKED = "locked"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class ExecutionLock:
    """Represents a lock on a task"""
    task_id: str
    agent_id: str
    locked_at: datetime
    expires_at: datetime
    status: ExecutionStatus = ExecutionStatus.LOCKED

    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "locked_at": self.locked_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "status": self.status.value
        }


@dataclass
class BudgetConfig:
    """Budget configuration for an agent or project"""
    entity_id: str
    entity_type: str  # "agent" or "project"
    max_tokens_per_day: int = 100000
    max_tokens_per_task: int = 10000
    max_tasks_per_day: int = 50
    max_cost_per_day: float = 10.0  # USD

    # Current usage
    tokens_used_today: int = 0
    tasks_completed_today: int = 0
    cost_spent_today: float = 0.0
    last_reset: datetime = field(default_factory=datetime.now)


@dataclass
class ExecutionRecord:
    """Record of an atomic execution"""
    execution_id: str
    task_id: str
    agent_id: str
    status: ExecutionStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    tokens_used: int = 0
    cost: float = 0.0
    result: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "execution_id": self.execution_id,
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "tokens_used": self.tokens_used,
            "cost": self.cost,
            "result": self.result,
            "error": self.error
        }


class AtomicExecutor:
    """
    Manages atomic execution of tasks.

    Ensures:
    - Only one agent can work on a task at a time
    - Budgets are enforced
    - Execution history is maintained
    - Timeouts are handled
    """

    DEFAULT_LOCK_TIMEOUT = 3600  # 1 hour
    LOCKS_FILE = "/a0/usr/workdir/garuda-system/beads/.locks.json"
    HISTORY_FILE = "/a0/usr/workdir/garuda-system/beads/.execution_history.json"
    BUDGETS_FILE = "/a0/usr/workdir/garuda-system/config/budgets.json"

    def __init__(self):
        self.locks: Dict[str, ExecutionLock] = {}
        self.budgets: Dict[str, BudgetConfig] = {}
        self.history: List[ExecutionRecord] = []
        self._lock = threading.RLock()

        # Load state from files
        self._load_locks()
        self._load_budgets()
        self._load_history()

        # Clean expired locks
        self._clean_expired_locks()

        logger.info("Atomic Executor initialized")

    def _load_locks(self):
        """Load locks from file"""
        if os.path.exists(self.LOCKS_FILE):
            try:
                with open(self.LOCKS_FILE, 'r') as f:
                    data = json.load(f)
                    for task_id, lock_data in data.items():
                        self.locks[task_id] = ExecutionLock(
                            task_id=lock_data["task_id"],
                            agent_id=lock_data["agent_id"],
                            locked_at=datetime.fromisoformat(lock_data["locked_at"]),
                            expires_at=datetime.fromisoformat(lock_data["expires_at"]),
                            status=ExecutionStatus(lock_data["status"])
                        )
                logger.info(f"Loaded {len(self.locks)} locks")
            except Exception as e:
                logger.error(f"Error loading locks: {e}")

    def _save_locks(self):
        """Save locks to file"""
        os.makedirs(os.path.dirname(self.LOCKS_FILE), exist_ok=True)
        with open(self.LOCKS_FILE, 'w') as f:
            json.dump({tid: lock.to_dict() for tid, lock in self.locks.items()}, f, indent=2)

    def _load_budgets(self):
        """Load budgets from file"""
        if os.path.exists(self.BUDGETS_FILE):
            try:
                with open(self.BUDGETS_FILE, 'r') as f:
                    data = json.load(f)
                    for entity_id, budget_data in data.items():
                        self.budgets[entity_id] = BudgetConfig(
                            entity_id=budget_data["entity_id"],
                            entity_type=budget_data["entity_type"],
                            max_tokens_per_day=budget_data.get("max_tokens_per_day", 100000),
                            max_tokens_per_task=budget_data.get("max_tokens_per_task", 10000),
                            max_tasks_per_day=budget_data.get("max_tasks_per_day", 50),
                            max_cost_per_day=budget_data.get("max_cost_per_day", 10.0),
                            tokens_used_today=budget_data.get("tokens_used_today", 0),
                            tasks_completed_today=budget_data.get("tasks_completed_today", 0),
                            cost_spent_today=budget_data.get("cost_spent_today", 0.0),
                            last_reset=datetime.fromisoformat(budget_data["last_reset"]) if budget_data.get("last_reset") else datetime.now()
                        )
                logger.info(f"Loaded {len(self.budgets)} budgets")
            except Exception as e:
                logger.error(f"Error loading budgets: {e}")

    def _save_budgets(self):
        """Save budgets to file"""
        os.makedirs(os.path.dirname(self.BUDGETS_FILE), exist_ok=True)
        with open(self.BUDGETS_FILE, 'w') as f:
            json.dump({eid: asdict(b) for eid, b in self.budgets.items()}, f, indent=2, default=str)

    def _load_history(self):
        """Load execution history"""
        if os.path.exists(self.HISTORY_FILE):
            try:
                with open(self.HISTORY_FILE, 'r') as f:
                    data = json.load(f)
                    for record in data:
                        self.history.append(ExecutionRecord(
                            execution_id=record["execution_id"],
                            task_id=record["task_id"],
                            agent_id=record["agent_id"],
                            status=ExecutionStatus(record["status"]),
                            started_at=datetime.fromisoformat(record["started_at"]),
                            completed_at=datetime.fromisoformat(record["completed_at"]) if record.get("completed_at") else None,
                            tokens_used=record.get("tokens_used", 0),
                            cost=record.get("cost", 0.0),
                            result=record.get("result"),
                            error=record.get("error")
                        ))
                logger.info(f"Loaded {len(self.history)} history records")
            except Exception as e:
                logger.error(f"Error loading history: {e}")

    def _save_history(self):
        """Save execution history"""
        os.makedirs(os.path.dirname(self.HISTORY_FILE), exist_ok=True)
        with open(self.HISTORY_FILE, 'w') as f:
            json.dump([r.to_dict() for r in self.history[-1000:]], f, indent=2)  # Keep last 1000

    def _clean_expired_locks(self):
        """Remove expired locks"""
        expired = [tid for tid, lock in self.locks.items() if lock.is_expired()]
        for tid in expired:
            del self.locks[tid]
            logger.info(f"Removed expired lock for task {tid}")
        if expired:
            self._save_locks()

    def _reset_daily_budgets(self):
        """Reset daily budget counters"""
        now = datetime.now()
        for budget in self.budgets.values():
            if (now - budget.last_reset).days >= 1:
                budget.tokens_used_today = 0
                budget.tasks_completed_today = 0
                budget.cost_spent_today = 0.0
                budget.last_reset = now
        self._save_budgets()

    def acquire_lock(self, task_id: str, agent_id: str, 
                     timeout_seconds: int = None) -> bool:
        """
        Try to acquire a lock on a task.

        Returns True if lock acquired, False if already locked.
        """
        with self._lock:
            timeout = timeout_seconds or self.DEFAULT_LOCK_TIMEOUT

            # Check if already locked
            if task_id in self.locks:
                lock = self.locks[task_id]
                if not lock.is_expired():
                    logger.warning(f"Task {task_id} already locked by {lock.agent_id}")
                    return False
                else:
                    # Remove expired lock
                    del self.locks[task_id]

            # Create new lock
            now = datetime.now()
            lock = ExecutionLock(
                task_id=task_id,
                agent_id=agent_id,
                locked_at=now,
                expires_at=now + timedelta(seconds=timeout),
                status=ExecutionStatus.LOCKED
            )

            self.locks[task_id] = lock
            self._save_locks()

            logger.info(f"Lock acquired: task={task_id}, agent={agent_id}")
            return True

    def release_lock(self, task_id: str, agent_id: str) -> bool:
        """Release a lock on a task"""
        with self._lock:
            if task_id not in self.locks:
                return True

            lock = self.locks[task_id]
            if lock.agent_id != agent_id:
                logger.warning(f"Cannot release lock: owned by {lock.agent_id}, not {agent_id}")
                return False

            del self.locks[task_id]
            self._save_locks()
            logger.info(f"Lock released: task={task_id}")
            return True

    def check_budget(self, agent_id: str, project_id: str = None,
                     estimated_tokens: int = 0) -> Dict[str, Any]:
        """
        Check if an agent has budget available.

        Returns dict with 'allowed' and 'reason' keys.
        """
        self._reset_daily_budgets()

        agent_budget = self.budgets.get(agent_id)
        project_budget = self.budgets.get(project_id) if project_id else None

        result = {"allowed": True, "reason": "", "agent_budget": None, "project_budget": None}

        # Check agent budget
        if agent_budget:
            result["agent_budget"] = {
                "tokens_remaining": agent_budget.max_tokens_per_day - agent_budget.tokens_used_today,
                "tasks_remaining": agent_budget.max_tasks_per_day - agent_budget.tasks_completed_today,
                "cost_remaining": agent_budget.max_cost_per_day - agent_budget.cost_spent_today
            }

            if agent_budget.tokens_used_today + estimated_tokens > agent_budget.max_tokens_per_day:
                result["allowed"] = False
                result["reason"] = f"Agent {agent_id} token budget exceeded"
            elif agent_budget.tasks_completed_today >= agent_budget.max_tasks_per_day:
                result["allowed"] = False
                result["reason"] = f"Agent {agent_id} task limit exceeded"

        # Check project budget
        if project_budget and result["allowed"]:
            result["project_budget"] = {
                "tokens_remaining": project_budget.max_tokens_per_day - project_budget.tokens_used_today,
                "cost_remaining": project_budget.max_cost_per_day - project_budget.cost_spent_today
            }

            if project_budget.tokens_used_today + estimated_tokens > project_budget.max_tokens_per_day:
                result["allowed"] = False
                result["reason"] = f"Project {project_id} token budget exceeded"

        return result

    def record_usage(self, agent_id: str, tokens_used: int, 
                     cost: float = 0.0, project_id: str = None):
        """Record token usage for budget tracking"""
        with self._lock:
            # Update agent budget
            if agent_id in self.budgets:
                self.budgets[agent_id].tokens_used_today += tokens_used
                self.budgets[agent_id].cost_spent_today += cost

            # Update project budget
            if project_id and project_id in self.budgets:
                self.budgets[project_id].tokens_used_today += tokens_used
                self.budgets[project_id].cost_spent_today += cost

            self._save_budgets()

    def start_execution(self, task_id: str, agent_id: str) -> str:
        """
        Start an atomic execution.

        Returns execution_id if successful, empty string if failed.
        """
        with self._lock:
            # Try to acquire lock
            if not self.acquire_lock(task_id, agent_id):
                return ""

            # Create execution record
            execution_id = hashlib.md5(f"{task_id}:{agent_id}:{time.time()}".encode()).hexdigest()[:12]

            record = ExecutionRecord(
                execution_id=execution_id,
                task_id=task_id,
                agent_id=agent_id,
                status=ExecutionStatus.RUNNING,
                started_at=datetime.now()
            )

            self.history.append(record)
            self._save_history()

            # Update lock status
            if task_id in self.locks:
                self.locks[task_id].status = ExecutionStatus.RUNNING
                self._save_locks()

            logger.info(f"Execution started: {execution_id}")
            return execution_id

    def complete_execution(self, execution_id: str, result: str = None,
                          tokens_used: int = 0, cost: float = 0.0,
                          error: str = None) -> bool:
        """Complete an execution"""
        with self._lock:
            # Find execution record
            record = None
            for r in self.history:
                if r.execution_id == execution_id:
                    record = r
                    break

            if not record:
                logger.error(f"Execution not found: {execution_id}")
                return False

            # Update record
            record.completed_at = datetime.now()
            record.tokens_used = tokens_used
            record.cost = cost
            record.result = result[:500] if result else None  # Truncate long results
            record.error = error
            record.status = ExecutionStatus.FAILED if error else ExecutionStatus.COMPLETED

            # Release lock
            self.release_lock(record.task_id, record.agent_id)

            # Record usage
            self.record_usage(record.agent_id, tokens_used, cost)

            # Update task count
            if record.agent_id in self.budgets and not error:
                self.budgets[record.agent_id].tasks_completed_today += 1
                self._save_budgets()

            self._save_history()
            logger.info(f"Execution completed: {execution_id}, status={record.status.value}")
            return True

    def get_status(self) -> Dict[str, Any]:
        """Get atomic executor status"""
        return {
            "active_locks": len(self.locks),
            "total_executions": len(self.history),
            "budgets_tracked": len(self.budgets),
            "locks": {tid: lock.to_dict() for tid, lock in self.locks.items()}
        }

    def set_budget(self, entity_id: str, entity_type: str,
                   max_tokens_per_day: int = 100000,
                   max_tokens_per_task: int = 10000,
                   max_tasks_per_day: int = 50,
                   max_cost_per_day: float = 10.0):
        """Set budget for an agent or project"""
        budget = BudgetConfig(
            entity_id=entity_id,
            entity_type=entity_type,
            max_tokens_per_day=max_tokens_per_day,
            max_tokens_per_task=max_tokens_per_task,
            max_tasks_per_day=max_tasks_per_day,
            max_cost_per_day=max_cost_per_day
        )
        self.budgets[entity_id] = budget
        self._save_budgets()
        logger.info(f"Budget set for {entity_type} {entity_id}")


def get_atomic_executor() -> AtomicExecutor:
    """Get singleton atomic executor"""
    global _atomic_executor
    if '_atomic_executor' not in globals():
        _atomic_executor = AtomicExecutor()
    return _atomic_executor
