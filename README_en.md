# skill-subtraction

> The core of AI skill management is "lean and focused," not "more is better."

A systematic audit tool for installed AI skills, practicing the philosophy of **regular subtraction**. Scans all installed skills, evaluates their value by category, and generates structured keep / archive / uninstall recommendations to help users maintain a lean and efficient skill set.

Inspired by Swyx (Latent Space host / smol.ai founder) on AI skill management — most people habitually keep adding skills, installing every new one they see, ending up with dozens but rarely using most of them.

## Why Subtraction?

| Problem | Description |
|---------|-------------|
| **Cognitive overload** | More skills = higher selection cost, defeating the purpose of efficiency |
| **Judgment interference** | Outdated skills act as noise, clouding decisions when facing new problems |
| **High maintenance cost** | Skills need updates and debugging; too many means wasted effort |

## Features

- **Auto-scan**: One-click scan of all installed skills under `~/.workbuddy/skills/` and the current workspace's `.workbuddy/skills/`
- **Categorized evaluation**: Classifies skills into Tool / Business / News / Productivity types, scoring across 5 metrics (usage frequency, necessity, current relevance, maintenance status, unique value)
- **Smart recommendations**: Auto-generates keep / archive / uninstall suggestions with special rules for deduplication, disabled-skill detection, and project-end detection
- **Safe cleanup**: Archive operations save skill configurations first; uninstall only executes after user confirmation — never deletes without consent

## Directory Structure

```
skill-subtraction/
├── SKILL.md                          # Main skill definition (workflow + trigger rules)
├── LICENSE                           # MIT License
├── README.md                         # Chinese README
├── README_en.md                      # English README (this file)
├── .gitignore
├── scripts/
│   └── audit_skills.py               # Skill scanning script, outputs structured JSON
└── references/
    └── evaluation_framework.md       # Full evaluation framework (categories, scoring matrix, dedup rules)
```

## Installation

### Option 1: Manual Install

```bash
# Clone the repository
git clone https://github.com/<your-username>/skill-subtraction.git

# Copy to WorkBuddy skills directory
cp -r skill-subtraction ~/.workbuddy/skills/
```

### Option 2: Direct Download

Download the ZIP, extract it, and place the `skill-subtraction` folder under `~/.workbuddy/skills/`.

## Usage

In a WorkBuddy conversation, simply say:

- "Check what skills I have installed"
- "Do a skill subtraction"
- "Which skills should I delete"
- "Audit my skills"

The skill auto-triggers and executes a 5-step workflow:

1. **Scan** — Run `audit_skills.py` to collect metadata for all installed skills
2. **Classify** — Categorize into Tool / Business / News / Productivity types
3. **Evaluate** — Score across 5 weighted metrics, composite score ranges 21-100
4. **Recommend** — Generate keep / archive / uninstall report
5. **Cleanup** — Execute after user confirmation (archive saves config first)

### Run the Scan Script Directly

```bash
# Scan user-level skills
python3 scripts/audit_skills.py

# Scan project-level skills with a specific workspace
python3 scripts/audit_skills.py --workspace /path/to/workspace
```

Example JSON output:

```json
{
  "audit_time": "2026-08-12 10:30:00",
  "total_skills": 7,
  "user_skills": 7,
  "project_skills": 0,
  "skills": [
    {
      "name": "skill-subtraction",
      "scope": "user",
      "path": "~/.workbuddy/skills/skill-subtraction",
      "description": "Skill subtraction — audit and cleanup of installed skills...",
      "agent_created": true,
      "file_count": 4,
      "dir_size_kb": 12.5,
      "last_modified": "2026-08-12 10:30:00"
    }
  ]
}
```

## Evaluation Framework

### Scoring Matrix

| Composite Score | Recommendation | Description |
|----------------|----------------|-------------|
| 80-100 | Keep | High-value skill, master it deeply |
| 50-79 | Archive | Uncertain value, save config then uninstall, re-activate when needed |
| 21-49 | Uninstall | Low value, clean up directly |

### Special Rules (Override Scoring)

1. **Zero usage + irrelevant → Uninstall directly**
2. **Complete overlap → Keep the best one** (deduplication)
3. **Disabled + unused for 90 days → Uninstall**
4. **Project-level + project ended → Uninstall**
5. **Data source defunct → Uninstall**

See [`references/evaluation_framework.md`](references/evaluation_framework.md) for the full framework.

## Audit Cycle Recommendations

| Frequency | Scenario |
|-----------|----------|
| Quarterly | When skill count exceeds 10 |
| After each project ends | Clean up project-level skills |
| When business direction shifts | Re-evaluate business-type skills |
| When feeling "too many skills" | Anytime |

## Requirements

- Python 3.10+
- WorkBuddy (or a compatible AI assistant platform)

## License

[MIT](LICENSE)
