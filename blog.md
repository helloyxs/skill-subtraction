# 你的 AI 助手装了多少技能？是时候做一次"技能减法"了

> 大多数人用 AI 的习惯是不断做加法——看到一个技能就装一个，结果堆了几十个，真正用的没几个。是时候反其道而行之。

## 一个被忽视的问题：AI 技能的"囤积症"

如果你是一个重度 AI 助手用户，大概率经历过这样的场景：

- 看到一个酷炫的技能 → 装上
- 朋友推荐一个效率工具 → 装上
- 平台更新预装了一批模板 → 照单全收
- 自己让 AI 帮忙写了个定制技能 → 也留着

三个月后，你打开技能列表，发现堆了四五十个技能。你记不清一半技能是干什么的，另一半你压根没用过。更要命的是——当你在对话中提出一个需求时，AI 助手需要在海量技能描述中做匹配，**认知负荷从人转移到了机器，但效率损耗是一样的**。

这不是个别现象。Swyx（Latent Space 主播 / smol.ai 创始人）早就指出过：**AI 技能管理的核心是"精而专"，而非"多而全"。**

于是，[skill-subtraction](https://github.com/helloyxs/skill-subtraction) 诞生了。

---

## skill-subtraction 是什么

一句话：**给 AI 助手的技能做系统性审计和减法清理的命令行工具。**

它干三件事：

1. **扫描** 全部已安装技能，提取元数据（文件数、大小、版本、最近修改时间、是否 Agent 创建……）
2. **评估** 每个技能的价值，用六维指标加权打分（24–100 分）
3. **建议** 每个技能该保留、归档还是卸载，生成结构化报告

整个过程安全可控——**不擅自卸载任何东西**，所有清理操作都需要用户确认。

---

## 五步工作流：从扫描到清理

### 第一步：一键扫描

运行审计脚本，自动检测当前 Agent 平台并扫描其已安装技能：

```bash
# 自动检测当前 Agent（推荐）
python3 scripts/audit_skills.py

# 扫描所有已安装的 Agent 平台
python3 scripts/audit_skills.py --all

# 指定自定义技能目录（如 Windows 非标准路径）
python3 scripts/audit_skills.py --skills-dir "C:\Users\admin\AppData\Roaming\LobsterAI\SKILLs"

# 同时扫描项目级技能
python3 scripts/audit_skills.py --workspace /path/to/workspace
```

脚本输出一份结构化 JSON 报告。以下是真实的扫描结果（来自作者本人的 WorkBuddy 环境）：

```json
{
  "audit_time": "2026-08-12 16:22:54",
  "total_skills": 7,
  "source_stats": {
    "agent_created": 5,
    "not_agent_created": 2,
    "disabled": 2,
    "batch_detected": 0
  },
  "skills": [
    {
      "name": "aihot",
      "description": "查询 AI HOT 的中文 AI 资讯、精选、当前热点和日报...",
      "agent_created": true,
      "file_count": 8,
      "dir_size_kb": 28.4,
      "last_modified": "2026-08-03 08:56:37",
      "version": "1.2.1"
    },
    {
      "name": "ecom-customer-service",
      "description": "电商智能客服助手...",
      "agent_created": true,
      "disable_model_invocation": true,
      "file_count": 6,
      "last_modified": "2026-08-11 16:59:30"
    }
    // ... 更多技能
  ]
}
```

**跨平台兼容**：脚本在 Windows 上自动处理 GBK 编码问题，支持 `AppData/Roaming/<Agent>/SKILLs` 非标准路径。在 macOS / Linux 上通过脚本路径自动反推所属 Agent 平台。

### 第二步：分类评估

扫描拿到原始数据后，进入分类评估环节。每个技能从三个维度切入：

**维度一：技能类型**

| 类型 | 定义 | 典型示例 |
|------|------|---------|
| 工具类 | 通用型操作工具，跨项目复用 | 浏览器自动化、文档处理、文件操作 |
| 业务型 | 与特定项目/业务方向绑定 | 竞品分析、电商客服、法律文书 |
| 资讯类 | 信息获取与聚合 | AI 新闻聚合、GitHub 趋势追踪 |
| 生产力类 | 日常工作流增强 | 周报生成、会议纪要、任务管理 |
| 平台预装 | 出厂自带，用户未主动选择 | `agent_created=false` + 批量安装特征 |

**维度二：安装来源**（影响评估策略）

| 来源 | 识别方法 | 评估策略 |
|------|---------|---------|
| 用户主动安装 | `agent_created=false`，非批量 | 正常六指标评分 |
| 平台预装 | `agent_created=false`，同日批量 ≥ 5 个 | 按业务方向整批筛选 |
| Agent 创建 | `agent_created=true` | 重点关注创建目的是否仍有效 |

**维度三：六指标加权打分**（24–100 分）

这是评估框架的核心。每个技能在六个维度上被逐一评分，加权求和得到总分：

| 指标 | 权重 | 设计理由 |
|------|------|---------|
| 使用频率 | 25 分 | 权重最高——用不用是决定去留的第一标准 |
| 必要性 | 20 分 | 没有它行不行，决定不可替代程度 |
| 当前相关性 | 20 分 | 技能再好，跟当前方向不匹配也要清理 |
| 启用状态 | 15 分 | 已禁用的技能不出现在上下文中，不提供自动价值 |
| 维护状态 | 10 分 | 长期不更新可能已失效 |
| 独特价值 | 10 分 | 功能重叠的技能只留最优的一个 |

这个权重设计有意思——**使用频率占 25%，必要性 + 相关性占 40%**，说明框架优先看"现在到底还用不用"，而非"理论上好不好用"。这符合"定期做减法"的理念：减法的目的是保持活跃技能集的高信噪比。

### 第三步：生成建议

根据综合评分，每个技能被归入三类：

| 综合评分 | 建议 | 操作 |
|---------|------|------|
| 80–100 | **保留** | 深度掌握，定期更新 |
| 50–79 | **归档** | 保存提示词和配置文档后卸载，需要时重新激活 |
| 24–49 | **卸载** | 直接清理 |

但评分不是唯一的判据。框架内置了**八条特殊规则**，它们优先于评分矩阵：

1. 零使用 + 不相关 → 直接卸载
2. 完全重叠 → 保留最优的一个（去重）
3. 已禁用且从未手动调用 → 卸载
4. 项目级 + 项目已结束 → 卸载
5. 数据源失效 → 卸载
6. 平台预装 + 批量安装 + 与当前业务不匹配 → 整批归档
7. 平台预装 + 用户从未主动触发 → 归档（非卸载，预装技能可能被平台依赖）
8. 批量安装检测 → 同日创建 ≥ 5 个时作为一组评估

规则 6 和 7 值得特别说一下。很多人装好 AI 助手后发现平台预装了几十个模板技能（HR、财务、法务、销售全覆盖），但自己只做工程开发。逐个评分既费时又没意义——**直接按业务方向整批归档**才是高效做法。而预装技能之所以建议"归档"而非"卸载"，是因为某些平台功能可能依赖它们，归档后遇到问题可以快速恢复。

### 第四步：输出审计报告

报告格式清晰直观：

```markdown
# 技能减法审计报告

**审计时间**：2026-08-12
**技能总数**：7 个（用户级 7 个，项目级 0 个）

## 保留（4 个）

| 技能 | 类型 | 保留理由 | 使用频率 |
|------|------|---------|---------|
| skill-subtraction | 工具类 | 核心审计工具，每周使用 | 高 |
| ... | ... | ... | ... |

## 归档（2 个）

| 技能 | 类型 | 归档理由 | 重新激活条件 |
|------|------|---------|------------|
| ecom-customer-service | 业务型 | 已禁用，当前无电商项目 | 重新启动电商业务时 |
| ... | ... | ... | ... |

## 卸载（1 个）

| 技能 | 类型 | 卸载理由 | 风险评估 |
|------|------|---------|---------|
| ... | ... | 零使用 + 与当前方向不相关 | 低 |

## 汇总建议

- 当前技能集健康度：中
- 主要问题：2 个技能已禁用且从未手动调用
- 下次审计建议时间：2026-11-01
```

### 第五步：执行清理（需用户确认）

报告生成后，工具会询问用户是否执行清理操作。**每一步操作前都会展示将要执行的动作，获得明确确认后才执行。**

三种操作的处理方式：

- **保留**：不做任何操作
- **归档**：将技能的 SKILL.md 全文、关键参考文档、脚本清单整理为一个 Markdown 文件，保存到当前 Agent 对应的归档目录（如 `~/.workbuddy/skill-archive/<skill-name>.md`），确认写入成功后再卸载技能
- **卸载**：直接使用 SkillManage 删除技能

归档操作的设计体现了"安全第一"的理念——**不是简单卸载，而是保存核心知识以便未来快速恢复**。归档文件包含完整的 SKILL.md 原文、参考文档摘要和脚本清单，确保重新激活时有据可依。

---

## 技术设计亮点

### 1. 零配置自动检测 Agent 平台

脚本不需要写死路径。它通过自身所在路径反推当前 Agent 平台：

```python
def detect_current_agent() -> tuple[str, Path] | None:
    """
    标准路径结构: ~/.<agent>/skills/<skill-name>/scripts/audit_skills.py
    Windows 非标准: C:\\Users\\<user>\\AppData\\Roaming\\<Agent>\\SKILLs\\<skill-name>\\scripts\\audit_skills.py
    """
    script_path = Path(__file__).resolve()
    # scripts/audit_skills.py → skill-dir/ → skills/ (or SKILLs/)
    # parents[0] = scripts/, parents[1] = skill-dir/, parents[2] = skills dir
    skills_dir = script_path.parents[2]
    agent_dir = script_path.parents[3]
    agent_name = agent_dir.name
    # 去掉前导点：.workbuddy → workbuddy
    if agent_name.startswith('.'):
        agent_name = agent_name[1:]
    agent_name = agent_name.lower()
    return agent_name, skills_dir
```

这意味着——**装在 `~/.workbuddy/skills/` 下就扫 WorkBuddy，装在 `~/.codex/skills/` 下就扫 Codex，装在 `~/.claude/skills/` 下就扫 Claude**。同一份脚本，跨平台、跨 Agent，零配置。

### 2. 可靠性设计：绝不静默失败

这是整个工具最值得称道的工程实践。脚本在所有可能失败的环节都主动记录 issue，输出到 JSON 的 `issues` 字段并通过 stderr 打印摘要：

| Issue 类型 | 严重度 | 说明 |
|------------|--------|------|
| `missing_skill_md` | error | 技能目录缺少 SKILL.md |
| `unreadable_skill_md` | error | SKILL.md 编码异常（非 UTF-8） |
| `permission_denied` | error | 目录/文件权限不足 |
| `no_frontmatter` | warning | SKILL.md 没有 YAML frontmatter |
| `malformed_frontmatter` | warning | frontmatter 内容解析异常 |
| `no_name_field` | warning | frontmatter 缺少 name 字段（已用目录名兜底） |
| `empty_description` | warning | frontmatter description 为空 |
| `not_a_directory` | warning | 技能目录下出现普通文件 |
| `broken_symlink` | error | 符号链接指向不存在的位置 |

每个 issue 都记录了路径、类型、严重度和具体信息。stderr 摘要让你一眼看出扫描是否完整：

```
[WARN] 扫描完成但发现 6 个问题（2 个技能）
  - 错误: 3 个（可能导致技能被跳过）
  - 警告: 3 个（信息不完整但仍可处理）
  问题类型分布:
    missing_skill_md: 3
    not_a_directory: 3
```

退出码也有讲究：**0 表示完全正常，2 表示扫描完成但有 error 级问题**——方便 CI/CD 流水线接入。

### 3. 批量安装检测：识别平台预装的"全家桶"

脚本会自动检测批量安装的技能组。当多个技能共享相同创建日期（±1 天内）且数量 ≥ 5 个时，标记为"批量安装"：

```python
def detect_batch_installs(skills: list[dict]) -> list[dict]:
    """
    检测批量安装的技能组。
    当多个技能共享相同创建日期（±1天内）且数量 ≥ 5 个时，标记为批量安装。
    """
    date_groups: dict[str, list[str]] = {}
    for s in skills:
        mtime = s.get('last_modified', '')
        if mtime == 'unknown' or not mtime:
            continue
        date_str = mtime[:10]  # YYYY-MM-DD
        date_groups.setdefault(date_str, []).append(s['name'])

    batches = []
    for date_str, names in date_groups.items():
        if len(names) >= 5:
            batches.append({
                'date': date_str,
                'count': len(names),
                'skills': sorted(names)
            })
    batches.sort(key=lambda x: -x['count'])
    return batches
```

这个功能直击痛点——平台预装的"全家桶"技能是技能膨胀的主要来源。识别出批量组后，建议作为一组评估而非逐个打分，大幅提升审计效率。

### 4. 归档而非删除：安全第一

归档操作的规范体现了"可逆"的设计理念：

1. 读取技能的 SKILL.md 全文
2. 如有 `references/` 目录，读取关键参考文档
3. 如有 `scripts/` 目录，记录脚本文件名和用途
4. 整理为一个 Markdown 文件，保存到当前 Agent 对应的归档目录
5. **确认归档文件写入成功后，再执行卸载操作**

归档文件格式规范：

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

这意味着归档不是信息丢失，而是信息转移。需要时可以从归档文件恢复技能配置，甚至直接重新安装。

---

## 实战：一次真实的技能审计

以下是作者本人环境中的真实审计结果。扫描 WorkBuddy 用户级技能目录，发现 7 个技能：

| 技能 | 安装来源 | 状态 | 评估结论 |
|------|---------|------|---------|
| aihot | Agent 创建 | 启用 | ✅ 保留 — 资讯类，AI 新闻聚合，高频使用 |
| competitor-analysis | Agent 创建 | 启用 | ✅ 保留 — 业务型，竞品分析框架，与当前工作方向匹配 |
| ecom-customer-service | Agent 创建 | **已禁用** | 📦 归档 — 当前无电商项目，已禁用且从未手动调用 |
| follow-builders | Agent 创建 | 启用 | ✅ 保留 — 资讯类，AI builders 内容追踪 |
| skill-subtraction | Agent 创建 | 启用 | ✅ 保留 — 工具类，本工具自身 |
| ... | ... | ... | ... |

**审计结论**：技能集健康度为"中"。主要问题是有一个已禁用且从未手动调用的电商客服技能，建议归档。没有发现批量安装的预装技能组，说明技能集较为精简。

整个审计过程不到 30 秒——扫描脚本 + 分类评估 + 生成报告。如果手动逐一检查 7 个技能的 frontmatter、文件大小、修改时间，至少需要 10 分钟，而且很容易遗漏已禁用的技能。

---

## 审计周期建议

| 频率 | 适用场景 |
|------|---------|
| 每季度 | 技能数量超过 10 个时 |
| 每个项目结束时 | 清理项目级技能 |
| 业务方向调整时 | 评估业务型技能的相关性 |
| 感觉"技能太多"时 | 随时触发 |

我的建议是把它加进你的**季度技术债清理流程**——就像清理 `node_modules` 和 Docker 镜像一样，定期跑一次 `audit_skills.py`，保持技能集精简。

---

## 快速上手

### 安装

```bash
# 克隆仓库
git clone https://github.com/helloyxs/skill-subtraction.git

# 复制到你的 AI 助手技能目录
cp -r skill-subtraction ~/.workbuddy/skills/   # WorkBuddy
# 或
cp -r skill-subtraction ~/.codex/skills/       # Codex
# 或
cp -r skill-subtraction ~/.claude/skills/      # Claude
```

### 使用

在 AI 助手对话中直接说：

- "帮我检查一下装了哪些技能"
- "做一次技能减法"
- "哪些技能该删"
- "审计我的技能"

技能会自动触发，执行完整的五步工作流。

### 直接运行脚本

```bash
python3 scripts/audit_skills.py              # 扫描当前 Agent
python3 scripts/audit_skills.py --all         # 扫描所有已安装的 Agent
python3 scripts/audit_skills.py --help        # 查看完整用法
```

### 技术要求

- Python 3.10+
- 任何支持技能目录结构的 AI 助手平台（WorkBuddy / Codex / Claude / Cursor / Cline / LobsterAI 等）

---

## 写在最后：减法的哲学

做减法不是目的，而是手段。

我们清理技能集，不是为了"拥有更少的技能"，而是为了让**留下的每一个技能都被充分使用、持续维护、与当前工作方向高度匹配**。这和代码库的重构是同一个道理——删掉死代码不是为了减少代码量，而是让活代码更清晰、更可维护。

skill-subtraction 试图把这种"定期做减法"的理念变成一个可执行的流程：

- **可扫描**：一键获取全量技能元数据，不用手动翻目录
- **可评估**：六指标加权打分 + 八条特殊规则，避免拍脑袋决策
- **可追溯**：归档操作保存完整配置，不丢知识
- **可安全**：所有清理操作需用户确认，不擅自删除

它开源在 GitHub 上（MIT 协议），欢迎 Star、Fork、Issue。

> **技能管理的核心是"精而专"，而非"多而全"。**
> **定期做减法，让你的 AI 助手保持认知清爽。**

---

*项目地址：[github.com/helloyxs/skill-subtraction](https://github.com/helloyxs/skill-subtraction)*
*License：MIT | Python 3.10+ | 跨平台（macOS / Linux / Windows）*
