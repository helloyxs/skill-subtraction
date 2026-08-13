#!/usr/bin/env python3
"""
技能减法 · 技能扫描脚本 / Skill Subtraction · Skill Audit Script

自动检测当前脚本所在的 Agent 平台，只扫描该平台下的已安装技能。
Auto-detects the current Agent platform and scans installed skills only.

语言支持 / Language Support:
  --lang zh  (默认) 中文输出
  --lang en  English output

可靠性设计 / Reliability Design
----------
所有异常情况都会被收集到 issues 列表，最终输出到 JSON 的 `issues` 字段
并通过 stderr 打印摘要。常见 issue 类型：
  - missing_skill_md        技能目录缺少 SKILL.md / Skill dir missing SKILL.md
  - unreadable_skill_md     SKILL.md 读取失败（权限/编码）/ Read failure
  - no_frontmatter          SKILL.md 没有 YAML frontmatter / No frontmatter
  - malformed_frontmatter   frontmatter 内容解析异常 / Malformed frontmatter
  - no_name_field           frontmatter 缺少 name 字段 / Missing name field
  - empty_description       frontmatter description 为空 / Empty description
  - permission_denied       目录/文件权限不足 / Permission denied
  - not_a_directory         技能目录下一项不是目录 / Not a directory
  - broken_symlink          符号链接指向不存在的位置 / Broken symlink

用法 / Usage:
    python3 audit_skills.py                                    # 自动检测当前 Agent / Auto-detect
    python3 audit_skills.py --lang en                         # English output
    python3 audit_skills.py --agent codex                      # 手动指定 Agent / Specify agent
    python3 audit_skills.py --all                              # 扫描所有已安装的 Agent / Scan all
    python3 audit_skills.py --skills-dir /custom/skills/path   # 自定义技能目录 / Custom dir
    python3 audit_skills.py --workspace /path/to/ws            # 同时扫描项目级技能 / Include project skills
"""

import json
import os
import sys
import re
import time
from pathlib import Path
from collections import Counter


# ── Windows 编码修复 / Windows encoding fix ──────────────────
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except (AttributeError, Exception):
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


# ── 已知 Agent 平台 / Known agent platforms ──────────────────
KNOWN_AGENTS = ['workbuddy', 'codex', 'claude', 'cursor', 'cline', 'continue', 'lobsterai']

# ── 语言设置 / Language setting ──────────────────────────────
LANG = 'zh'  # default Chinese; set to 'en' via --lang en


def L(zh: str, en: str) -> str:
    """根据当前语言返回对应文本 / Return text in current language."""
    return en if LANG == 'en' else zh


def add_issue(issues: list, path: str, issue_type: str, message: str, severity: str = 'warning'):
    """向 issues 列表追加一条问题记录 / Append an issue record."""
    issues.append({
        'path': path,
        'type': issue_type,
        'severity': severity,
        'message': message
    })


def parse_frontmatter(content: str, issues: list, skill_path: str) -> dict:
    """
    解析 SKILL.md 的 YAML frontmatter，返回字典。
    Parse YAML frontmatter from SKILL.md, return a dict.

    支持格式 / Supported formats:
      - 单行 key: value / Single-line key: value
      - 字符串值（带引号或不带）/ String values (quoted or not)
      - 布尔值 true/false / Boolean true/false
      - 多行折叠字符串（缩进续行）/ Multi-line folded strings

    异常情况通过 issues 列表上报，不静默失败。
    Exceptions are reported via issues list, never silently skipped.
    """
    meta = {}

    if not content.startswith('---'):
        add_issue(issues, skill_path, 'no_frontmatter',
                  L('SKILL.md 缺少 YAML frontmatter 起始标记 ---',
                    'SKILL.md missing YAML frontmatter start marker ---'))
        return meta

    match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not match:
        add_issue(issues, skill_path, 'malformed_frontmatter',
                  L('frontmatter 格式异常：起始 --- 后未找到结束 ---',
                    'Malformed frontmatter: no closing --- found after opening ---'))
        return meta

    frontmatter = match.group(1)
    lines = frontmatter.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        i += 1

        if not stripped or stripped.startswith('#'):
            continue

        if line[0:1].isspace() if line else False:
            continue

        if ':' not in stripped:
            add_issue(issues, skill_path, 'malformed_frontmatter',
                      L(f'frontmatter 第 {i} 行缺少冒号: "{stripped[:60]}"',
                        f'Frontmatter line {i} missing colon: "{stripped[:60]}"'))
            continue

        key, _, value = stripped.partition(':')
        key = key.strip()
        value = value.strip()

        while i < len(lines):
            next_raw = lines[i]
            if not next_raw.strip():
                if i + 1 < len(lines) and lines[i + 1] and lines[i + 1][0:1].isspace():
                    value += ' '
                    i += 1
                    continue
                else:
                    break
            if next_raw[0:1].isspace():
                value += ' ' + next_raw.strip()
                i += 1
            else:
                break

        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]

        if value.lower() == 'true':
            value = True
        elif value.lower() == 'false':
            value = False

        meta[key] = value

    return meta


def get_dir_info(path: Path, issues: list) -> dict:
    """获取目录的文件数和大小 / Get file count and size; record issues on permission errors."""
    file_count = 0
    total_size = 0
    error_count = 0

    for root, dirs, files in os.walk(path, onerror=lambda e: add_issue(
            issues, str(e.filename or path), 'permission_denied',
            L(f'遍历目录失败: {e.strerror}', f'Directory walk failed: {e.strerror}'), 'error')):
        for f in files:
            file_path = os.path.join(root, f)
            try:
                total_size += os.path.getsize(file_path)
                file_count += 1
            except OSError as e:
                error_count += 1
                add_issue(issues, file_path, 'permission_denied',
                          L(f'读取文件信息失败: {e.strerror}',
                            f'Failed to read file info: {e.strerror}'))

    return {
        'file_count': file_count,
        'dir_size_kb': round(total_size / 1024, 1),
        'file_access_errors': error_count
    }


def get_latest_mtime(path: Path, issues: list) -> str:
    """获取目录中最近修改的文件时间 / Get latest file modification time in directory."""
    latest = 0
    error_count = 0

    for root, dirs, files in os.walk(path, onerror=lambda e: add_issue(
            issues, str(e.filename or path), 'permission_denied',
            L(f'遍历目录失败: {e.strerror}', f'Directory walk failed: {e.strerror}'), 'error')):
        for f in files:
            file_path = os.path.join(root, f)
            try:
                mtime = os.path.getmtime(file_path)
                if mtime > latest:
                    latest = mtime
            except OSError as e:
                error_count += 1
                add_issue(issues, file_path, 'permission_denied',
                          L(f'读取文件修改时间失败: {e.strerror}',
                            f'Failed to read file mtime: {e.strerror}'))

    if latest == 0:
        return 'unknown'
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(latest))


def detect_current_agent() -> tuple[str, Path] | None:
    """
    通过脚本自身路径反推当前 Agent。
    Detect current Agent from the script's own path.

    标准路径结构 / Standard path:
      ~/.<agent>/skills/<skill-name>/scripts/audit_skills.py
    Windows 非标准 / Windows non-standard:
      C:\\Users\\<user>\\AppData\\Roaming\\<Agent>\\SKILLs\\<skill-name>\\scripts\\audit_skills.py
    """
    try:
        script_path = Path(__file__).resolve()
    except NameError:
        if sys.argv and sys.argv[0]:
            script_path = Path(sys.argv[0]).resolve()
        else:
            return None

    if len(script_path.parents) < 4:
        return None

    skills_dir = script_path.parents[2]
    agent_dir = script_path.parents[3]
    agent_name = agent_dir.name

    if agent_name.startswith('.'):
        agent_name = agent_name[1:]

    agent_name = agent_name.lower()

    if skills_dir.exists():
        return agent_name, skills_dir
    return None


def scan_skill_dir(skill_path: Path, agent: str, scope: str, issues: list) -> dict | None:
    """
    扫描单个技能目录，返回技能信息字典。
    Scan a single skill directory, return skill info dict.
    """
    skill_md = skill_path / 'SKILL.md'

    if not skill_md.exists():
        add_issue(issues, str(skill_path), 'missing_skill_md',
                  L('技能目录缺少 SKILL.md 文件', 'Skill directory missing SKILL.md file'), 'error')
        return None

    try:
        content = skill_md.read_text(encoding='utf-8')
    except PermissionError as e:
        add_issue(issues, str(skill_md), 'permission_denied',
                  L(f'无法读取 SKILL.md: {e.strerror}', f'Cannot read SKILL.md: {e.strerror}'), 'error')
        return None
    except UnicodeDecodeError as e:
        add_issue(issues, str(skill_md), 'unreadable_skill_md',
                  L(f'SKILL.md 编码异常（非 UTF-8）: {e}', f'SKILL.md encoding error (non-UTF-8): {e}'), 'error')
        return None
    except Exception as e:
        add_issue(issues, str(skill_md), 'unreadable_skill_md',
                  L(f'读取 SKILL.md 失败: {type(e).__name__}: {e}',
                    f'Failed to read SKILL.md: {type(e).__name__}: {e}'), 'error')
        return None

    meta = parse_frontmatter(content, issues, str(skill_path))

    if 'name' not in meta:
        add_issue(issues, str(skill_path), 'no_name_field',
                  L('frontmatter 缺少 name 字段，已使用目录名兜底',
                    'Frontmatter missing name field, fell back to directory name'), 'warning')

    if not meta.get('description', '').strip():
        add_issue(issues, str(skill_path), 'empty_description',
                  L('frontmatter description 字段为空，技能描述将不完整',
                    'Frontmatter description is empty, skill description will be incomplete'), 'warning')

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
    Scan all skills under the given directory.
    """
    if not skills_dir.exists():
        return []

    try:
        entries = list(skills_dir.iterdir())
    except PermissionError as e:
        add_issue(issues, str(skills_dir), 'permission_denied',
                  L(f'无法列出 skills 目录内容: {e.strerror}',
                    f'Cannot list skills directory contents: {e.strerror}'), 'error')
        return []

    results = []
    for entry in sorted(entries):
        if entry.name.startswith('.') or entry.name.startswith('_'):
            continue

        if entry.is_symlink() and not entry.exists():
            add_issue(issues, str(entry), 'broken_symlink',
                      L('符号链接指向不存在的位置', 'Symlink points to non-existent target'), 'error')
            continue

        if not entry.is_dir():
            add_issue(issues, str(entry), 'not_a_directory',
                      L(f'技能目录下的 {entry.name} 不是目录，已跳过',
                        f'{entry.name} in skills dir is not a directory, skipped'), 'warning')
            continue

        # 命名空间目录（如 @user_xxx、learned）：没有 SKILL.md 但含子目录时
        # 递归扫描其中的真实技能，避免误报 missing_skill_md 并漏报内部技能。
        # Namespace dirs (e.g. @user_xxx): no SKILL.md but contain subdirs --
        # recurse to find real skills inside instead of flagging the dir.
        if not (entry / 'SKILL.md').exists():
            try:
                has_subdirs = any(
                    p.is_dir() and not p.name.startswith('.')
                    for p in entry.iterdir()
                )
            except (PermissionError, OSError):
                has_subdirs = False
            if has_subdirs:
                results.extend(scan_skills_dir(entry, agent, scope, issues))
                continue

        info = scan_skill_dir(entry, agent, scope, issues)
        if info:
            results.append(info)

    return results


def detect_all_agents() -> list[tuple[str, Path]]:
    """检测机器上所有已安装的 Agent 平台 / Detect all installed Agent platforms."""
    found = []
    for name in KNOWN_AGENTS:
        skills_dir = Path.home() / f'.{name}' / 'skills'
        if skills_dir.exists():
            found.append((name, skills_dir))

    if sys.platform == 'win32':
        appdata = os.environ.get('APPDATA')
        if appdata:
            for name in KNOWN_AGENTS:
                for skills_subdir in ['SKILLs', 'skills']:
                    skills_dir = Path(appdata) / name / skills_subdir
                    if skills_dir.exists() and not any(str(sd) == str(skills_dir) for _, sd in found):
                        found.append((name, skills_dir))

    return found


def print_usage():
    print(__doc__)


def print_issue_summary(issues: list, total_skills: int):
    """通过 stderr 打印问题摘要 / Print issue summary to stderr."""
    if not issues:
        print(L(f'[OK] 扫描完成：发现 {total_skills} 个技能，无任何问题',
                f'[OK] Scan complete: {total_skills} skills found, no issues'), file=sys.stderr)
        return

    by_type: dict[str, int] = {}
    by_severity: dict[str, int] = {'error': 0, 'warning': 0}
    for issue in issues:
        by_type[issue['type']] = by_type.get(issue['type'], 0) + 1
        by_severity[issue['severity']] = by_severity.get(issue['severity'], 0) + 1

    print(L(f'[WARN] 扫描完成但发现 {len(issues)} 个问题（{total_skills} 个技能）',
            f'[WARN] Scan complete but found {len(issues)} issues ({total_skills} skills)'), file=sys.stderr)
    print(L(f'  - 错误: {by_severity.get("error", 0)} 个（可能导致技能被跳过）',
            f'  - Errors: {by_severity.get("error", 0)} (may cause skills to be skipped)'), file=sys.stderr)
    print(L(f'  - 警告: {by_severity.get("warning", 0)} 个（信息不完整但仍可处理）',
            f'  - Warnings: {by_severity.get("warning", 0)} (incomplete info but processable)'), file=sys.stderr)
    print(L('  问题类型分布:', '  Issue type distribution:'), file=sys.stderr)
    for issue_type, count in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f'    {issue_type}: {count}', file=sys.stderr)


def detect_batch_installs(skills: list[dict]) -> list[dict]:
    """
    检测批量安装的技能组。
    Detect batch-installed skill groups.

    当多个技能共享相同创建日期（±1天内）且数量 ≥ 5 个时，标记为批量安装。
    When ≥5 skills share the same creation date (±1 day), flagged as batch install.
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


def main():
    global LANG

    # ── 解析参数 / Parse args ──
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
        elif args[i] == '--lang' and i + 1 < len(args):
            lang_val = args[i + 1].strip().lower()
            if lang_val in ('zh', 'en'):
                LANG = lang_val
            i += 2
        elif args[i] == '--all':
            scan_all = True
            i += 1
        elif args[i] in ('-h', '--help'):
            print_usage()
            return
        else:
            i += 1

    # ── 收集所有问题 / Collect all issues ──
    issues: list[dict] = []
    skills: list[dict] = []
    agents_scanned: list[dict] = []

    # ── 确定扫描目标 / Determine scan target ──
    if skills_dir_override:
        skills_dir = Path(skills_dir_override)
        if not skills_dir.exists():
            print(L(f'错误: 技能目录不存在: {skills_dir}',
                    f'Error: skills directory not found: {skills_dir}'), file=sys.stderr)
            sys.exit(1)
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
        skills_dir = Path.home() / f'.{agent_override}' / 'skills'
        if not skills_dir.exists() and sys.platform == 'win32':
            appdata = os.environ.get('APPDATA', '')
            for subdir in ['SKILLs', 'skills']:
                alt_dir = Path(appdata) / agent_override / subdir
                if alt_dir.exists():
                    skills_dir = alt_dir
                    break
        if not skills_dir.exists():
            print(L(f"错误: 未找到 Agent '{agent_override}' 的技能目录",
                    f"Error: skills directory not found for agent '{agent_override}'"), file=sys.stderr)
            print(f"  {skills_dir}", file=sys.stderr)
            if sys.platform == 'win32':
                print(f"  {Path(os.environ.get('APPDATA', '')) / agent_override / 'SKILLs'}", file=sys.stderr)
            print(L('使用 --skills-dir <path> 指定自定义路径。',
                    'Use --skills-dir <path> to specify a custom path.'), file=sys.stderr)
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
        if detected:
            agent_name, skills_dir = detected
            # 校验是否为标准技能目录；开发模式下脚本躺在仓库里，反推的
            # parents[2] 是项目根而非技能根，此时回退到全平台扫描。
            # Verify this is a standard skills dir; in dev mode the script
            # lives in a repo, so parents[2] is a project root, not a skills
            # root -- fall back to scanning all installed agents.
            is_standard = skills_dir == Path.home() / f'.{agent_name}' / 'skills'
            if not is_standard and sys.platform == 'win32':
                appdata = os.environ.get('APPDATA', '')
                is_standard = any(
                    skills_dir == Path(appdata) / agent_name / subdir
                    for subdir in ['SKILLs', 'skills']
                )
            if not is_standard:
                print(L('提示: 脚本路径不是标准技能目录（疑似开发模式），'
                        '已回退到全平台已安装技能扫描。',
                        'Note: script path is not a standard skills dir (dev mode?). '
                        'Falling back to scanning all installed agents.'), file=sys.stderr)
                detected = None

        if detected:
            agent_name, skills_dir = detected
            agent_skills = scan_skills_dir(skills_dir, agent_name, 'user', issues)
            skills.extend(agent_skills)
            agents_scanned.append({
                'agent': agent_name,
                'path': str(skills_dir),
                'skill_count': len(agent_skills)
            })
        else:
            all_agents = detect_all_agents()
            if not all_agents:
                print(L('错误: 无法确定技能目录。',
                        'Error: cannot determine a skills directory.'), file=sys.stderr)
                print(L('使用 --skills-dir <path> 指定自定义路径。',
                        'Use --skills-dir <path> to specify a custom path.'), file=sys.stderr)
                sys.exit(1)
            for agent_name, skills_dir in all_agents:
                agent_skills = scan_skills_dir(skills_dir, agent_name, 'user', issues)
                skills.extend(agent_skills)
                agents_scanned.append({
                    'agent': agent_name,
                    'path': str(skills_dir),
                    'skill_count': len(agent_skills)
                })

    # 扫描项目级技能 / Scan project-level skills
    if workspace:
        project_dir = Path(workspace) / '.workbuddy' / 'skills'
        project_agent = agents_scanned[0]['agent'] if agents_scanned else 'workbuddy'
        project_skills = scan_skills_dir(project_dir, project_agent, 'project', issues)
        skills.extend(project_skills)

    # ── 批量安装检测 / Batch install detection ──
    batch_installs = detect_batch_installs(skills)

    # ── 安装来源统计 / Source stats ──
    source_stats = {
        'agent_created': sum(1 for s in skills if s.get('agent_created')),
        'not_agent_created': sum(1 for s in skills if not s.get('agent_created')),
        'disabled': sum(1 for s in skills if s.get('disable_model_invocation')),
        'batch_detected': sum(b['count'] for b in batch_installs),
    }

    # ── 输出 JSON / Output JSON ──
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

    for issue in issues:
        t = issue['type']
        output['issue_summary']['by_type'][t] = \
            output['issue_summary']['by_type'].get(t, 0) + 1

    print(json.dumps(output, ensure_ascii=False, indent=2))

    # stderr 打印摘要 / Print summary to stderr
    print_issue_summary(issues, len(skills))

    # 批量安装提示 / Batch install notice
    if batch_installs:
        print(L(f'\n[INFO] 检测到 {len(batch_installs)} 批批量安装：',
                f'\n[INFO] Detected {len(batch_installs)} batch install(s):'), file=sys.stderr)
        for b in batch_installs:
            print(L(f"  - {b['date']}: {b['count']} 个技能（建议按业务方向整批评估）",
                    f"  - {b['date']}: {b['count']} skills (recommend batch evaluation by business direction)"),
                  file=sys.stderr)

    # 有错误时退出码非零 / Non-zero exit on errors (for CI)
    if any(i['severity'] == 'error' for i in issues):
        sys.exit(2)


if __name__ == '__main__':
    main()
