"""
Garuda Heartbeat System

Implements scheduled agent wake-up for proactive task monitoring.
Based on Paperclip Mission Control pattern.

Features:
- Configurable heartbeat intervals per lane
- Wake-up checks for pending tasks
- Status reporting to orchestrator
- Budget enforcement
"""

import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger("GARUDA_HEARTBEAT")

class HeartbeatStatus(Enum):
    IDLE = "idle"
    ACTIVE = "active"
    PROCESSING = "processing"
    ERROR = "error"
    SLEEPING = "sleeping"


@dataclass
class HeartbeatConfig:
    """Configuration for a lane's heartbeat"""
    lane_name: str
    interval_seconds: int = 300  # 5 minutes default
    max_retries: int = 3
    timeout_seconds: int = 60
    enabled: bool = True
    callbacks: List[str] = field(default_factory=list)


@dataclass
class HeartbeatResult:
    """Result of a heartbeat execution"""
    lane_name: str
    timestamp: datetime
    status: HeartbeatStatus
    tasks_processed: int = 0
    tasks_pending: int = 0
    message: str = ""
    duration_ms: float = 0
    error: Optional[str] = None


class HeartbeatManager:
    """
    Manages heartbeat schedules for all lanes.

    Each lane can have its own heartbeat interval.
    The manager coordinates wake-ups and reports to TEJAS.
    """

    DEFAULT_INTERVALS = {
        "development": 300,    # 5 minutes
        "marketing": 600,      # 10 minutes
        "research": 900,       # 15 minutes
        "operations": 180,     # 3 minutes (needs quick response)
        "personal": 3600       # 1 hour
    }

    def __init__(self, core=None):
        self.core = core
        self.configs: Dict[str, HeartbeatConfig] = {}
        self.last_heartbeats: Dict[str, HeartbeatResult] = {}
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Initialize default configs
        for lane, interval in self.DEFAULT_INTERVALS.items():
            self.configs[lane] = HeartbeatConfig(
                lane_name=lane,
                interval_seconds=interval
            )

        logger.info("Heartbeat Manager initialized")

    def configure(self, lane_name: str, interval_seconds: int = None, 
                  enabled: bool = True, callbacks: List[str] = None):
        """Configure heartbeat for a specific lane"""
        config = self.configs.get(lane_name, HeartbeatConfig(lane_name=lane_name))

        if interval_seconds:
            config.interval_seconds = interval_seconds
        config.enabled = enabled
        if callbacks:
            config.callbacks = callbacks

        self.configs[lane_name] = config
        logger.info(f"Configured heartbeat for {lane_name}: interval={config.interval_seconds}s")

    def start(self):
        """Start the heartbeat manager"""
        if self.running:
            logger.warning("Heartbeat manager already running")
            return

        self.running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("Heartbeat manager started")

    def stop(self):
        """Stop the heartbeat manager"""
        self.running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Heartbeat manager stopped")

    def _run_loop(self):
        """Main heartbeat loop"""
        while self.running and not self._stop_event.is_set():
            self._check_heartbeats()
            self._stop_event.wait(60)  # Check every minute

    def _check_heartbeats(self):
        """Check if any lane needs a heartbeat"""
        now = datetime.now()

        for lane_name, config in self.configs.items():
            if not config.enabled:
                continue

            last = self.last_heartbeats.get(lane_name)
            if last:
                elapsed = (now - last.timestamp).total_seconds()
                if elapsed < config.interval_seconds:
                    continue

            # Execute heartbeat
            self._execute_heartbeat(lane_name, config)

    def _execute_heartbeat(self, lane_name: str, config: HeartbeatConfig) -> HeartbeatResult:
        """Execute a heartbeat for a lane"""
        start_time = time.time()

        try:
            logger.info(f"Executing heartbeat for {lane_name}")

            # Check for pending tasks in the lane
            pending_count = self._check_pending_tasks(lane_name)

            # Process if there are pending tasks
            processed = 0
            if pending_count > 0:
                processed = self._process_pending_tasks(lane_name)

            duration = (time.time() - start_time) * 1000

            result = HeartbeatResult(
                lane_name=lane_name,
                timestamp=datetime.now(),
                status=HeartbeatStatus.ACTIVE if processed > 0 else HeartbeatStatus.IDLE,
                tasks_processed=processed,
                tasks_pending=pending_count - processed,
                message=f"Heartbeat completed: {processed} tasks processed",
                duration_ms=duration
            )

        except Exception as e:
            result = HeartbeatResult(
                lane_name=lane_name,
                timestamp=datetime.now(),
                status=HeartbeatStatus.ERROR,
                message="Heartbeat failed",
                error=str(e)
            )
            logger.error(f"Heartbeat error for {lane_name}: {e}")

        self.last_heartbeats[lane_name] = result
        return result

    def _check_pending_tasks(self, lane_name: str) -> int:
        """Check for pending tasks in a lane"""
        # Check beads folder for pending tasks
        import os
        beads_path = f"/a0/usr/workdir/garuda-system/beads/{lane_name}"

        if not os.path.exists(beads_path):
            return 0

        pending_files = [f for f in os.listdir(beads_path) if f.endswith('.json')]
        return len(pending_files)

    def _process_pending_tasks(self, lane_name: str) -> int:
        """Process pending tasks in a lane"""
        # This would integrate with actual lane processing
        # For now, return 0 as placeholder
        return 0

    def get_status(self) -> Dict[str, Any]:
        """Get heartbeat status for all lanes"""
        return {
            "running": self.running,
            "lanes": {
                name: {
                    "interval": config.interval_seconds,
                    "enabled": config.enabled,
                    "last_heartbeat": self.last_heartbeats.get(name).timestamp.isoformat() 
                        if name in self.last_heartbeats else None,
                    "status": self.last_heartbeats.get(name).status.value 
                        if name in self.last_heartbeats else "never"
                }
                for name, config in self.configs.items()
            }
        }

    def force_heartbeat(self, lane_name: str) -> HeartbeatResult:
        """Force an immediate heartbeat for a lane"""
        config = self.configs.get(lane_name)
        if not config:
            return HeartbeatResult(
                lane_name=lane_name,
                timestamp=datetime.now(),
                status=HeartbeatStatus.ERROR,
                error=f"Unknown lane: {lane_name}"
            )

        return self._execute_heartbeat(lane_name, config)


def create_heartbeat_manager(core=None) -> HeartbeatManager:
    """Factory function to create a heartbeat manager"""
    return HeartbeatManager(core=core)
