"""
Garuda Governance System

Implements approval gates and safe rollback capabilities.
Based on Paperclip Mission Control pattern.

Features:
- Approval gates for critical actions
- Multi-level approval workflows
- Safe rollback mechanism
- Audit trail for all governance decisions
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib

logger = logging.getLogger("GARUDA_GOVERNANCE")

class GateType(Enum):
    DEPLOYMENT = "deployment"
    BUDGET_OVERRIDE = "budget_override"
    CREDENTIAL_CHANGE = "credential_change"
    SYSTEM_UPDATE = "system_update"
    PROJECT_CREATION = "project_creation"
    LANE_MODIFICATION = "lane_modification"
    AGENT_PROMOTION = "agent_promotion"
    DATA_EXPORT = "data_export"
    EXTERNAL_API = "external_api"
    ROLLBACK = "rollback"


class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


@dataclass
class ApprovalRequest:
    """Request for approval of a critical action"""
    request_id: str
    gate_type: GateType
    requester: str  # Agent ID
    action_description: str
    action_data: dict
    required_approvers: List[str]  # Agent IDs or roles
    current_approvals: List[str] = field(default_factory=list)
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    decided_at: Optional[datetime] = None
    decided_by: Optional[str] = None
    rejection_reason: Optional[str] = None

    def is_approved(self) -> bool:
        return self.status == ApprovalStatus.APPROVED

    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at

    def can_approve(self, approver_id: str) -> bool:
        return approver_id in self.required_approvers and approver_id not in self.current_approvals

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "gate_type": self.gate_type.value,
            "requester": self.requester,
            "action_description": self.action_description,
            "action_data": self.action_data,
            "required_approvers": self.required_approvers,
            "current_approvals": self.current_approvals,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "decided_at": self.decided_at.isoformat() if self.decided_at else None,
            "decided_by": self.decided_by,
            "rejection_reason": self.rejection_reason
        }


@dataclass
class RollbackPoint:
    """A point in time that can be rolled back to"""
    rollback_id: str
    name: str
    description: str
    created_at: datetime
    git_commit: str
    state_snapshot: dict
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "rollback_id": self.rollback_id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "git_commit": self.git_commit,
            "state_snapshot": self.state_snapshot,
            "tags": self.tags
        }


# Default gate configurations
GATE_CONFIGS = {
    GateType.DEPLOYMENT: {
        "required_approvers": ["tejas", "prakash"],
        "auto_approve_after_hours": 24,
        "description": "Production deployment requires approval"
    },
    GateType.BUDGET_OVERRIDE: {
        "required_approvers": ["tejas", "lakshmi"],
        "auto_approve_after_hours": None,  # Never auto-approve
        "description": "Budget override requires approval"
    },
    GateType.CREDENTIAL_CHANGE: {
        "required_approvers": ["prakash"],
        "auto_approve_after_hours": None,
        "description": "Credential changes require Prakash approval"
    },
    GateType.SYSTEM_UPDATE: {
        "required_approvers": ["tejas"],
        "auto_approve_after_hours": 4,
        "description": "System updates require TEJAS approval"
    },
    GateType.PROJECT_CREATION: {
        "required_approvers": ["tejas"],
        "auto_approve_after_hours": 2,
        "description": "New project creation requires approval"
    },
    GateType.LANE_MODIFICATION: {
        "required_approvers": ["tejas", "prakash"],
        "auto_approve_after_hours": None,
        "description": "Lane modifications require approval"
    },
    GateType.AGENT_PROMOTION: {
        "required_approvers": ["tejas", "prakash"],
        "auto_approve_after_hours": None,
        "description": "Agent promotion requires approval"
    },
    GateType.DATA_EXPORT: {
        "required_approvers": ["tejas"],
        "auto_approve_after_hours": 1,
        "description": "Data export requires approval"
    },
    GateType.EXTERNAL_API: {
        "required_approvers": ["tejas"],
        "auto_approve_after_hours": 2,
        "description": "External API integration requires approval"
    },
    GateType.ROLLBACK: {
        "required_approvers": ["tejas"],
        "auto_approve_after_hours": 0,  # Immediate auto-approve for rollbacks
        "description": "Rollback approval"
    }
}


class GovernanceManager:
    """
    Manages governance gates and rollback capabilities.

    Features:
    - Request approvals for critical actions
    - Multi-level approval workflows
    - Auto-approval with time limits
    - Rollback to safe points
    """

    REQUESTS_FILE = "/a0/usr/workdir/garuda-system/beads/.approval_requests.json"
    ROLLBACKS_FILE = "/a0/usr/workdir/garuda-system/beads/.rollback_points.json"
    AUDIT_FILE = "/a0/usr/workdir/garuda-system/beads/.governance_audit.json"

    def __init__(self):
        self.requests: Dict[str, ApprovalRequest] = {}
        self.rollback_points: Dict[str, RollbackPoint] = {}
        self.audit_log: List[dict] = []
        self.gate_configs = GATE_CONFIGS.copy()

        # Load state
        self._load_requests()
        self._load_rollback_points()
        self._load_audit_log()

        # Clean expired requests
        self._clean_expired_requests()

        logger.info("Governance Manager initialized")

    def _load_requests(self):
        """Load approval requests from file"""
        if os.path.exists(self.REQUESTS_FILE):
            try:
                with open(self.REQUESTS_FILE, 'r') as f:
                    data = json.load(f)
                    for req_id, req_data in data.items():
                        self.requests[req_id] = ApprovalRequest(
                            request_id=req_data["request_id"],
                            gate_type=GateType(req_data["gate_type"]),
                            requester=req_data["requester"],
                            action_description=req_data["action_description"],
                            action_data=req_data["action_data"],
                            required_approvers=req_data["required_approvers"],
                            current_approvals=req_data.get("current_approvals", []),
                            status=ApprovalStatus(req_data["status"]),
                            created_at=datetime.fromisoformat(req_data["created_at"]),
                            expires_at=datetime.fromisoformat(req_data["expires_at"]) if req_data.get("expires_at") else None,
                            decided_at=datetime.fromisoformat(req_data["decided_at"]) if req_data.get("decided_at") else None,
                            decided_by=req_data.get("decided_by"),
                            rejection_reason=req_data.get("rejection_reason")
                        )
                logger.info(f"Loaded {len(self.requests)} approval requests")
            except Exception as e:
                logger.error(f"Error loading requests: {e}")

    def _save_requests(self):
        """Save approval requests to file"""
        os.makedirs(os.path.dirname(self.REQUESTS_FILE), exist_ok=True)
        with open(self.REQUESTS_FILE, 'w') as f:
            json.dump({rid: req.to_dict() for rid, req in self.requests.items()}, f, indent=2)

    def _load_rollback_points(self):
        """Load rollback points from file"""
        if os.path.exists(self.ROLLBACKS_FILE):
            try:
                with open(self.ROLLBACKS_FILE, 'r') as f:
                    data = json.load(f)
                    for rb_id, rb_data in data.items():
                        self.rollback_points[rb_id] = RollbackPoint(
                            rollback_id=rb_data["rollback_id"],
                            name=rb_data["name"],
                            description=rb_data["description"],
                            created_at=datetime.fromisoformat(rb_data["created_at"]),
                            git_commit=rb_data["git_commit"],
                            state_snapshot=rb_data["state_snapshot"],
                            tags=rb_data.get("tags", [])
                        )
                logger.info(f"Loaded {len(self.rollback_points)} rollback points")
            except Exception as e:
                logger.error(f"Error loading rollback points: {e}")

    def _save_rollback_points(self):
        """Save rollback points to file"""
        os.makedirs(os.path.dirname(self.ROLLBACKS_FILE), exist_ok=True)
        with open(self.ROLLBACKS_FILE, 'w') as f:
            json.dump({rid: rb.to_dict() for rid, rb in self.rollback_points.items()}, f, indent=2)

    def _load_audit_log(self):
        """Load audit log"""
        if os.path.exists(self.AUDIT_FILE):
            try:
                with open(self.AUDIT_FILE, 'r') as f:
                    self.audit_log = json.load(f)
                logger.info(f"Loaded {len(self.audit_log)} audit entries")
            except Exception as e:
                logger.error(f"Error loading audit log: {e}")

    def _save_audit_log(self):
        """Save audit log"""
        os.makedirs(os.path.dirname(self.AUDIT_FILE), exist_ok=True)
        with open(self.AUDIT_FILE, 'w') as f:
            json.dump(self.audit_log[-1000:], f, indent=2)  # Keep last 1000

    def _log_audit(self, action: str, details: dict):
        """Log a governance action"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details
        }
        self.audit_log.append(entry)
        self._save_audit_log()

    def _clean_expired_requests(self):
        """Mark expired requests"""
        for req in self.requests.values():
            if req.status == ApprovalStatus.PENDING and req.is_expired():
                req.status = ApprovalStatus.EXPIRED
        self._save_requests()

    def configure_gate(self, gate_type: GateType, 
                       required_approvers: List[str] = None,
                       auto_approve_after_hours: int = None):
        """Configure a governance gate"""
        if gate_type not in self.gate_configs:
            self.gate_configs[gate_type] = {}

        if required_approvers is not None:
            self.gate_configs[gate_type]["required_approvers"] = required_approvers
        if auto_approve_after_hours is not None:
            self.gate_configs[gate_type]["auto_approve_after_hours"] = auto_approve_after_hours

        logger.info(f"Configured gate: {gate_type.value}")

    def request_approval(self, gate_type: GateType, requester: str,
                        action_description: str, action_data: dict = None,
                        expires_in_hours: int = 24) -> ApprovalRequest:
        """Request approval for a critical action"""
        config = self.gate_configs.get(gate_type, {})

        request_id = hashlib.md5(f"{gate_type.value}:{requester}:{datetime.now().isoformat()}".encode()).hexdigest()[:12]

        request = ApprovalRequest(
            request_id=request_id,
            gate_type=gate_type,
            requester=requester,
            action_description=action_description,
            action_data=action_data or {},
            required_approvers=config.get("required_approvers", ["tejas"]),
            expires_at=datetime.now() + __import__("datetime").timedelta(hours=expires_in_hours)
        )

        self.requests[request_id] = request
        self._save_requests()

        self._log_audit("approval_requested", {
            "request_id": request_id,
            "gate_type": gate_type.value,
            "requester": requester,
            "action_description": action_description
        })

        logger.info(f"Approval requested: {request_id} ({gate_type.value})")
        return request

    def approve(self, request_id: str, approver_id: str) -> dict:
        """Approve a request (or add approval)"""
        if request_id not in self.requests:
            return {"success": False, "error": "Request not found"}

        request = self.requests[request_id]

        if request.status != ApprovalStatus.PENDING:
            return {"success": False, "error": f"Request already {request.status.value}"}

        if not request.can_approve(approver_id):
            return {"success": False, "error": "Not authorized to approve or already approved"}

        request.current_approvals.append(approver_id)

        # Check if all approvals received
        if set(request.current_approvals) >= set(request.required_approvers):
            request.status = ApprovalStatus.APPROVED
            request.decided_at = datetime.now()
            request.decided_by = approver_id

            self._log_audit("approval_granted", {
                "request_id": request_id,
                "approver": approver_id,
                "all_approvers": request.current_approvals
            })
        else:
            self._log_audit("approval_added", {
                "request_id": request_id,
                "approver": approver_id,
                "remaining": list(set(request.required_approvers) - set(request.current_approvals))
            })

        self._save_requests()
        return {"success": True, "status": request.status.value}

    def reject(self, request_id: str, approver_id: str, reason: str) -> dict:
        """Reject a request"""
        if request_id not in self.requests:
            return {"success": False, "error": "Request not found"}

        request = self.requests[request_id]

        if request.status != ApprovalStatus.PENDING:
            return {"success": False, "error": f"Request already {request.status.value}"}

        if approver_id not in request.required_approvers:
            return {"success": False, "error": "Not authorized to reject"}

        request.status = ApprovalStatus.REJECTED
        request.decided_at = datetime.now()
        request.decided_by = approver_id
        request.rejection_reason = reason

        self._save_requests()

        self._log_audit("approval_rejected", {
            "request_id": request_id,
            "approver": approver_id,
            "reason": reason
        })

        return {"success": True, "status": request.status.value}

    def check_approval(self, request_id: str) -> dict:
        """Check if a request is approved"""
        if request_id not in self.requests:
            return {"approved": False, "error": "Request not found"}

        request = self.requests[request_id]

        # Check auto-approval
        if request.status == ApprovalStatus.PENDING:
            config = self.gate_configs.get(request.gate_type, {})
            auto_hours = config.get("auto_approve_after_hours")
            if auto_hours is not None and auto_hours >= 0:
                elapsed = (datetime.now() - request.created_at).total_seconds() / 3600
                if elapsed >= auto_hours:
                    request.status = ApprovalStatus.APPROVED
                    request.decided_at = datetime.now()
                    request.decided_by = "auto"
                    self._save_requests()
                    self._log_audit("auto_approved", {"request_id": request_id})

        return {
            "approved": request.status == ApprovalStatus.APPROVED,
            "status": request.status.value,
            "request": request.to_dict()
        }

    def create_rollback_point(self, name: str, description: str,
                              git_commit: str = None,
                              state_snapshot: dict = None,
                              tags: List[str] = None) -> RollbackPoint:
        """Create a rollback point"""
        rollback_id = hashlib.md5(f"{name}:{datetime.now().isoformat()}".encode()).hexdigest()[:12]

        # Get current git commit if not provided
        if not git_commit:
            import subprocess
            try:
                result = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd="/a0/usr/workdir/garuda-system",
                    capture_output=True,
                    text=True
                )
                git_commit = result.stdout.strip() if result.returncode == 0 else "unknown"
            except:
                git_commit = "unknown"

        rollback = RollbackPoint(
            rollback_id=rollback_id,
            name=name,
            description=description,
            created_at=datetime.now(),
            git_commit=git_commit,
            state_snapshot=state_snapshot or {},
            tags=tags or []
        )

        self.rollback_points[rollback_id] = rollback
        self._save_rollback_points()

        self._log_audit("rollback_point_created", {
            "rollback_id": rollback_id,
            "name": name,
            "git_commit": git_commit
        })

        logger.info(f"Rollback point created: {rollback_id} ({name})")
        return rollback

    def execute_rollback(self, rollback_id: str, requester: str) -> dict:
        """Execute a rollback to a saved point"""
        if rollback_id not in self.rollback_points:
            return {"success": False, "error": "Rollback point not found"}

        rollback = self.rollback_points[rollback_id]

        # Request approval for rollback
        approval = self.request_approval(
            gate_type=GateType.ROLLBACK,
            requester=requester,
            action_description=f"Rollback to: {rollback.name}",
            action_data={"rollback_id": rollback_id},
            expires_in_hours=1
        )

        # Auto-approve rollbacks immediately
        result = self.check_approval(approval.request_id)

        if result["approved"]:
            # Execute git rollback
            import subprocess
            try:
                subprocess.run(
                    ["git", "reset", "--hard", rollback.git_commit],
                    cwd="/a0/usr/workdir/garuda-system",
                    check=True
                )

                self._log_audit("rollback_executed", {
                    "rollback_id": rollback_id,
                    "name": rollback.name,
                    "requester": requester
                })

                return {"success": True, "message": f"Rolled back to {rollback.name}"}
            except subprocess.CalledProcessError as e:
                return {"success": False, "error": f"Git rollback failed: {e}"}

        return {"success": False, "error": "Rollback not approved"}

    def get_pending_approvals(self, approver_id: str = None) -> List[dict]:
        """Get pending approval requests"""
        pending = []
        for req in self.requests.values():
            if req.status == ApprovalStatus.PENDING:
                if approver_id is None or approver_id in req.required_approvers:
                    pending.append(req.to_dict())
        return pending

    def get_rollback_points(self, tags: List[str] = None) -> List[dict]:
        """Get available rollback points"""
        points = []
        for rb in self.rollback_points.values():
            if tags is None or any(tag in rb.tags for tag in tags):
                points.append(rb.to_dict())
        return sorted(points, key=lambda x: x["created_at"], reverse=True)

    def get_status(self) -> dict:
        """Get governance status"""
        return {
            "total_requests": len(self.requests),
            "pending_requests": len([r for r in self.requests.values() if r.status == ApprovalStatus.PENDING]),
            "rollback_points": len(self.rollback_points),
            "audit_entries": len(self.audit_log),
            "configured_gates": list(self.gate_configs.keys())
        }


def get_governance_manager() -> GovernanceManager:
    """Get singleton governance manager"""
    global _governance_manager
    if '_governance_manager' not in globals():
        _governance_manager = GovernanceManager()
    return _governance_manager
