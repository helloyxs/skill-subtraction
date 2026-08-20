---
name: skill-subtraction
description: "Audit installed AI skills and recommend keep / archive / uninstall to keep your skill set lean and focused. Triggers when the user asks for a skill audit, to check or list installed skills, do a skill subtraction or cleanup, decide which skills to keep or delete, declutter or slim down their skill list, or find redundant or duplicate skills. Scans all installed skills across agent platforms, classifies them into 6 industry functional domains (dev & engineering, data & connectors, content & media, domain business, productivity, meta & agent control) plus subcategories, scores each on 6 weighted metrics, and generates a structured keep / archive / uninstall report with dedup and batch-install detection. Supports bilingual output (English / Chinese). 技能减法：审计已安装技能，生成保留/归档/卸载建议报告。当用户要求检查已安装技能、清理技能、做技能减法、审计 skill、评估技能去留、整理技能列表时触发。"
---

# Skill Subtraction (技能减法)

Audit your installed AI skills and cut the fat — a systematic, score-based review of every installed skill with clear keep / archive / uninstall recommendations.

## Why subtraction (核心理念)

Most people keep adding skills — install one, see another, install that too — until dozens pile up and few get real use. Regular subtraction keeps the set lean:

- **认知清爽**：技能越少，选择成本越低
- **资源聚焦**：把精力投入到最有价值的技能上
- **维护省心**：技能需要更新调试，越少负担越轻

## Requirements (运行要求)

| Dependency | Requirement | Notes |
|------|---------|---------|
| Python | 3.10+ | Stdlib only, no third-party deps |
| Runtime | `python3` on PATH | The audit script is invoked by this skill |
| Privileges | Non-root | Scan is read-only; uninstall/archive requires user confirmation |
| Platforms | WorkBuddy / Codex / Claude Code / Cursor / Cline / Continue / LobsterAI | Follows the `~/.<agent>/skills/` directory convention |
| Env vars | None | No environment variables required |

## Language auto-detection (语言自动检测)

Never ask the user to select a language upfront. Automatically detect and choose the report language based on the user's input:

- **Chinese input / conversation** → Output Chinese report directly, run script with `--lang zh`
- **English input / conversation** → Output English report directly, run script with `--lang en`
- **Ambiguous / Undetectable input** → Only if the language is truly ambiguous (e.g., pure numbers or code only), ask the user: "中文报告还是英文报告？ / Output in Chinese or English?"

Once determined, stick to that language for all workflow steps (scan, evaluation, report, confirmation).

## Workflow (工作流程)

### Step 1: Scan installed skills

Run the audit script; it auto-detects the hosting agent platform from its own path and scans that platform's installed skills (plus project-level skills in the current workspace). Pass `--lang zh|en` to match the conversation language:

```bash
python3 scripts/audit_skills.py --lang zh   # or --lang en
python3 scripts/audit_skills.py --agent codex
python3 scripts/audit_skills.py --all
python3 scripts/audit_skills.py --skills-dir "C:\Users\admin\AppData\Roaming\LobsterAI\SKILLs"
python3 scripts/audit_skills.py --archives              # scan the detected agents' archive inventories
python3 scripts/audit_skills.py --archive-dir /path/to/skill-archive
python3 scripts/audit_skills.py --workspace /path/to/workspace
```

Cross-platform notes: the script handles Windows GBK encoding and non-standard `AppData/Roaming/<Agent>/SKILLs` paths. Every failure point logs an issue into the JSON `issues` field and prints a stderr summary. Issue types: `missing_skill_md`, `unreadable_skill_md`, `permission_denied`, `broken_symlink` (error level); `no_frontmatter`, `malformed_frontmatter`, `no_name_field`, `empty_description`, `not_a_directory` (warning level). Exit codes: 0 = clean, 2 = scan done with error-level issues (CI-friendly).

Output includes installed skills plus a separate `archived_skills` inventory; archive records include their archive date, reason, reactivation condition, source path, and integrity indicator. `--archives` checks each detected agent's default `~/.<agent>/skill-archive/`; `--archive-dir` checks a specified archive directory. Archived records are never counted as installed skills or fed into keep/archive/uninstall scoring.

### Step 2: Classify & score

Apply the classification and scoring from the [Evaluation framework](#evaluation-framework-评估框架) section (full detail in `references/evaluation_framework.md` — read it for complex scenarios):

- **6 Functional Domains & Subcategories**: Dev & System / Data & Connectors / Content & Media / Domain & Business / Productivity & Workflow / Meta & Agent Control
- **Install Source** (decoupled dimension): user-installed / platform-preinstalled / agent-created
- **6 weighted metrics** (composite 24–100): usage frequency 25, necessity 20, current relevance 20, enabled status 15, maintenance 10, unique value 10

### Step 3: Recommend

Map the composite score to keep / archive / uninstall using the decision matrix and special rules in the [Evaluation framework](#evaluation-framework-评估框架) section.

### Step 4: Output the report

Using the language determined in the auto-detection section, output the matching template:

```markdown
# 技能减法审计报告

**审计时间**：YYYY-MM-DD
**技能总数**：N 个（用户级 X 个，项目级 Y 个）

## 保留（N 个）

| 技能 | 类型 | 细分领域 | 保留理由 | 使用频率 |
|------|------|---------|---------|---------|
| ... | ... | ... | ... | ... |

## 归档（N 个）

| 技能 | 类型 | 细分领域 | 归档理由 | 重新激活条件 |
|------|------|---------|---------|------------|
| ... | ... | ... | ... | ... |

## 卸载（N 个）

| 技能 | 类型 | 细分领域 | 卸载理由 | 风险评估 |
|------|------|---------|---------|---------|
| ... | ... | ... | ... | ... |

## 汇总建议

- 当前技能集健康度：高/中/低
- 主要问题：...
- 下次审计建议时间：...
```

When archive inventory scanning is requested, add an **已归档技能库** / **Archived Inventory** section after the summary. List the archive date, original archive reason, reactivation condition, and whether the saved record contains `SKILL.md` source. This is an inventory and recovery-readiness check, not a recommendation to reinstall anything.

```markdown
# Skill Subtraction Audit Report

**Audit Date**: YYYY-MM-DD
**Total Skills**: N (User-level: X, Project-level: Y)

## Keep (N)

| Skill | Type | Subcategory | Reason to Keep | Usage Frequency |
|-------|------|-------------|---------------|-----------------|
| ... | ... | ... | ... | ... |

## Archive (N)

| Skill | Type | Subcategory | Reason to Archive | Reactivation Condition |
|-------|------|-------------|--------------------|-----------------------|
| ... | ... | ... | ... | ... |

## Uninstall (N)

| Skill | Type | Subcategory | Reason to Uninstall | Risk Assessment |
|-------|------|-------------|---------------------|-----------------|
| ... | ... | ... | ... | ... |

## Summary

- Current skill set health: High/Medium/Low
- Main issues: ...
- Recommended next audit: ...
```

### Step 5: Execute cleanup (user confirmation required)

After outputting the report, ask the user whether to execute cleanup. **Never uninstall skills without consent.**

- **Execute cleanup**: uninstall (via SkillManage) / archive (save SKILL.md and key config files to `~/.<agent>/skill-archive/<skill-name>.md`, then uninstall) / keep (no action)
- **Report only**: no action, the user decides later

Show each action before executing; proceed only after explicit confirmation.

## Audit cycle recommendations (审计周期建议)

| Frequency | Scenario |
|------|---------|
| Quarterly | When skill count exceeds 10 |
| After each project ends | Clean up project-level skills |
| When business direction shifts | Re-evaluate business-type skills |
| When feeling "too many skills" | Anytime |

## Bundled resources (捆绑资源)

- `scripts/audit_skills.py` — auto-detects the hosting agent platform, scans all installed skills, parses frontmatter, outputs structured JSON
- `scripts/audit_skills.py --archives` — separately scans default archived-skill records; `--archive-dir` supports a custom archive location
- `references/evaluation_framework.md` — full bilingual framework: classification, 6-metric scoring detail, decision matrix, special rules, dedup priority, archive standard and template. Read it for complex scenarios (batch dedup, archive recovery, platform-preinstalled batch filtering)
- `examples/` — sample audit reports (English & Chinese), useful as expected-output references and demo material

## Evaluation framework (评估框架)

> Core scoring tables and decision matrix below for daily use. Full detail (classification, dedup priority, archive standard & template) in `references/evaluation_framework.md` — read it for complex scenarios.

### Six-metric scoring detail (六指标评分细则)

| Metric | Weight | Levels & scores |
|------|------|---------|
| Usage frequency | 25 | high 25 / medium 16 / low 8 / zero 4 |
| Necessity | 20 | irreplaceable 20 / has alternatives 12 / nice-to-have 4 |
| Current relevance | 20 | match 20 / partial 12 / irrelevant 4 |
| Enabled status | 15 | enabled 15 / disabled but recently invoked 9 / disabled & never invoked 3 |
| Maintenance | 10 | active ≤ 30d 10 / normal 30–90d 6 / stagnant > 90d 3 |
| Unique value | 10 | unique 10 / partially unique 6 / complete overlap 3 |

Composite = weighted sum, range 24–100.

### Decision matrix (判定矩阵)

| Score | Recommendation | Description |
|------|------|---------|
| 80–100 | Keep | High-value, master deeply |
| 50–79 | Archive | Save config, uninstall, re-activate when needed |
| 24–49 | Uninstall | Low value, clean up directly |

### Special rules (特殊规则，覆盖评分)

1. Zero usage + irrelevant → uninstall
2. Complete overlap → keep the best one (dedup)
3. Disabled & never invoked → uninstall
4. Project-level + project ended → uninstall
5. Data source defunct → uninstall
6. Platform-preinstalled + batch + no match → batch archive (don't score individually, filter by business direction)
7. Platform-preinstalled + never triggered → archive (not uninstall; may be platform-dependent)
8. Batch detection: ≥ 5 skills created the same day (±1 day) → flag and evaluate as a group

### Dedup & archive details (去重与归档细则)

- **Dedup**: overlapping skills keep only the best one; eliminated ones are marked "uninstall" with "overlaps with X" as the reason. Keep priority: complete → recently updated → high frequency → agent-created → lightweight (see `references/evaluation_framework.md` §4)
- **Archive**: target `~/.<agent>/skill-archive/<skill-name>.md` (see Step 5); full steps and file template in `references/evaluation_framework.md` §5
