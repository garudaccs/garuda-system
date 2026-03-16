#!/usr/bin/env python3
"""
Garuda Pre-Flight Check System
==============================
Validates system readiness before operations.
Implements the governance gate concept from Mission Control.

Version: 0.1.0
Author: Tejas Agnihotri (COO)
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("GARUDA_PREFLIGHT")


class CheckStatus(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    SKIP = "SKIP"


@dataclass
class CheckResult:
    """Result of a single pre-flight check"""
    name: str
    status: CheckStatus
    message: str
    details: Dict = None

    def to_dict(self):
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "details": self.details
        }


class PreFlightCheck:
    """
    Pre-flight validation system.

    Ensures all systems are ready before operations begin.
    Based on Mission Control governance gates.
    """

    def __init__(self, core=None):
        self.core = core
        self.results: List[CheckResult] = []
        self.timestamp = datetime.now()

    def _check(self, name: str, condition: bool, 
               success_msg: str, fail_msg: str,
               warning_msg: str = None, details: Dict = None) -> CheckResult:
        """Helper to create a check result"""
        if condition:
            status = CheckStatus.PASS
            message = success_msg
        elif warning_msg:
            status = CheckStatus.WARNING
            message = warning_msg
        else:
            status = CheckStatus.FAIL
            message = fail_msg

        result = CheckResult(
            name=name,
            status=status,
            message=message,
            details=details
        )
        self.results.append(result)
        return result

    def check_core_loaded(self) -> CheckResult:
        """Check if Garuda Core is loaded"""
        loaded = self.core is not None and self.core.is_healthy()
        return self._check(
            "Core System",
            loaded,
            "Garuda Core is healthy",
            "Garuda Core not loaded or unhealthy"
        )

    def check_agents_loaded(self) -> CheckResult:
        """Check if agents are loaded"""
        if self.core:
            count = len(self.core.agents)
            return self._check(
                "Agents Loaded",
                count > 0,
                f"{count} agents loaded",
                "No agents loaded",
                details={"count": count}
            )
        return self._check("Agents Loaded", False, "", "Core not loaded")

    def check_orchestrator_present(self) -> CheckResult:
        """Check if TEJAS orchestrator is present"""
        if self.core:
            tejas = self.core.get_orchestrator()
            return self._check(
                "Orchestrator (TEJAS)",
                tejas is not None,
                f"TEJAS present: {tejas.full_name if tejas else ""}",
                "TEJAS orchestrator not found"
            )
        return self._check("Orchestrator (TEJAS)", False, "", "Core not loaded")

    def check_lanes_configured(self) -> CheckResult:
        """Check if all lanes are configured"""
        expected_lanes = ["development", "marketing", "research", "operations", "personal"]
        if self.core:
            config_lanes = list(self.core.config.get("lanes", {}).keys())
            missing = [l for l in expected_lanes if l not in config_lanes]
            return self._check(
                "Lanes Configured",
                len(missing) == 0,
                f"All {len(expected_lanes)} lanes configured",
                f"Missing lanes: {missing}",
                details={"expected": expected_lanes, "configured": config_lanes}
            )
        return self._check("Lanes Configured", False, "", "Core not loaded")

    def run_all_checks(self, include_infrastructure: bool = True) -> Dict:
        """Run all pre-flight checks"""
        self.results = []
        self.timestamp = datetime.now()

        # System checks
        self.check_core_loaded()
        self.check_agents_loaded()
        self.check_orchestrator_present()
        self.check_lanes_configured()

        # Calculate summary
        passed = sum(1 for r in self.results if r.status == CheckStatus.PASS)
        failed = sum(1 for r in self.results if r.status == CheckStatus.FAIL)
        warnings = sum(1 for r in self.results if r.status == CheckStatus.WARNING)

        all_passed = failed == 0

        return {
            "timestamp": self.timestamp.isoformat(),
            "all_passed": all_passed,
            "summary": {
                "passed": passed,
                "failed": failed,
                "warnings": warnings,
                "total": len(self.results)
            },
            "results": [r.to_dict() for r in self.results],
            "recommendation": "Proceed" if all_passed else "Fix failures before proceeding"
        }


def run_preflight(core=None, include_infrastructure: bool = True) -> Dict:
    """Convenience function to run pre-flight checks"""
    checker = PreFlightCheck(core)
    return checker.run_all_checks(include_infrastructure)


if __name__ == "__main__":
    # Run standalone pre-flight check
    checker = PreFlightCheck()
    report = checker.run_all_checks()
    print(json.dumps(report, indent=2))
