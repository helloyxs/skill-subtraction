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

- **自动扫描**：一键扫描 `~/.workbuddy/skills/` 和当前工作区 `.workbuddy/skills/` 下的所有已安装技能
- **分类评估**：按工具类 / 业务型 / 资讯类 / 生产力类四维度分类，五指标打分（使用频率、必要性、当前相关性、维护状态、独特价值）
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

# 复制到 WorkBuddy 技能目录
cp -r skill-subtraction ~/.workbuddy/skills/
```

### 方式二：直接下载

下载 ZIP 解压后，将 `skill-subtraction` 文件夹放到 `~/.workbuddy/skills/` 下即可。

## 使用方法

在 WorkBuddy 对话中直接说：

- "帮我检查一下装了哪些技能"
- "做一次技能减法"
- "哪些技能该删"
- "审计我的技能"

技能会自动触发，执行五步工作流：

1. **扫描** — 运行 `audit_skills.py`，获取所有已安装技能的元数据
2. **分类** — 按工具类 / 业务型 / 资讯类 / 生产力类归类
3. **评估** — 五指标打分，综合评分 5-16 分
4. **建议** — 生成保留 / 归档 / 卸载报告
5. **清理** — 用户确认后执行（归档会先保存配置）

### 直接运行扫描脚本

```bash
# 扫描用户级技能
python3 scripts/audit_skills.py

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
| 13-16 | 保留 | 高价值技能，深度掌握 |
| 9-12 | 归档 | 价值不确定，保存配置后卸载，需要时重新激活 |
| 5-8 | 卸载 | 低价值，直接清理 |

### 特殊规则（覆盖评分）

1. **零使用 + 不相关 → 直接卸载**
2. **完全重叠 → 保留最优的一个**（去重）
3. **已禁用 + 90 天未使用 → 卸载**
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
- WorkBuddy（或兼容的 AI 助手平台）

## License

[MIT](LICENSE)
