# 技能减法 · 评估框架

## 一、技能分类体系

### 1. 工具类

**定义**：通用型操作工具，跨项目复用，解决"怎么做"的问题。

**特征**：
- 面向操作而非面向业务
- 功能不随业务方向变化而过时
- 通常是工作流中的基础设施

**示例**：
- 浏览器自动化（操作网页、截图、填表）
- 文档处理（Word/Excel/PDF 读写、格式转换）
- 文件操作（批量重命名、压缩解压）
- 邮件发送
- 代码执行辅助

**保留标准**：高频使用（每天或每周）+ 不可替代（没有它效率大幅降低）

### 2. 业务型

**定义**：与特定项目、业务方向或行业绑定的技能，解决"做什么"的问题。

**特征**：
- 包含业务知识、政策规则、行业术语
- 与特定项目或业务周期相关
- 业务方向变化时可能失效

**示例**：
- 电商客服回复（含退款政策、回复模板）
- 竞品分析报告（含分析框架）
- 金融数据分析（含行业指标）
- 法律文书生成（含法条引用）

**保留标准**：当前正在使用的项目或业务 + 在可预见未来会持续使用

### 3. 资讯类

**定义**：信息获取、聚合和推送类技能。

**特征**：
- 依赖外部数据源（API、RSS、网页）
- 内容时效性强
- 数据源可能失效或迁移

**示例**：
- AI 新闻聚合
- GitHub 趋势追踪
- 社交媒体监控
- 行业报告推送

**保留标准**：信息源稳定 + 与当前关注方向匹配 + 无法被更简单的手段替代

### 4. 生产力类

**定义**：日常工作流程增强技能，提升个人效率。

**特征**：
- 跨项目但面向个人工作习惯
- 基于固定模板或流程
- 依赖个人输入而非外部数据

**示例**：
- 周报生成
- 会议纪要整理
- 任务管理
- 知识库整理

**保留标准**：每周至少使用一次 + 流程确实比手动操作更高效

### 5. 平台预装

**定义**：Agent 平台出厂自带的技能，用户未主动选择安装。

**特征**：
- `agent_created` 为 false 且非用户手动安装
- 多个技能共享相同的创建/修改日期（批量安装特征）
- 描述风格统一（如都是 "Use when..." 模板句式）
- 涵盖多种业务职能（HR/财务/法务/销售/产品等）

**识别方法**：
- 脚本输出的 `agent_created` 字段为 false
- `last_modified` 日期高度集中（如同一天创建 60+ 个）
- 技能名称和描述风格高度相似

**保留标准**：与用户当前工作方向直接匹配 + 用户有过主动使用记录

## 二、评估指标（百分制）

六个指标加权求和，总分 100 分。各指标权重反映其对技能保留决策的影响程度。

### 指标 1：使用频率（25 分）

> 权重最高——用不用是决定去留的第一标准。

| 等级 | 定义 | 分值 |
|------|------|------|
| 高 | 每天 or 每周使用 | 25 |
| 中 | 每月使用 | 16 |
| 低 | 几个月一次 | 8 |
| 零 | 安装后从未使用，或已忘记其存在 | 4 |

### 指标 2：必要性（20 分）

> 没有它行不行，直接决定技能的不可替代程度。

| 等级 | 定义 | 分值 |
|------|------|------|
| 不可替代 | 没有它，对应工作流断裂 | 20 |
| 有替代方案 | 有其他技能或通用能力可覆盖，但本技能更优 | 12 |
| 可有可无 | 通用能力即可完成，技能只是锦上添花 | 4 |

### 指标 3：当前相关性（20 分）

> 技能再好，跟当前方向不匹配也要清理。

| 等级 | 定义 | 分值 |
|------|------|------|
| 匹配 | 与当前核心业务/工作方向直接相关 | 20 |
| 部分匹配 | 与当前方向间接相关，偶尔有用 | 12 |
| 不相关 | 业务方向已变化，或属于已结束的项目 | 4 |

### 指标 4：启用状态（15 分）

> 已禁用的技能不出现在 agent 上下文中，不影响思考，但也不提供自动价值。

| 等级 | 定义 | 分值 |
|------|------|------|
| 已启用 | 自动触发可用，agent 主动考虑是否调用 | 15 |
| 已禁用但近期有手动调用 | 有意降噪保留，偶尔手动 `/skill-name` 调用 | 9 |
| 已禁用且从未手动调用 | 完全闲置，纯占磁盘空间 | 3 |

### 指标 5：维护状态（10 分）

> 长期不更新的技能可能已经失效。

| 等级 | 定义 | 分值 |
|------|------|------|
| 活跃 | 近 30 天内有修改或更新 | 10 |
| 一般 | 30-90 天内有修改 | 6 |
| 停滞 | 90 天以上未修改 | 3 |

### 指标 6：独特价值（10 分）

> 功能重叠的技能只留最优的一个。

| 等级 | 定义 | 分值 |
|------|------|------|
| 独有 | 提供其他技能和通用能力都没有的功能 | 10 |
| 部分独有 | 与其他技能有重叠，但有差异化能力 | 6 |
| 完全重叠 | 与其他技能功能高度重复 | 3 |

## 三、判定矩阵

综合评分 = 使用频率 + 必要性 + 当前相关性 + 启用状态 + 维护状态 + 独特价值

评分范围：24 - 100

| 综合评分 | 建议 | 说明 |
|---------|------|------|
| 80-100 | 保留 | 高价值技能，深度掌握 |
| 50-79 | 归档 | 价值不确定，保存配置后卸载，需要时重新激活 |
| 24-49 | 卸载 | 低价值，直接清理 |

### 特殊规则（覆盖评分）

以下规则优先于评分矩阵：

1. **零使用 + 不相关 → 直接卸载**：不论其他指标如何
2. **完全重叠 → 保留最优的一个**：同功能技能去重
3. **已禁用且从未手动调用 → 直接卸载**：禁用后从未手动调用过，说明完全不需要
4. **项目级 + 项目已结束 → 卸载**：项目结束后清理
5. **数据源失效 → 卸载**：资讯类技能如果数据源已不可用
6. **平台预装 + 批量安装 + 与当前业务不匹配 → 整批归档**：不要逐个评估，直接按业务方向筛选，不匹配的整批归档。典型场景：平台预装了 HR/财务/法务/销售全套模板，但用户只做工程开发
7. **平台预装 + 用户从未主动触发 → 归档（非卸载）**：预装技能可能被平台依赖，归档而非卸载更安全。归档后若平台功能异常可快速恢复
8. **批量安装检测**：当多个技能共享相同创建日期（±1天内）且数量 ≥ 5 个时，标记为"批量安装"，建议作为一组评估而非逐个打分

## 四、去重规则

当发现功能重叠的技能时，按以下优先级保留：

1. 功能更完整的
2. 更近期更新的
3. 使用频率更高的
4. agent_created 的（可自主修改迭代）
5. 目录更轻量的（file_count 更少、dir_size 更小）

被去重淘汰的技能标记为"卸载"，理由注明"与 XX 功能重叠，保留更优方案"。

## 五、归档操作规范

归档不是简单卸载，而是保存技能的核心知识以便未来快速恢复：

1. 读取技能的 SKILL.md 全文
2. 如有 references/ 目录，读取关键参考文档
3. 如有 scripts/ 目录，记录脚本文件名和用途
4. 将以上内容整理为一个 Markdown 文件，保存到当前 Agent 对应的归档目录 `~/.<agent>/skill-archive/<skill-name>.md`（通过脚本路径反推当前 Agent，如 WorkBuddy → `~/.workbuddy/skill-archive/`，Codex → `~/.codex/skill-archive/`，Claude → `~/.claude/skill-archive/`）
5. 文件格式：

```markdown
# 归档技能：<skill-name>

**归档时间**：YYYY-MM-DD
**归档原因**：...
**重新激活条件**：...

## SKILL.md 原文

<完整 SKILL.md 内容>

## 参考文档摘要

<关键 references 文件内容摘要>

## 脚本清单

<scripts/ 目录下文件名及用途>
```

6. 确认归档文件写入成功后，再执行卸载操作

---

# Skill Subtraction · Evaluation Framework

## I. Skill Classification System

### 1. Tool Type

**Definition**: General-purpose operational tools, reusable across projects, solving "how to do" problems.

**Characteristics**:
- Operation-oriented rather than business-oriented
- Functionality doesn't become outdated with business direction changes
- Usually infrastructure in workflows

**Examples**:
- Browser automation (web page operation, screenshots, form filling)
- Document processing (Word/Excel/PDF read-write, format conversion)
- File operations (batch rename, compress/decompress)
- Email sending
- Code execution assistance

**Keep Criteria**: High frequency (daily or weekly) + irreplaceable (without it, efficiency drops significantly)

### 2. Business Type

**Definition**: Skills tied to specific projects, business directions, or industries, solving "what to do" problems.

**Characteristics**:
- Contains business knowledge, policy rules, industry terminology
- Related to specific projects or business cycles
- May become invalid when business direction changes

**Examples**:
- E-commerce customer service replies (with refund policies, reply templates)
- Competitor analysis reports (with analysis frameworks)
- Financial data analysis (with industry metrics)
- Legal document generation (with legal clause references)

**Keep Criteria**: Currently in use for active projects or business + will continue to be used in the foreseeable future

### 3. News Type

**Definition**: Information gathering, aggregation, and push-type skills.

**Characteristics**:
- Depends on external data sources (API, RSS, web pages)
- Strong timeliness of content
- Data sources may fail or migrate

**Examples**:
- AI news aggregation
- GitHub trend tracking
- Social media monitoring
- Industry report feeds

**Keep Criteria**: Stable information source + matches current focus + cannot be replaced by simpler means

### 4. Productivity Type

**Definition**: Daily workflow enhancement skills, boosting personal efficiency.

**Characteristics**:
- Cross-project but oriented toward personal work habits
- Based on fixed templates or processes
- Relies on personal input rather than external data

**Examples**:
- Weekly report generation
- Meeting notes organization
- Task management
- Knowledge base organization

**Keep Criteria**: Used at least once a week + process is genuinely more efficient than manual operation

### 5. Platform-preinstalled

**Definition**: Skills that come pre-installed with the Agent platform, not actively chosen by the user.

**Characteristics**:
- `agent_created` is false and not manually installed by user
- Multiple skills share the same creation/modification date (batch install pattern)
- Uniform description style (e.g., all "Use when..." template phrases)
- Covers multiple business functions (HR/finance/legal/sales/product, etc.)

**Identification Method**:
- Script output `agent_created` field is false
- `last_modified` dates are highly concentrated (e.g., 60+ created same day)
- Skill names and description styles are highly similar

**Keep Criteria**: Directly matches user's current work direction + user has active usage records

## II. Evaluation Metrics (100-point scale)

Six metrics weighted and summed for a total score of 100. Weights reflect their impact on skill retention decisions.

### Metric 1: Usage Frequency (25 pts)

> Highest weight — whether it's used is the primary criterion for keep/remove.

| Level | Definition | Score |
|-------|-----------|-------|
| High | Daily or weekly use | 25 |
| Medium | Monthly use | 16 |
| Low | Once every few months | 8 |
| Zero | Never used after install, or forgotten | 4 |

### Metric 2: Necessity (20 pts)

> Whether you can do without it directly determines irreplaceability.

| Level | Definition | Score |
|-------|-----------|-------|
| Irreplaceable | Without it, the corresponding workflow breaks | 20 |
| Has alternatives | Other skills or general capabilities can cover, but this one is better | 12 |
| Nice-to-have | General capabilities suffice, skill is just icing on the cake | 4 |

### Metric 3: Current Relevance (20 pts)

> No matter how good a skill is, if it doesn't match current direction, it should be cleaned up.

| Level | Definition | Score |
|-------|-----------|-------|
| Match | Directly related to current core business/work direction | 20 |
| Partial match | Indirectly related, occasionally useful | 12 |
| Irrelevant | Business direction has changed, or belongs to ended project | 4 |

### Metric 4: Enabled Status (15 pts)

> Disabled skills don't appear in agent context, don't affect thinking, but also don't provide automatic value.

| Level | Definition | Score |
|-------|-----------|-------|
| Enabled | Auto-trigger available, agent actively considers calling | 15 |
| Disabled but recently manually invoked | Intentionally kept for noise reduction, occasionally called via `/skill-name` | 9 |
| Disabled & never manually invoked | Completely idle, purely wasting disk space | 3 |

### Metric 5: Maintenance Status (10 pts)

> Long-unupdated skills may have already failed.

| Level | Definition | Score |
|-------|-----------|-------|
| Active | Modified or updated within last 30 days | 10 |
| Normal | Modified within 30-90 days | 6 |
| Stagnant | Not modified for 90+ days | 3 |

### Metric 6: Unique Value (10 pts)

> Only keep the best among functionally overlapping skills.

| Level | Definition | Score |
|-------|-----------|-------|
| Unique | Provides functionality no other skill or general capability has | 10 |
| Partially unique | Overlaps with other skills but has differentiated capabilities | 6 |
| Complete overlap | Highly redundant with other skills | 3 |

## III. Decision Matrix

Composite Score = Usage Frequency + Necessity + Current Relevance + Enabled Status + Maintenance Status + Unique Value

Score range: 24 - 100

| Composite Score | Recommendation | Description |
|----------------|----------------|-------------|
| 80-100 | Keep | High-value skill, master deeply |
| 50-79 | Archive | Uncertain value, save config then uninstall, re-activate when needed |
| 24-49 | Uninstall | Low value, clean up directly |

### Special Rules (Override Scoring)

The following rules take priority over the scoring matrix:

1. **Zero usage + irrelevant → Uninstall directly**: Regardless of other metrics
2. **Complete overlap → Keep the best one**: Deduplicate functionally identical skills
3. **Disabled & never manually invoked → Uninstall directly**: If never manually called after disabling, it's completely unnecessary
4. **Project-level + project ended → Uninstall**: Clean up after project ends
5. **Data source defunct → Uninstall**: News-type skills with non-functional data sources
6. **Platform-preinstalled + batch install + no match with current business → Batch archive**: Don't evaluate individually; filter by business direction and batch archive non-matching ones. Typical scenario: platform pre-installed HR/finance/legal/sales templates, but user only does engineering
7. **Platform-preinstalled + never triggered by user → Archive (not uninstall)**: Pre-installed skills may be platform-dependent; archiving is safer than uninstalling. If platform functions abnormally after archiving, can quickly restore
8. **Batch install detection**: When multiple skills share the same creation date (±1 day) and count ≥ 5, flagged as "batch install"; recommend evaluating as a group rather than scoring individually

## IV. Deduplication Rules

When functionally overlapping skills are found, keep in the following priority order:

1. More complete functionality
2. More recently updated
3. Higher usage frequency
4. Agent-created (can self-modify and iterate)
5. Lighter directory (fewer file_count, smaller dir_size)

Skills eliminated by deduplication are marked as "Uninstall" with reason "Overlaps with XX, keeping the better option".

## V. Archive Operation Standard

Archiving is not simply uninstalling — it saves the skill's core knowledge for quick future recovery:

1. Read the skill's full SKILL.md
2. If references/ directory exists, read key reference docs
3. If scripts/ directory exists, record script file names and purposes
4. Organize the above into a Markdown file, save to the current Agent's archive directory `~/.<agent>/skill-archive/<skill-name>.md` (inferred from script path: WorkBuddy → `~/.workbuddy/skill-archive/`, Codex → `~/.codex/skill-archive/`, Claude → `~/.claude/skill-archive/`)
5. File format:

```markdown
# Archived Skill: <skill-name>

**Archive Date**: YYYY-MM-DD
**Archive Reason**: ...
**Reactivation Condition**: ...

## SKILL.md Original Content

<Full SKILL.md content>

## Reference Document Summary

<Key references file content summary>

## Script Inventory

<scripts/ directory file names and purposes>
```

6. Confirm the archive file was written successfully, then execute uninstall

## VI. Frontmatter Specification & Metadata Standard

To ensure maximum cross-platform compatibility across Agent platforms (Codex, Claude Code, Cursor, WorkBuddy, etc.), `SKILL.md` YAML frontmatter follows strict standard conventions:

1. **Standard Top-Level Fields**:
   - `name`: Lowercase hyphenated string (e.g., `skill-subtraction`).
   - `description`: English-primary capability and trigger description, ending with Chinese trigger keywords (covering `skill audit`, `do a skill subtraction`, `技能减法`, `审计已安装技能`).
2. **Non-Standard & Extended Attributes**:
   - Top-level frontmatter must only contain standard fields (`name` and `description`).
   - Non-standard attributes such as `version`, `agent_created`, `required_commands`, `required_privileges`, `metadata.hermes` should be placed inside a nested `metadata:` dictionary or documented within Markdown body sections (`## Requirements` / `## Metadata`).

