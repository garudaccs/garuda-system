"""
Garuda Tools Module

Core tools for the Garuda Autonomous System.
"""

# Lazy imports to avoid circular dependencies

def run_preflight(*args, **kwargs):
    from .preflight_check import run_preflight as _run_preflight
    return _run_preflight(*args, **kwargs)

def route_task(*args, **kwargs):
    from .lane_router import route_task as _route_task
    return _route_task(*args, **kwargs)

def create_heartbeat_manager(*args, **kwargs):
    from .heartbeat import create_heartbeat_manager as _create
    return _create(*args, **kwargs)

def get_atomic_executor(*args, **kwargs):
    from .atomic_executor import get_atomic_executor as _get
    return _get()

def get_governance_manager(*args, **kwargs):
    from .governance import get_governance_manager as _get
    return _get()

# Expose classes directly (these will be lazy loaded when accessed)
HeartbeatManager = None
HeartbeatStatus = None
AtomicExecutor = None
ExecutionStatus = None
GovernanceManager = None
GateType = None
ApprovalStatus = None

def __getattr__(name):
    """Lazy load classes when accessed"""
    global HeartbeatManager, HeartbeatStatus, AtomicExecutor, ExecutionStatus
    global GovernanceManager, GateType, ApprovalStatus

    if name == "HeartbeatManager":
        from .heartbeat import HeartbeatManager as _cls
        return _cls
    elif name == "HeartbeatStatus":
        from .heartbeat import HeartbeatStatus as _cls
        return _cls
    elif name == "AtomicExecutor":
        from .atomic_executor import AtomicExecutor as _cls
        return _cls
    elif name == "ExecutionStatus":
        from .atomic_executor import ExecutionStatus as _cls
        return _cls
    elif name == "GovernanceManager":
        from .governance import GovernanceManager as _cls
        return _cls
    elif name == "GateType":
        from .governance import GateType as _cls
        return _cls
    elif name == "ApprovalStatus":
        from .governance import ApprovalStatus as _cls
        return _cls

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "run_preflight",
    "route_task",
    "create_heartbeat_manager",
    "get_atomic_executor",
    "get_governance_manager",
    "HeartbeatManager",
    "HeartbeatStatus",
    "AtomicExecutor",
    "ExecutionStatus",
    "GovernanceManager",
    "GateType",
    "ApprovalStatus",
]
