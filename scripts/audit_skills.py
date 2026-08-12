#!/usr/bin/env python3
"""
技能减法 · 技能扫描脚本

自动检测当前脚本所在的 Agent 平台，只扫描该平台下的已安装技能。
无需写死路径——装在 ~/.workbuddy/skills/ 下就扫 workbuddy，
装在 ~/.codex/skills/ 下就扫 codex，以此类推。
也支持非标准路径（如 Windows LobsterAI 的 AppData/Roaming/LobsterAI/SKILLs）。

可靠性设计
----------
所有异常情况都会被收集到 issues 列表，最终输出到 JSON 的 `issues` 字段
并通过 stderr 打印摘要。常见 issue 类型：
  - missing_skill_md        技能目录缺少 SKILL.md
  - unreadable_skill_md     SKILL.md 读取失败（权限/编码）
  - no_frontmatter          SKILL.md 没有 YAML frontmatter
  - malformed_frontmatter   frontmatter 内容解析异常
  - no_name_field           frontmatter 缺少 name 字段（已用目录名兜底）
  - empty_description       frontmatter description 为空
  - permission_denied       目录/文件权限不足
  - not_a_directory         技能目录下一项不是目录
  - broken_symlink          符号链接指向不存在的位置

用法：
    python3 audit_skills.py                                    # 自动检测当前 Agent
    python3 audit_skills.py --agent codex                      # 手动指定 Agent
    python3 audit_skills.py --all                              # 扫描所有已安装的 Agent
    python3 audit_skills.py --skills-dir /custom/skills/path   # 指定自定义技能目录
    python3 audit_skills.py --workspace /path/to/ws            # 同时扫描项目级技能
"""

import json
import os
import sys
import re
import time
from pathlib import Path
from collections import Counter


# ── Windows 编码修复 ──────────────────────────────────────────
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except (AttributeError, Exception):
        # Python < 3.7 没有 reconfigure，用旧方式
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


# ── 已知 Agent 平台（仅用于 --all 全量扫描） ──────────────────
KNOWN_AGENTS = ['workbuddy', 'codex', 'claude', 'cursor', 'cline', 'continue', 'lobsterai']


def add_issue(issues: list, path: str, issue_type: str, message: str, severity: str = 'warning'):
    """向 issues 列表追加一条问题记录。"""
    issues.append({
        'path': path,
        'type': issue_type,
        'severity': severity,
        'message': message
    })


def parse_frontmatter(content: str, issues: list, skill_path: str) -> dict:
    """
    解析 SKILL.md 的 YAML frontmatter，返回字典。

    支持格式：
      - 单行 key: value
      - 字符串值（带引号或不带）
      - 布尔值 true/false
      - 多行折叠字符串（缩进续行）

    异常情况通过 issues 列表上报，不静默失败。
    """
    meta = {}

    # 检测 frontmatter 起始标记 ---
    if not content.startswith('---'):
        add_issue(issues, skill_path, 'no_frontmatter',
                  'SKILL.md 缺少 YAML frontmatter 起始标记 ---')
        return meta

    # 匹配 --- ... --- 块
    match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not match:
        add_issue(issues, skill_path, 'malformed_frontmatter',
                  'frontmatter 格式异常：起始 --- 后未找到结束 ---')
        return meta

    frontmatter = match.group(1)
    lines = frontmatter.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        i += 1

        # 跳过空行和注释
        if not stripped or stripped.startswith('#'):
            continue

        # 缩进行（以空格/tab 开头）是上一行的续行，跳过（已合并到上一 key）
        if line[0:1].isspace() if line else False:
            # 实际的多行值已在 key 解析时合并处理，这里仅跳过
            continue

        # 缺少冒号的行视为格式异常
        if ':' not in stripped:
            add_issue(issues, skill_path, 'malformed_frontmatter',
                      f'frontmatter 第 {i} 行缺少冒号: "{stripped[:60]}"')
            continue

        key, _, value = stripped.partition(':')
        key = key.strip()
        value = value.strip()

        # 合并后续缩进续行（YAML 折叠字符串）
        while i < len(lines):
            next_raw = lines[i]
            if not next_raw.strip():
                # 空行：可能是结尾的换行，不算续行
                # 但要看下一行是否还有缩进续行
                if i + 1 < len(lines) and lines[i + 1] and lines[i + 1][0:1].isspace():
                    # 空行 + 缩进行 = 折叠字符串中的段落分隔
                    value += ' '
                    i += 1
                    continue
                else:
                    break
            if next_raw[0:1].isspace():
                # 续行：去掉前导空格后追加
                value += ' ' + next_raw.strip()
                i += 1
            else:
                break

        # 去引号
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]

        # 布尔值识别
        if value.lower() == 'true':
            value = True
        elif value.lower() == 'false':
            value = False

        meta[key] = value

    return meta


def get_dir_info(path: Path, issues: list) -> dict:
    """获取目录的文件数和大小，权限错误时记录 issue。"""
    file_count = 0
    total_size = 0
    error_count = 0

    for root, dirs, files in os.walk(path, onerror=lambda e: add_issue(
            issues, str(e.filename or path), 'permission_denied',
            f'遍历目录失败: {e.strerror}', 'error')):
        for f in files:
            file_path = os.path.join(root, f)
            try:
                total_size += os.path.getsize(file_path)
                file_count += 1
            except OSError as e:
                error_count += 1
                add_issue(issues, file_path, 'permission_denied',
                          f'读取文件信息失败: {e.strerror}')

    return {
        'file_count': file_count,
        'dir_size_kb': round(total_size / 1024, 1),
        'file_access_errors': error_count
    }


def get_latest_mtime(path: Path, issues: list) -> str:
    """获取目录中最近修改的文件时间，权限错误时记录 issue。"""
    latest = 0
    error_count = 0

    for root, dirs, files in os.walk(path, onerror=lambda e: add_issue(
            issues, str(e.filename or path), 'permission_denied',
            f'遍历目录失败: {e.strerror}', 'error')):
        for f in files:
            file_path = os.path.join(root, f)
            try:
                mtime = os.path.getmtime(file_path)
                if mtime > latest:
                    latest = mtime
            except OSError as e:
                error_count += 1
                add_issue(issues, file_path, 'permission_denied',
                          f'读取文件修改时间失败: {e.strerror}')

    if latest == 0:
        return 'unknown'
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(latest))


def detect_current_agent() -> tuple[str, Path] | None:
    """
    通过脚本自身路径反推当前 Agent。

    标准路径结构: ~/.<agent>/skills/<skill-name>/scripts/audit_skills.py
    Windows 非标准: C:\\Users\\<user>\\AppData\\Roaming\\<Agent>\\SKILLs\\<skill-name>\\scripts\\audit_skills.py

    两种情况下 parents[2] 都是 skills 目录，parents[3] 是 agent 目录。
    """
    # __file__ 在某些 exec() 场景下未定义，用 sys.argv[0] 兜底
    try:
        script_path = Path(__file__).resolve()
    except NameError:
        if sys.argv and sys.argv[0]:
            script_path = Path(sys.argv[0]).resolve()
        else:
            return None

    # scripts/audit_skills.py → skill-dir/ → skills/ (or SKILLs/)
    # parents[0] = scripts/, parents[1] = skill-dir/, parents[2] = skills dir
    if len(script_path.parents) < 4:
        return None

    skills_dir = script_path.parents[2]
    agent_dir = script_path.parents[3]
    agent_name = agent_dir.name

    # 去掉前导点：.workbuddy → workbuddy
    if agent_name.startswith('.'):
        agent_name = agent_name[1:]

    # 统一小写：LobsterAI → lobsterai
    agent_name = agent_name.lower()

    if skills_dir.exists():
        return agent_name, skills_dir
    return None


def scan_skill_dir(skill_path: Path, agent: str, scope: str, issues: list) -> dict | None:
    """
    扫描单个技能目录，返回技能信息字典。
    所有失败都通过 issues 列表上报，绝不静默跳过。
    """
    skill_md = skill_path / 'SKILL.md'

    # 区分"不存在"和"存在但读不了"
    if not skill_md.exists():
        add_issue(issues, str(skill_path), 'missing_skill_md',
                  f'技能目录缺少 SKILL.md 文件', 'error')
        return None

    # 尝试读取，区分具体异常类型
    try:
        content = skill_md.read_text(encoding='utf-8')
    except PermissionError as e:
        add_issue(issues, str(skill_md), 'permission_denied',
                  f'无法读取 SKILL.md: {e.strerror}', 'error')
        return None
    except UnicodeDecodeError as e:
        add_issue(issues, str(skill_md), 'unreadable_skill_md',
                  f'SKILL.md 编码异常（非 UTF-8）: {e}', 'error')
        return None
    except Exception as e:
        add_issue(issues, str(skill_md), 'unreadable_skill_md',
                  f'读取 SKILL.md 失败: {type(e).__name__}: {e}', 'error')
        return None

    # 解析 frontmatter（异常会写入 issues）
    meta = parse_frontmatter(content, issues, str(skill_path))

    # 检测关键字段缺失
    if 'name' not in meta:
        add_issue(issues, str(skill_path), 'no_name_field',
                  'frontmatter 缺少 name 字段，已使用目录名兜底', 'warning')

    if not meta.get('description', '').strip():
        add_issue(issues, str(skill_path), 'empty_description',
                  'frontmatter description 字段为空，技能描述将不完整', 'warning')

    # 获取目录信息（权限错误会写入 issues）
    dir_info = get_dir_info(skill_path, issues)
    latest_mtime = get_latest_mtime(skill_path, issues)

    has_scripts = (skill_path / 'scripts').is_dir()
    has_references = (skill_path / 'references').is_dir()
    has_assets = (skill_path / 'assets').is_dir()

    description = meta.get('description', '')
    summary = description[:200] + '...' if len(description) > 200 else description

    return {
        'name': meta.get('name', skill_path.name),
        'agent': agent,
        'scope': scope,
        'path': str(skill_path),
        'description': summary,
        'agent_created': bool(meta.get('agent_created', False)),
        'disable_model_invocation': bool(meta.get('disable-model-invocation', False)),
        'has_scripts': has_scripts,
        'has_references': has_references,
        'has_assets': has_assets,
        'file_count': dir_info['file_count'],
        'dir_size_kb': dir_info['dir_size_kb'],
        'last_modified': latest_mtime,
        'version': str(meta.get('version', 'unknown'))
    }


def scan_skills_dir(skills_dir: Path, agent: str, scope: str, issues: list) -> list[dict]:
    """
    扫描指定 skills 目录下的所有技能。
    目录权限不足或子项异常都会通过 issues 上报。
    """
    if not skills_dir.exists():
        return []

    # 目录存在但无法访问的情况
    try:
        entries = list(skills_dir.iterdir())
    except PermissionError as e:
        add_issue(issues, str(skills_dir), 'permission_denied',
                  f'无法列出 skills 目录内容: {e.strerror}', 'error')
        return []

    results = []
    for entry in sorted(entries):
        # 隐藏目录和文件默认跳过（不记录为 issue，因为是设计意图）
        if entry.name.startswith('.') or entry.name.startswith('_'):
            continue

        # 符号链接检查
        if entry.is_symlink() and not entry.exists():
            add_issue(issues, str(entry), 'broken_symlink',
                      f'符号链接指向不存在的位置', 'error')
            continue

        # 非目录项（普通文件等）单独处理
        if not entry.is_dir():
            add_issue(issues, str(entry), 'not_a_directory',
                      f'技能目录下的 {entry.name} 不是目录，已跳过', 'warning')
            continue

        info = scan_skill_dir(entry, agent, scope, issues)
        if info:
            results.append(info)

    return results


def detect_all_agents() -> list[tuple[str, Path]]:
    """检测机器上所有已安装的 Agent 平台。"""
    found = []
    # Unix/Mac: ~/.<agent>/skills/
    for name in KNOWN_AGENTS:
        skills_dir = Path.home() / f'.{name}' / 'skills'
        if skills_dir.exists():
            found.append((name, skills_dir))

    # Windows: AppData/Roaming/<Agent>/SKILLs/ 或 AppData/Roaming/<Agent>/skills/
    if sys.platform == 'win32':
        appdata = os.environ.get('APPDATA')
        if appdata:
            for name in KNOWN_AGENTS:
                for skills_subdir in ['SKILLs', 'skills']:
                    skills_dir = Path(appdata) / name / skills_subdir
                    # 避免重复
                    if skills_dir.exists() and not any(str(sd) == str(skills_dir) for _, sd in found):
                        found.append((name, skills_dir))

    return found


def print_usage():
    print(__doc__)


def print_issue_summary(issues: list, total_skills: int):
    """通过 stderr 打印问题摘要，让用户立刻知道扫描是否完整。"""
    if not issues:
        print(f"[OK] 扫描完成：发现 {total_skills} 个技能，无任何问题", file=sys.stderr)
        return

    # 按类型分组统计
    by_type: dict[str, int] = {}
    by_severity: dict[str, int] = {'error': 0, 'warning': 0}
    for issue in issues:
        by_type[issue['type']] = by_type.get(issue['type'], 0) + 1
        by_severity[issue['severity']] = by_severity.get(issue['severity'], 0) + 1

    print(f"[WARN] 扫描完成但发现 {len(issues)} 个问题（{total_skills} 个技能）", file=sys.stderr)
    print(f"  - 错误: {by_severity.get('error', 0)} 个（可能导致技能被跳过）", file=sys.stderr)
    print(f"  - 警告: {by_severity.get('warning', 0)} 个（信息不完整但仍可处理）", file=sys.stderr)
    print(f"  问题类型分布:", file=sys.stderr)
    for issue_type, count in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"    {issue_type}: {count}", file=sys.stderr)


def detect_batch_installs(skills: list[dict]) -> list[dict]:
    """
    检测批量安装的技能组。
    当多个技能共享相同创建日期（±1天内）且数量 ≥ 5 个时，标记为批量安装。
    """
    # 按日期分组（只取日期部分，不含时间）
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

    # 按数量降序
    batches.sort(key=lambda x: -x['count'])
    return batches


def main():
    # ── 解析参数 ──
    agent_override = None
    workspace = None
    scan_all = False
    skills_dir_override = None

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == '--agent' and i + 1 < len(args):
            agent_override = args[i + 1].strip()
            i += 2
        elif args[i] == '--workspace' and i + 1 < len(args):
            workspace = args[i + 1]
            i += 2
        elif args[i] == '--skills-dir' and i + 1 < len(args):
            skills_dir_override = args[i + 1]
            i += 2
        elif args[i] == '--all':
            scan_all = True
            i += 1
        elif args[i] in ('-h', '--help'):
            print_usage()
            return
        else:
            i += 1

    # ── 收集所有问题 ──
    issues: list[dict] = []
    skills: list[dict] = []
    agents_scanned: list[dict] = []

    # ── 确定扫描目标 ──
    if skills_dir_override:
        # 自定义技能目录（如 LobsterAI 的非标准路径）
        skills_dir = Path(skills_dir_override)
        if not skills_dir.exists():
            print(f"Error: skills directory not found: {skills_dir}", file=sys.stderr)
            sys.exit(1)
        # 尝试从路径推断 agent 名称
        agent_name = skills_dir.parent.name.lower()
        if agent_name.startswith('.'):
            agent_name = agent_name[1:]
        agent_skills = scan_skills_dir(skills_dir, agent_name, 'user', issues)
        skills.extend(agent_skills)
        agents_scanned.append({
            'agent': agent_name,
            'path': str(skills_dir),
            'skill_count': len(agent_skills)
        })
    elif scan_all:
        for agent_name, skills_dir in detect_all_agents():
            agent_skills = scan_skills_dir(skills_dir, agent_name, 'user', issues)
            skills.extend(agent_skills)
            agents_scanned.append({
                'agent': agent_name,
                'path': str(skills_dir),
                'skill_count': len(agent_skills)
            })
    elif agent_override:
        # 先尝试 Unix 路径，再尝试 Windows AppData
        skills_dir = Path.home() / f'.{agent_override}' / 'skills'
        if not skills_dir.exists() and sys.platform == 'win32':
            appdata = os.environ.get('APPDATA', '')
            for subdir in ['SKILLs', 'skills']:
                alt_dir = Path(appdata) / agent_override / subdir
                if alt_dir.exists():
                    skills_dir = alt_dir
                    break
        if not skills_dir.exists():
            print(f"Error: skills directory not found for agent '{agent_override}'", file=sys.stderr)
            print(f"  Tried: {skills_dir}", file=sys.stderr)
            if sys.platform == 'win32':
                print(f"  Also tried: {Path(os.environ.get('APPDATA', '')) / agent_override / 'SKILLs'}", file=sys.stderr)
            print(f"Use --skills-dir <path> to specify a custom path.", file=sys.stderr)
            sys.exit(1)
        agent_skills = scan_skills_dir(skills_dir, agent_override, 'user', issues)
        skills.extend(agent_skills)
        agents_scanned.append({
            'agent': agent_override,
            'path': str(skills_dir),
            'skill_count': len(agent_skills)
        })
    else:
        detected = detect_current_agent()
        if not detected:
            print("Error: cannot determine current agent from script path.", file=sys.stderr)
            print("Use --agent <name>, --skills-dir <path>, or --all to specify manually.", file=sys.stderr)
            sys.exit(1)

        agent_name, skills_dir = detected
        agent_skills = scan_skills_dir(skills_dir, agent_name, 'user', issues)
        skills.extend(agent_skills)
        agents_scanned.append({
            'agent': agent_name,
            'path': str(skills_dir),
            'skill_count': len(agent_skills)
        })

    # 扫描项目级技能
    if workspace:
        project_dir = Path(workspace) / '.workbuddy' / 'skills'
        project_agent = agents_scanned[0]['agent'] if agents_scanned else 'workbuddy'
        project_skills = scan_skills_dir(project_dir, project_agent, 'project', issues)
        skills.extend(project_skills)

    # ── 批量安装检测 ──
    batch_installs = detect_batch_installs(skills)

    # ── 安装来源统计 ──
    source_stats = {
        'agent_created': sum(1 for s in skills if s.get('agent_created')),
        'not_agent_created': sum(1 for s in skills if not s.get('agent_created')),
        'disabled': sum(1 for s in skills if s.get('disable_model_invocation')),
        'batch_detected': sum(b['count'] for b in batch_installs),
    }

    # ── 输出 JSON ──
    output = {
        'audit_time': time.strftime('%Y-%m-%d %H:%M:%S'),
        'total_skills': len(skills),
        'agents_scanned': agents_scanned,
        'user_skills': sum(1 for s in skills if s['scope'] == 'user'),
        'project_skills': sum(1 for s in skills if s['scope'] == 'project'),
        'source_stats': source_stats,
        'batch_installs': batch_installs,
        'issue_summary': {
            'total': len(issues),
            'errors': sum(1 for i in issues if i['severity'] == 'error'),
            'warnings': sum(1 for i in issues if i['severity'] == 'warning'),
            'by_type': {}
        },
        'issues': issues,
        'skills': skills
    }

    # 填充 by_type 统计
    for issue in issues:
        t = issue['type']
        output['issue_summary']['by_type'][t] = \
            output['issue_summary']['by_type'].get(t, 0) + 1

    print(json.dumps(output, ensure_ascii=False, indent=2))

    # stderr 打印摘要，让用户立刻看到是否有问题
    print_issue_summary(issues, len(skills))

    # 批量安装提示
    if batch_installs:
        print(f"\n[INFO] 检测到 {len(batch_installs)} 批批量安装：", file=sys.stderr)
        for b in batch_installs:
            print(f"  - {b['date']}: {b['count']} 个技能（建议按业务方向整批评估）", file=sys.stderr)

    # 有错误时退出码非零，方便 CI 接入
    if any(i['severity'] == 'error' for i in issues):
        sys.exit(2)


if __name__ == '__main__':
    main()