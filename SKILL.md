---
name: skill-subtraction
version: 1.2.0
description: "技能减法 — 已安装技能审计与减法清理。当用户要求检查已安装技能、清理技能、做技能减法、评估技能保留与否、审计 skill、整理技能列表时触发此 Skill。典型场景：'帮我检查一下装了哪些技能'、'哪些技能该删'、'做一次技能减法'、'审计我的技能'、'skill audit'、'技能减法'。此 Skill 扫描所有已安装技能，按工具类/业务型分类评估，生成保留与卸载建议报告。支持中文和英文报告输出（根据用户语言或 --lang 参数自动选择）。"
agent_created: true
required_commands:
  - python3
required_environment_variables: []
required_privileges: non-root
metadata:
  required_binaries:
    - python3
  hermes:
    platform: cross-platform (macOS, Linux, Windows)
---

# 技能减法

## 概述

对已安装的 AI 技能进行系统性审计，践行"定期做减法"的理念。扫描全部已安装技能，按类别评估使用价值，生成结构化的保留/卸载建议报告，帮助用户保持技能集精简高效。

## 核心理念

技能管理的核心是"精而专"，而非"多而全"。大多数人的习惯是不断做加法——看到一个技能就装一个，结果堆了几十个，真正用的没几个。定期做减法可以：

- **保持认知清爽**：让大脑专注于核心任务，提高决策效率
- **提升资源利用率**：把有限的精力和时间投入到最有价值的技能上
- **更好地应对变化**：随着业务和技术的变化，快速调整技能组合

做减法的三个理由：
1. 认知负荷过重：技能越多，选择成本越高，违背提效初衷
2. 干扰判断：过时技能像噪音，干扰面对新问题时的判断
3. 维护成本高：技能需要更新调试，过多意味着无谓的精力消耗

## 何时使用 / When to Use

- 用户要求检查/审计已安装的技能 / User asks to check/audit installed skills
- 用户想做技能清理/减法 / User wants to clean up / do skill subtraction
- 用户想知道哪些技能该留、哪些该删 / User wants to know which skills to keep or delete
- 用户感觉技能太多、记不住、不知道该用哪个 / User feels they have too many skills
- 定期（如每季度）技能盘点 / Regular (e.g., quarterly) skill inventory

## 运行要求 / Requirements

| 依赖 Dependency | 要求 Requirement | 说明 Notes |
|------|---------|---------|
| Python | 3.10+ | 仅使用标准库，无第三方依赖 Only stdlib, no third-party deps |
| 运行时 Runtime | `python3` 可执行命令 Available on PATH | 扫描脚本由本 Skill 调用 The audit script is invoked by this Skill |
| 权限 Privileges | 非 root / non-root | 扫描为只读；卸载/归档操作必须经用户确认 Scan is read-only; uninstall/archive requires user confirmation |
| 平台 Platforms | WorkBuddy / Codex / Claude Code / Cursor / Cline / Continue / LobsterAI | 遵循 `~/.<agent>/skills/` 目录约定 Follows the `~/.<agent>/skills/` directory convention |
| 环境变量 Env Vars | 无 None | 不依赖任何环境变量 No environment variables required |

## 语言自动检测

本 Skill 支持中文和英文两种报告语言，**根据用户当前对话语言自动判断，不主动询问**：

- 用户用中文交流 → 输出中文报告，脚本传 `--lang zh`
- 用户用英文交流 → 输出英文报告，脚本传 `--lang en`
- **无法判断语言时** → 询问用户："中文报告还是英文报告？"

确定语言后，所有后续步骤（脚本执行、评估、报告输出）均使用该语言。

## 工作流程

### 第一步：扫描已安装技能

运行审计脚本，自动检测当前脚本所在的 Agent 平台，只扫描该平台下的已安装技能。**根据检测到的对话语言自动传 `--lang zh` 或 `--lang en`**，无需用户指定：

```bash
# 自动检测当前 Agent，扫描同级技能（推荐）
# 中文对话时：python3 scripts/audit_skills.py --lang zh
# 英文对话时：python3 scripts/audit_skills.py --lang en
python3 scripts/audit_skills.py --lang zh

# 手动指定 Agent
python3 scripts/audit_skills.py --agent codex

# 扫描所有已安装的 Agent 平台
python3 scripts/audit_skills.py --all

# 指定自定义技能目录（如 Windows LobsterAI 的非标准路径）
python3 scripts/audit_skills.py --skills-dir "C:\Users\admin\AppData\Roaming\LobsterAI\SKILLs"

# 同时扫描项目级技能
python3 scripts/audit_skills.py --workspace /path/to/workspace
```

**跨平台兼容**：脚本在 Windows 上自动处理 GBK 编码问题，支持 `AppData/Roaming/<Agent>/SKILLs` 非标准路径。

**可靠性保证**：

脚本在所有可能失败的环节都主动记录 issue，最终输出到 JSON 的 `issues` 字段，并通过 stderr 打印摘要。

支持的 issue 类型：

| 类型 | 严重度 | 说明 |
|------|--------|------|
| `missing_skill_md` | error | 技能目录缺少 SKILL.md |
| `unreadable_skill_md` | error | SKILL.md 编码异常（非 UTF-8） |
| `permission_denied` | error | 目录/文件权限不足 |
| `no_frontmatter` | warning | SKILL.md 没有 YAML frontmatter |
| `malformed_frontmatter` | warning | frontmatter 内容解析异常 |
| `no_name_field` | warning | frontmatter 缺少 name 字段 |
| `empty_description` | warning | frontmatter description 为空 |
| `not_a_directory` | warning | 技能目录下出现普通文件 |
| `broken_symlink` | error | 符号链接指向不存在的位置 |

**退出码**：0 表示完全正常，2 表示扫描完成但有 error 级问题（方便 CI 接入）。

脚本输出 JSON 数组，每个元素包含：
- `name`：技能名称
- `agent`：所属 Agent 平台（自动检测，如 workbuddy / codex / claude）
- `scope`：作用域（user / project）
- `path`：技能目录路径
- `description`：技能描述（从 frontmatter 提取）
- `agent_created`：是否为 Agent 创建
- `has_scripts`：是否包含脚本
- `has_references`：是否包含参考文档
- `file_count`：文件总数
- `dir_size`：目录大小（KB）
- `last_modified`：最近修改时间
- `version`：技能版本

**输出中的统计字段**：
- `source_stats`：安装来源统计（agent_created 数量、平台预装数量、已禁用数量、批量安装检测数量）
- `batch_installs`：批量安装检测（当同一天创建 ≥ 5 个技能时标记为批量，含日期、数量、技能列表）

### 第二步：分类评估

按文末「评估框架 / Evaluation Framework」章节执行分类与评分。对每个技能进行三维度分类：

**维度一：技能类型 / Skill Type**

| 类型 Type | 定义 Definition | 典型特征 Typical Features |
|------|------|---------|
| 工具类 Tool | 通用型操作工具，跨项目复用 General-purpose tools, cross-project | 浏览器操作、文档处理、PDF 处理、邮件发送、文件格式转换 Browser automation, document processing, PDF, email, file conversion |
| 业务型 Business | 与特定项目、业务方向绑定的技能 Tied to specific project/business domain | 竞品分析、客服回复、行业报告生成 Competitor analysis, customer service, industry reports |
| 资讯类 News | 信息获取与聚合类技能 Information gathering and aggregation | AI 新闻、趋势追踪、RSS 聚合 AI news, trend tracking, RSS |
| 生产力类 Productivity | 日常工作流程增强技能 Daily workflow enhancement | 周报生成、会议纪要、任务管理 Weekly reports, meeting notes, task management |
| 平台预装 Platform-preinstalled | Agent 平台出厂自带，用户未主动选择 Pre-installed by platform, not user-chosen | `agent_created=false` + 批量安装特征 Batch install pattern |

**维度二：安装来源（影响评估策略，不单独打分）/ Install Source (affects evaluation strategy, not scored separately)**

| 来源 Source | 识别方法 Detection | 评估策略 Strategy |
|------|---------|---------|
| 用户主动安装 User-installed | `agent_created=false`，非批量安装 | 正常六指标评分 Full 6-metric scoring |
| 平台预装 Platform-preinstalled | `agent_created=false`，批量安装（同日 ≥ 5 个）Batch install (≥5 same day) | 优先按业务方向整批筛选，不匹配的整批归档 Filter by business direction, batch archive non-matching |
| Agent 创建 Agent-created | `agent_created=true` | 重点关注创建目的是否仍然有效 Focus on whether original purpose still valid |

**维度三：评估指标（百分制）/ Evaluation Metrics (100-point scale)**

对每个技能逐一评估以下指标，加权求和得出总分（24-100 分）：
Evaluate each skill across the following weighted metrics (composite score: 24-100):

1. **使用频率 Usage Frequency（25 分）**：高（每天/每周）/ 中（每月）/ 低（几个月一次）/ 零（装了就没用过）High (daily/weekly) / Medium (monthly) / Low (few months) / Zero (never used)
2. **必要性 Necessity（20 分）**：不可替代 / 有替代方案 / 可有可无 Irreplaceable / Has alternatives / Nice-to-have
3. **当前相关性 Current Relevance（20 分）**：与当前业务方向匹配 / 部分匹配 / 已不相关 Matches current direction / Partial match / Irrelevant
4. **启用状态 Enabled Status（15 分）**：已启用（自动触发）/ 已禁用但偶尔手动调用 / 已禁用且从未手动调用 Enabled (auto-trigger) / Disabled but manually invoked / Disabled & never invoked
5. **维护状态 Maintenance（10 分）**：近期有更新 / 偶尔更新 / 长期未更新 / 已废弃 Active / Occasional / Stale / Deprecated
6. **独特价值 Unique Value（10 分）**：提供独有能力 / 与其他技能重叠 / 可被通用能力替代 Unique capability / Overlaps / Replaceable by general capabilities

### 第三步：生成建议

根据评估结果，将每个技能归入以下三类之一：
Based on evaluation results, categorize each skill into one of three actions:

| 建议 Recommendation | 判定条件 Criteria | 操作 Action |
|------|---------|------|
| **保留 Keep** | 综合评分 80-100 分；工具类且高频使用；或业务型且当前业务方向匹配且近期有使用记录 Score 80-100; Tool type & high frequency; or Business type matching current direction with recent usage | 深度掌握，定期更新 Master deeply, update regularly |
| **归档 Archive** | 综合评分 50-79 分；暂时不用但未来可能需要；或业务型且业务方向正在转型 Score 50-79; temporarily unused but may need later; or Business type during direction transition | 保存提示词和配置文档，卸载技能 Save prompt & config docs, uninstall skill |
| **卸载 Uninstall** | 综合评分 24-49 分；零使用且无独有价值；或与其他技能高度重叠；或已不相关且长期未更新 Score 24-49; zero usage & no unique value; or high overlap; or irrelevant & stale | 直接卸载 Uninstall directly |

特殊规则 / Special Rules (Override Scoring):
- 同功能技能只保留最优的一个（去重）/ Keep only the best among functionally identical skills (dedup)
- 已禁用且从未手动调用的技能，优先建议卸载 / Disabled & never manually invoked → prioritize uninstall
- 资讯类技能如果与用户当前关注方向不匹配，建议卸载 / News-type skills not matching current focus → uninstall
- 项目级技能如果对应项目已结束，建议卸载 / Project-level skills for ended projects → uninstall
- **平台预装 + 批量安装 + 与当前业务不匹配 → 整批归档** / Platform-preinstalled + batch + no match → batch archive（不逐个评分，直接按业务方向筛选 / Don't score individually, filter by business direction）
- **平台预装 + 用户从未主动触发 → 归档（非卸载）** / Platform-preinstalled + never triggered → archive (not uninstall)（预装技能可能被平台依赖 / Pre-installed skills may be platform-dependent）

### 第四步：输出审计报告

根据「语言自动检测」章节确定的语言，选择对应格式输出报告。

**使用中文时，按以下格式输出：**

```markdown
# 技能减法审计报告

**审计时间**：YYYY-MM-DD
**技能总数**：N 个（用户级 X 个，项目级 Y 个）

## 保留（N 个）

| 技能 | 类型 | 保留理由 | 使用频率 |
|------|------|---------|---------|
| ... | ... | ... | ... |

## 归档（N 个）

| 技能 | 类型 | 归档理由 | 重新激活条件 |
|------|------|---------|------------|
| ... | ... | ... | ... |

## 卸载（N 个）

| 技能 | 类型 | 卸载理由 | 风险评估 |
|------|------|---------|---------|
| ... | ... | ... | ... |

## 汇总建议

- 当前技能集健康度：高/中/低
- 主要问题：...
- 下次审计建议时间：...
```

**使用英文时，按以下格式输出：**

```markdown
# Skill Subtraction Audit Report

**Audit Date**: YYYY-MM-DD
**Total Skills**: N (User-level: X, Project-level: Y)

## Keep (N)

| Skill | Type | Reason to Keep | Usage Frequency |
|-------|------|---------------|-----------------|
| ... | ... | ... | ... |

## Archive (N)

| Skill | Type | Reason to Archive | Reactivation Condition |
|-------|------|--------------------|-----------------------|
| ... | ... | ... | ... |

## Uninstall (N)

| Skill | Type | Reason to Uninstall | Risk Assessment |
|-------|------|---------------------|-----------------|
| ... | ... | ... | ... |

## Summary

- Current skill set health: High/Medium/Low
- Main issues: ...
- Recommended next audit: ...
```

### 第五步：执行清理（需用户确认）/ Step 5: Execute Cleanup (User Confirmation Required)

输出报告后，询问用户是否要执行清理操作。**不擅自卸载任何技能**。
After outputting the report, ask the user whether to execute cleanup. **Never uninstall skills without consent.**

用户可选择 / User options:

- **执行清理 Execute Cleanup**：用户确认后按建议逐项操作 / Execute recommended actions after user confirmation
  - **卸载 Uninstall**：使用 SkillManage 删除技能 / Use SkillManage to delete the skill
  - **归档 Archive**：将技能的 SKILL.md 和关键配置文件内容保存到当前 Agent 对应的归档目录 `~/.<agent>/skill-archive/<skill-name>.md`（如 WorkBuddy → `~/.workbuddy/skill-archive/`，Codex → `~/.codex/skill-archive/`，Claude → `~/.claude/skill-archive/`），然后卸载技能 / Save SKILL.md and key config files to the agent's archive directory, then uninstall
  - **保留 Keep**：不做操作 / No action
- **仅查看报告 Report Only**：不做任何操作，用户自行决定后续行动 / No action, user decides later

每一步操作前都向用户展示将要执行的动作，获得明确确认后才执行。
Show the user each action before executing, and only proceed after explicit confirmation.

## 审计周期建议 / Audit Cycle Recommendations

| 频率 Frequency | 适用场景 Scenario |
|------|---------|
| 每季度 Quarterly | 技能数量超过 10 个时 When skill count exceeds 10 |
| 每个项目结束时 After each project ends | 清理项目级技能 Clean up project-level skills |
| 业务方向调整时 When business direction shifts | 评估业务型技能的相关性 Re-evaluate business-type skills |
| 感觉"技能太多"时 When feeling "too many skills" | 随时触发 Anytime |

## 捆绑资源

### scripts/

- `audit_skills.py` — 自动检测当前脚本所在的 Agent 平台，扫描该平台下的所有已安装技能（如 `~/.workbuddy/skills/`、`~/.codex/skills/`、`~/.claude/skills/` 等）及当前工作区项目级技能，解析 frontmatter，输出结构化 JSON 报告

### references/

- `evaluation_framework.md` — 评估框架完整双语版，保留在仓库中供查阅；ClawHub 发布包不含此文件，核心内容已内嵌于文末「评估框架 / Evaluation Framework」章节。Full bilingual framework, kept in the repo; the ClawHub package does not include it — core content is embedded in the Evaluation Framework section below.

## 评估框架 / Evaluation Framework

> 核心评估框架内嵌于此，供技能运行时直接参考（ClawHub 发布包不含 `references/` 目录）。完整双语版见仓库 `references/evaluation_framework.md`。
> Core framework embedded for runtime use (the ClawHub package does not include `references/`). Full bilingual version: `references/evaluation_framework.md` in the repo.

### 六指标评分细则 / Six-Metric Scoring Detail

| 指标 Metric | 权重 Weight | 等级与得分 Levels & Scores |
|------|------|---------|
| 使用频率 Usage Frequency | 25 | 高 High 25 / 中 Medium 16 / 低 Low 8 / 零 Zero 4 |
| 必要性 Necessity | 20 | 不可替代 Irreplaceable 20 / 有替代方案 Has alternatives 12 / 可有可无 Nice-to-have 4 |
| 当前相关性 Current Relevance | 20 | 匹配 Match 20 / 部分匹配 Partial 12 / 不相关 Irrelevant 4 |
| 启用状态 Enabled Status | 15 | 已启用 Enabled 15 / 禁用但近期手动调用 Disabled but recently invoked 9 / 禁用且从未调用 Disabled & never invoked 3 |
| 维护状态 Maintenance | 10 | 活跃 Active (≤30d) 10 / 一般 Normal (30-90d) 6 / 停滞 Stagnant (>90d) 3 |
| 独特价值 Unique Value | 10 | 独有 Unique 10 / 部分独有 Partially unique 6 / 完全重叠 Complete overlap 3 |

综合评分 = 六指标加权求和，范围 24-100。Composite Score = sum of six weighted metrics, range 24-100.

### 判定矩阵 / Decision Matrix

| 综合评分 Score | 建议 Recommendation | 说明 Description |
|------|------|---------|
| 80-100 | 保留 Keep | 高价值技能，深度掌握 High-value, master deeply |
| 50-79 | 归档 Archive | 保存配置后卸载，需要时重新激活 Save config, uninstall, re-activate when needed |
| 24-49 | 卸载 Uninstall | 低价值，直接清理 Low-value, clean up directly |

### 特殊规则（覆盖评分）/ Special Rules (Override Scoring)

1. **零使用 + 不相关 → 直接卸载** / Zero usage + irrelevant → uninstall
2. **完全重叠 → 保留最优的一个**（去重）/ Complete overlap → keep the best one (dedup)
3. **已禁用且从未手动调用 → 直接卸载** / Disabled & never invoked → uninstall
4. **项目级 + 项目已结束 → 卸载** / Project-level + project ended → uninstall
5. **数据源失效 → 卸载** / Data source defunct → uninstall
6. **平台预装 + 批量安装 + 与当前业务不匹配 → 整批归档**（不逐个评分，按业务方向筛选）/ Platform-preinstalled + batch + no match → batch archive (don't score individually, filter by business direction)
7. **平台预装 + 用户从未主动触发 → 归档（非卸载）**（可能被平台依赖）/ Platform-preinstalled + never triggered → archive (not uninstall, may be platform-dependent)
8. **批量安装检测**：同一天创建 ≥ 5 个技能（±1 天）→ 标记批量安装，整组评估 / Batch detection: ≥ 5 skills created the same day (±1 day) → flag and evaluate as a group

### 去重规则 / Deduplication Rules

按以下优先级保留 / Keep by priority: 功能更完整 More complete functionality → 更近期更新 More recently updated → 使用频率更高 Higher usage frequency → agent_created → 目录更轻量 Lighter directory (file_count / dir_size)。

被去重淘汰的技能标记为「卸载」，理由注明"与 XX 功能重叠，保留更优方案"。Eliminated skills are marked "Uninstall" with reason "Overlaps with XX, keeping the better option".

### 归档操作规范 / Archive Operation Standard

1. 读取技能 SKILL.md 全文 / Read the skill's full SKILL.md
2. 如有 references/ 目录，读取关键参考文档 / If references/ exists, read key reference docs
3. 如有 scripts/ 目录，记录脚本文件名和用途 / If scripts/ exists, record script names and purposes
4. 整理为 Markdown，保存到当前 Agent 对应归档目录 `~/.<agent>/skill-archive/<skill-name>.md`（agent 由脚本路径反推：WorkBuddy → `~/.workbuddy/skill-archive/`，Codex → `~/.codex/skill-archive/`，Claude → `~/.claude/skill-archive/`）/ Save to the archive dir `~/.<agent>/skill-archive/<skill-name>.md`, agent inferred from script path
5. 确认归档文件写入成功后，再执行卸载 / Only uninstall after archive write is confirmed

归档文件模板 / Archive template:

```markdown
# 归档技能 / Archived Skill: <skill-name>
**归档时间 Archive Date**: YYYY-MM-DD
**归档原因 Archive Reason**: ...
**重新激活条件 Reactivation Condition**: ...

## SKILL.md 原文 / Original Content
<完整 SKILL.md 内容 / Full SKILL.md content>

## 参考文档摘要 / Reference Summary
<关键 references 文件内容摘要 / Key references file content summary>

## 脚本清单 / Script Inventory
<scripts/ 目录下文件名及用途 / File names and purposes under scripts/>
```
