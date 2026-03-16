#!/usr/bin/env python3
"""
Garuda Lane Router - Intelligent Task Routing
=============================================
Analyzes tasks and routes them to appropriate worker lanes.
Implements the MEOW orchestration pattern from Gas Town.

Version: 0.1.0
Author: Tejas Agnihotri (COO)
"""

import re
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

logger = logging.getLogger("GARUDA_ROUTER")


class LaneType(Enum):
    ORCHESTRATION = "orchestration"
    DEVELOPMENT = "development"
    MARKETING = "marketing"
    RESEARCH = "research"
    OPERATIONS = "operations"
    PERSONAL = "personal"


@dataclass
class RoutingDecision:
    lane: str
    confidence: float
    reasoning: str
    suggested_agent: str = None
    priority: str = "MEDIUM"
    keywords_matched: List[str] = None

    def to_dict(self):
        return {
            "lane": self.lane,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "suggested_agent": self.suggested_agent,
            "priority": self.priority,
            "keywords_matched": self.keywords_matched or []
        }


class LaneRouter:
    """Intelligent task router for the Garuda system."""

    LANE_KEYWORDS = {
        "development": {
            "keywords": ["code", "coding", "program", "develop", "build", "api", "backend", "frontend", "database", "docker", "deploy", "git", "github", "vercel", "bug", "fix", "feature", "sprint", "architecture", "test", "qa", "implementation", "software", "web app", "mobile app"],
            "agents": {
                "pm": ["project", "manage", "coordinate", "sprint"],
                "architect": ["design", "architecture", "technical"],
                "developer": ["code", "implement", "build", "develop"],
                "devops": ["deploy", "docker", "infrastructure", "vercel"],
                "qa": ["test", "qa", "bug", "quality"]
            }
        },
        "marketing": {
            "keywords": ["market", "marketing", "campaign", "social media", "content", "brand", "design", "graphic", "ads", "newsletter", "email", "seo", "publer", "instagram", "twitter", "linkedin", "promotion", "launch"],
            "agents": {
                "head": ["strategy", "campaign", "plan"],
                "strategist": ["research", "analyze", "competitor"],
                "content": ["write", "content", "blog", "article"],
                "designer": ["design", "graphic", "visual"],
                "social": ["social media", "post", "schedule"]
            }
        },
        "research": {
            "keywords": ["research", "analyze", "analysis", "study", "investigate", "report", "data", "insights", "trends", "documentation", "document", "wiki", "knowledge"],
            "agents": {
                "head": ["research", "analysis", "insights"],
                "knowledge": ["document", "wiki", "knowledge"],
                "analyst": ["analyze", "data", "trends"]
            }
        },
        "operations": {
            "keywords": ["operations", "support", "customer", "ticket", "security", "compliance", "resource", "subscription", "n8n", "workflow", "automation"],
            "agents": {
                "head": ["operations", "coordinate"],
                "support": ["support", "customer", "ticket"],
                "security": ["security", "compliance"],
                "resources": ["resource", "subscription"]
            }
        },
        "personal": {
            "keywords": ["personal", "calendar", "schedule", "appointment", "health", "wellness", "fitness", "family", "home"],
            "agents": {
                "assistant": ["personal", "schedule"],
                "calendar": ["calendar", "appointment"],
                "wellness": ["health", "wellness"]
            }
        }
    }

    PRIORITY_KEYWORDS = {
        "CRITICAL": ["urgent", "critical", "emergency", "breaking", "asap"],
        "HIGH": ["important", "priority", "deadline", "soon"],
        "LOW": ["eventually", "someday", "nice to have"]
    }

    AGENT_MAP = {
        "development": {"pm": "indra", "architect": "ganesh", "developer": "arjun", "devops": "rudra", "qa": "yami"},
        "marketing": {"head": "karthik", "strategist": "surya", "content": "chandrika", "designer": "ayesha", "social": "david"},
        "research": {"head": "varun", "knowledge": "saraswati", "analyst": "sophia"},
        "operations": {"head": "lakshmi", "support": "hanuman", "security": "kaali", "resources": "fatima"},
        "personal": {"assistant": "ashwini", "calendar": "krishna", "wellness": "kamakshi"}
    }

    def __init__(self, core=None):
        self.core = core

    def analyze_task(self, task_description: str, context: Dict = None) -> RoutingDecision:
        task_lower = task_description.lower()
        lane_scores = {}
        matched_keywords = {}

        for lane, lane_data in self.LANE_KEYWORDS.items():
            score = 0
            matches = []
            for keyword in lane_data["keywords"]:
                if keyword in task_lower:
                    score += 1
                    matches.append(keyword)
            lane_scores[lane] = score
            matched_keywords[lane] = matches

        best_lane = max(lane_scores, key=lane_scores.get)
        best_score = lane_scores[best_lane]
        total_matches = sum(lane_scores.values())

        if total_matches == 0:
            confidence = 0.3
            best_lane = "operations"
            reasoning = "No clear indicators, defaulting to operations"
        else:
            confidence = best_score / total_matches
            reasoning = f"Matched {best_score} keywords for {best_lane} lane"

        suggested_agent = self._suggest_agent(best_lane, task_lower)
        priority = self._determine_priority(task_lower)

        return RoutingDecision(
            lane=best_lane,
            confidence=round(confidence, 2),
            reasoning=reasoning,
            suggested_agent=suggested_agent,
            priority=priority,
            keywords_matched=matched_keywords.get(best_lane, [])
        )

    def _suggest_agent(self, lane: str, task_lower: str) -> str:
        lane_data = self.LANE_KEYWORDS.get(lane, {})
        agents_data = lane_data.get("agents", {})

        best_agent = None
        best_score = 0

        for agent_role, keywords in agents_data.items():
            score = sum(1 for kw in keywords if kw in task_lower)
            if score > best_score:
                best_score = score
                best_agent = agent_role

        if best_agent and lane in self.AGENT_MAP:
            return self.AGENT_MAP[lane].get(best_agent)
        if lane in self.AGENT_MAP:
            return list(self.AGENT_MAP[lane].values())[0]
        return None

    def _determine_priority(self, task_lower: str) -> str:
        for priority, keywords in self.PRIORITY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in task_lower:
                    return priority
        return "MEDIUM"

    def route_to_lane(self, task_description: str, bucket: int = 2) -> Dict:
        if bucket == 1:
            decision = RoutingDecision(lane="personal", confidence=1.0, reasoning="Personal bucket", suggested_agent="ashwini", priority="MEDIUM")
        else:
            decision = self.analyze_task(task_description)

        lane_head = None
        if self.core:
            lane_head_agent = self.core.get_lane_head(decision.lane)
            if lane_head_agent:
                lane_head = lane_head_agent.full_name

        return {
            "timestamp": datetime.now().isoformat(),
            "task": task_description[:100],
            "bucket": bucket,
            "routing": decision.to_dict(),
            "lane_head": lane_head,
            "status": "ready_for_assignment"
        }


def route_task(task_description: str, bucket: int = 2, core=None) -> Dict:
    router = LaneRouter(core)
    return router.route_to_lane(task_description, bucket)


if __name__ == "__main__":
    router = LaneRouter()
    test_tasks = ["Build a landing page", "Create social media campaign", "Research pricing"]
    for task in test_tasks:
        result = router.route_to_lane(task)
        print(f"Task: {task} -> Lane: {result['routing']['lane']}")
