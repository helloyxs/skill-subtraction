# 技能减法 (skill-subtraction)

> AI 技能管理的核心是「精而专」，而非「多而全」。

对已安装的 AI 技能进行系统性审计，践行**定期做减法**的理念。扫描全部已安装技能，按类别评估使用价值，生成结构化的保留 / 归档 / 卸载建议报告，帮助用户保持技能集精简高效。

灵感来源：Swyx（Latent Space 主播 / smol.ai 创始人）关于 AI 技能管理的观点——大多数人用 AI 的习惯是不断做加法，看到一个技能就装一个，结果堆了几十个，真正用的没几个。

## 为什么需要做减法？

| 问题 | 说明 |
|------|------|
| **认知负荷过重** | 技能越多，选择成本越高，违背提效初衷 |
| **干扰判断** | 过时技能像噪音，干扰面对新问题时的判断 |
| **维护成本高** | 技能需要更新调试，过多意味着无谓的精力消耗 |

## 功能

- **自动扫描**：一键扫描当前 Agent 平台下的所有已安装技能。脚本通过自身路径自动检测所属平台——装在 `~/.workbuddy/skills/` 下就扫 WorkBuddy，装在 `~/.codex/skills/` 下就扫 Codex，以此类推；同时支持扫描当前工作区 `.workbuddy/skills/` 下的项目级技能
- **双语输出**：支持中文和英文报告输出，通过 `--lang zh`（默认）或 `--lang en` 控制；stderr 消息、问题描述、审计报告模板均完整双语化
- **多平台兼容**：不只支持 WorkBuddy，还兼容 Codex、Claude Code、Cursor、Cline、Continue、LobsterAI 等采用 `~/.<agent>/skills/` 目录约定的 AI 助手平台；`--all` 可一键扫描机器上所有已安装的平台
- **分类评估**：按工具类 / 业务型 / 资讯类 / 生产力类四维度分类，六指标打分（使用频率、必要性、当前相关性、启用状态、维护状态、独特价值）
- **智能建议**：自动生成保留 / 归档 / 卸载三类建议，含去重、禁用检测、项目结束检测等特殊规则
- **安全清理**：归档操作会先保存技能配置，确认后才执行卸载，不擅自删除

## 目录结构

```
skill-subtraction/
├── SKILL.md                          # 技能主定义（工作流 + 触发规则）
├── LICENSE                           # MIT 协议
├── README.md                         # 中文说明
├── README_en.md                      # English README
├── .gitignore
├── scripts/
│   └── audit_skills.py               # 技能扫描脚本，输出结构化 JSON
└── references/
    └── evaluation_framework.md       # 完整评估框架（分类、评分矩阵、去重规则）
```

## 安装

### 方式一：手动安装

```bash
# 克隆仓库
git clone https://github.com/<your-username>/skill-subtraction.git

# 复制到你使用的 AI 助手平台技能目录
# WorkBuddy
cp -r skill-subtraction ~/.workbuddy/skills/
# Codex
cp -r skill-subtraction ~/.codex/skills/
# Claude Code
cp -r skill-subtraction ~/.claude/skills/
# Cursor / Cline / Continue 等同理
```

### 方式二：直接下载

下载 ZIP 解压后，将 `skill-subtraction` 文件夹放到你所用平台的技能目录下即可（如 `~/.workbuddy/skills/`、`~/.codex/skills/` 等）。

## 使用方法

在你使用的 AI 助手平台对话中直接说：

- "帮我检查一下装了哪些技能"
- "做一次技能减法"
- "哪些技能该删"
- "审计我的技能"

技能会自动触发，执行五步工作流：

1. **扫描** — 运行 `audit_skills.py`，获取所有已安装技能的元数据（含批量安装检测、安装来源统计）
2. **分类** — 按工具类 / 业务型 / 资讯类 / 生产力类 / 平台预装归类，识别安装来源（用户安装 / 平台预装 / Agent 创建）
3. **评估** — 六指标加权打分，综合评分 24-100 分
4. **建议** — 生成保留 / 归档 / 卸载报告
5. **清理** — 用户确认后执行（归档会先保存配置）

### 直接运行扫描脚本

```bash
# 扫描用户级技能（默认中文输出）
python3 scripts/audit_skills.py

# 指定输出语言为英文
python3 scripts/audit_skills.py --lang en

# 指定自定义技能目录（如 Windows LobsterAI 的非标准路径）
python3 scripts/audit_skills.py --skills-dir "C:\Users\admin\AppData\Roaming\LobsterAI\SKILLs"

# 扫描所有已安装的 Agent 平台
python3 scripts/audit_skills.py --all

# 指定工作区扫描项目级技能
python3 scripts/audit_skills.py --workspace /path/to/workspace
```

输出 JSON 示例：

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
      "description": "技能减法 — 已安装技能审计与减法清理...",
      "agent_created": true,
      "file_count": 4,
      "dir_size_kb": 12.5,
      "last_modified": "2026-08-12 10:30:00"
    }
  ]
}
```

## 评估框架

### 评分矩阵

| 综合评分 | 建议 | 说明 |
|---------|------|------|
| 80-100 | 保留 | 高价值技能，深度掌握 |
| 50-79 | 归档 | 价值不确定，保存配置后卸载，需要时重新激活 |
| 24-49 | 卸载 | 低价值，直接清理 |

### 特殊规则（覆盖评分）

1. **零使用 + 不相关 → 直接卸载**
2. **完全重叠 → 保留最优的一个**（去重）
3. **已禁用且从未手动调用 → 卸载**
4. **项目级 + 项目已结束 → 卸载**
5. **数据源失效 → 卸载**

完整评估框架详见 [`references/evaluation_framework.md`](references/evaluation_framework.md)。

## 审计周期建议

| 频率 | 适用场景 |
|------|---------|
| 每季度 | 技能数量超过 10 个时 |
| 每个项目结束时 | 清理项目级技能 |
| 业务方向调整时 | 评估业务型技能的相关性 |
| 感觉"技能太多"时 | 随时触发 |

## 技术要求

- Python 3.10+
- WorkBuddy、Codex、Claude Code、Cursor、Cline、Continue、LobsterAI 等兼容的 AI 助手平台（采用 `~/.<agent>/skills/` 目录约定即可）

## License

[MIT](LICENSE)
