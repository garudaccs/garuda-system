# 🦅 Garuda Autonomous System

> Self-evolving, smart multi-agent orchestration system for Adhiratha Digital Solutions

## Overview

Garuda is a multi-agent system inspired by the best patterns from:
- **Gas Town / Agency** - MEOW orchestration, Git-backed persistence
- **BMAD Method** - Structured workflow lifecycle
- **Paperclip / Mission Control** - Company structure, heartbeats, atomic execution
- **Skills.sh / Anthropic** - Skill-based agent capabilities

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    GARUDA AUTONOMOUS SYSTEM                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ORCHESTRATOR: Tejas Agnihotri (COO)                           │
│       │                                                          │
│       ├── Development Lane (Head: Indra Varma)                  │
│       │      ├── Ganesh Iyer - Architect                        │
│       │      ├── Arjun Reddy - Senior Developer                 │
│       │      ├── Rudra Pratap - DevOps                          │
│       │      ├── Yami Gupta - QA Lead                           │
│       │      ├── Priya Sharma - Backend                         │
│       │      └── Michael Chen - Frontend                        │
│       │                                                          │
│       ├── Marketing Lane (Head: Karthik Menon)                  │
│       │      ├── Surya Narayan - Strategy                       │
│       │      ├── Chandrika Iyer - Content                       │
│       │      ├── Ayesha Khan - Design                           │
│       │      └── David Rodriguez - Social Media                 │
│       │                                                          │
│       ├── Research Lane (Head: Varun Malhotra)                  │
│       │      ├── Saraswati Nair - Knowledge                     │
│       │      └── Sophia Anderson - Analysis                     │
│       │                                                          │
│       ├── Operations Lane (Head: Lakshmi Rao)                   │
│       │      ├── Hanuman Das - Support                          │
│       │      ├── Kali Prasad - Security                         │
│       │      └── Fatima Zahra - Resources                       │
│       │                                                          │
│       └── Personal Lane (Head: Ashwini Kumar)                   │
│              ├── Krishna Murthy - Calendar                      │
│              └── Kamakshi Devi - Wellness                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Infrastructure

| VM | Name | IP | Purpose |
|----|------|-----|----------|
| VM1 | GARUDACCS | 20.33.121.94 | Production (AgentZero, N8N) |
| VM2 | GARUDADEV | 20.47.89.93 | Development (Docker, CI/CD) |

## Model Routing

| Task Type | Model | Provider |
|-----------|-------|----------|
| Architecture | GLM-5 | Z.AI |
| Complex Coding | GLM-5, M2.5 | Z.AI, MiniMax |
| General Coding | GLM-4.7-Flash | Z.AI |
| Document Generation | M2.1 | MiniMax |
| Fast Tasks | GLM-4.7-FlashX | Z.AI |

## Workflow Lifecycle

```
PLANNING → INBOX → ASSIGNED → IN_PROGRESS → TESTING → REVIEW → DONE
```

## Safety Features

- ✅ **Immutable Core** - Core system never breaks
- ✅ **Git-backed Persistence** - State saved in version control
- ✅ **Governance Gates** - Approval required for critical changes
- ✅ **Rollback Capability** - Can restore any previous state
- ✅ **Pre-flight & Post-flight Checks** - Thorough validation at each phase

## Directory Structure

```
/garuda-system/
├── core/           # Immutable core system
├── config/         # Configuration files (garuda.yaml, agents.yaml)
├── agents/         # Agent definitions and prompts
├── lanes/          # Worker lane implementations
├── tools/          # Utility tools
├── skills/         # Installed skills
├── projects/       # Project rigs
└── beads/          # Work items
```

## Buckets

| Bucket | Description |
|--------|-------------|
| Bucket 1 | Personal + MinervaInfo (confidential) |
| Bucket 2 | Adhiratha Digital Solutions (agency) |

## Communication Rule

- ✅ Agency → Personal: Allowed
- ❌ Personal → Agency: Never allowed

## Getting Started

1. Clone this repository
2. Configure credentials in AgentZero secrets
3. Run pre-flight checks
4. Activate TEJAS orchestrator

## Version

- Version: 0.1.0
- Created: 2026-03-16
- Orchestrator: Tejas Agnihotri
