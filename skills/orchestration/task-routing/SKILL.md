# Task Routing

## Metadata
- **ID:** task-routing
- **Version:** 1.0.0
- **Source:** garuda/internal
- **Agents:** tejas
- **Tags:** routing, orchestration, coordination

## Purpose
Intelligent task routing to appropriate lanes and agents.

## Routing Decision Tree

### Step 1: Detect Lane

| Keywords | Lane |
|----------|------|
| code, develop, API, bug, feature, deploy | development |
| marketing, campaign, social, email, content | marketing |
| research, analyze, document, market study | research |
| support, automate, monitor, security | operations |
| personal, calendar, reminder | personal |

### Step 2: Detect Priority

| Indicators | Priority |
|------------|----------|
| urgent, ASAP, critical, down | CRITICAL |
| important, deadline, client | HIGH |
| normal task description | MEDIUM |
| someday, nice to have, backlog | LOW |

### Step 3: Select Agent

1. Check lane head availability
2. Match task to agent specialty
3. Consider current workload
4. Assign and notify

## Routing Examples

```
Task: "Build a new landing page for N3News"
-> Lane: development (keywords: build, page)
-> Priority: MEDIUM (no urgency indicators)
-> Agent: michael (frontend specialist)
```

```
Task: "URGENT: Fix production API outage"
-> Lane: development (keywords: API, fix)
-> Priority: CRITICAL (keyword: URGENT, outage)
-> Agent: arjun (senior developer)
-> Escalate to: tejas, prakash
```

## Routing Commands

### Python API
```python
from tools import route_task
result = route_task("Build user dashboard", bucket=2)
# Returns: lane, agent, priority, confidence
```

### CLI
```bash
python -m tools.lane_router "Create marketing campaign"
```

## Escalation Rules

1. **CRITICAL tasks:** Notify TEJAS immediately
2. **Cross-lane tasks:** TEJAS coordinates
3. **Blocked tasks:** Escalate to lane head
4. **Budget issues:** Notify Lakshmi + TEJAS
