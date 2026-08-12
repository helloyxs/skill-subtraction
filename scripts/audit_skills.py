#!/usr/bin/env python3
"""
技能减法 · 技能扫描脚本

自动检测当前脚本所在的 Agent 平台，只扫描该平台下的已安装技能。
无需写死路径——装在 ~/.workbuddy/skills/ 下就扫 workbuddy，
装在 ~/.codex/skills/ 下就扫 codex，以此类推。

用法：
    python3 audit_skills.py                          # 自动检测当前 Agent，扫描同级技能
    python3 audit_skills.py --workspace /path/to/ws  # 同时扫描项目级技能
    python3 audit_skills.py --agent codex            # 手动指定 Agent（覆盖自动检测）
    python3 audit_skills.py --all                    # 扫描所有已检测到的 Agent
"""

import json
import os
import time
from pathlib import Path


# ── 已知 Agent 平台（仅用于 --all 全量扫描） ──────────────────
KNOWN_AGENTS = ['workbuddy', 'codex', 'claude', 'cursor', 'cline', 'continue']


def parse_frontmatter(content: str) -> dict:
    """解析 SKILL.md 的 YAML frontmatter，返回字典。"""
    meta = {}
    match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return meta

    frontmatter = match.group(1)
    for line in frontmatter.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if ':' in line:
            key, _, value = line.partition(':')
            key = key.strip()
            value = value.strip()
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            if value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False
            except OSError:
                pass
    if latest == 0:
        return 'unknown'
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(latest))


def detect_current_agent() -> tuple[str, Path] | None:
    """
    通过脚本自身路径反推当前 Agent。

    脚本路径结构: ~/.<agent>/skills/<skill-name>/scripts/audit_skills.py
    向上回溯 3 级到达 skills/ 目录，再上一级是 ~/.<agent>/，
    目录名去掉前导点即为 agent 名称。
    """
    script_path = Path(__file__).resolve()
    # scripts/audit_skills.py → scripts/ → skill-dir/ → skills/ → ~/.<agent>/
    agent_dir = script_path.parents[3]
    agent_name = agent_dir.name

    # 去掉前导点：.workbuddy → workbuddy
    if agent_name.startswith('.'):
        agent_name = agent_name[1:]

    skills_dir = agent_dir / 'skills'
    if skills_dir.exists():
        return agent_name, skills_dir
    return None


def scan_skill_dir(skill_path: Path, agent: str, scope: str) -> dict | None:
    """扫描单个技能目录，返回技能信息字典。"""
    skill_md = skill_path / 'SKILL.md'
    if not skill_md.exists():
        return None
    meta = parse_frontmatter(content)
    dir_info = get_dir_info(skill_path)
    latest_mtime = get_latest_mtime(skill_path)

    has_scripts = (skill_path / 'scripts').is_dir()
    has_references = (skill_path / 'references').is_dir()
    has_assets = (skill_path / 'assets').is_dir()

    disable_invocation = meta.get('disable-model-invocation', False)

    description = meta.get('description', '')
    summary = description[:200] + '...' if len(description) > 200 else description

    return {
        'name': meta.get('name', skill_path.name),
        'agent': agent,
        'scope': scope,
        'path': str(skill_path),
        'description': summary,
        'agent_created': meta.get('agent_created', False),
        'version': meta.get('version', 'unknown')
    }


def scan_skills_dir(skills_dir: Path, agent: str, scope: str) -> list[dict]:
    """扫描指定 skills 目录下的所有技能。"""
    if not skills_dir.exists():
        return []

    results = []
    for entry in sorted(skills_dir.iterdir()):
        if entry.is_dir() and not entry.name.startswith('.') and not entry.name.startswith('_'):
            info = scan_skill_dir(entry, agent, scope)
            if info:
                results.append(info)
    return results


def detect_all_agents() -> list[tuple[str, Path]]:
    """检测机器上所有已安装的 Agent 平台。"""
    found = []
    for name in KNOWN_AGENTS:
        skills_dir = Path.home() / f'.{name}' / 'skills'
        if skills_dir.exists():
            found.append((name, skills_dir))
    return found


def print_usage():
    print(__doc__)


def main():
    # ── 解析参数 ──
    agent_override = None
    workspace = None
    scan_all = False

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == '--agent' and i + 1 < len(args):
            agent_override = args[i + 1].strip()
            i += 2
        elif args[i] == '--workspace' and i + 1 < len(args):
            workspace = args[i + 1]
            i += 2
        elif args[i] == '--all':
            scan_all = True
            i += 1
        elif args[i] in ('-h', '--help'):
            print_usage()
            return
        else:
            i += 1

    # ── 确定扫描目标 ──
    skills = []
    agents_scanned = []

    if scan_all:
        # --all: 扫描所有已知 Agent
        for agent_name, skills_dir in detect_all_agents():
            agent_skills = scan_skills_dir(skills_dir, agent_name, 'user')
            skills.extend(agent_skills)
            agents_scanned.append({
                'agent': agent_name,
                'path': str(skills_dir),
                'skill_count': len(agent_skills)
            })
    elif agent_override:
        # --agent: 手动指定
        skills_dir = Path.home() / f'.{agent_override}' / 'skills'
        if not skills_dir.exists():
            print(f"Error: skills directory not found: {skills_dir}", file=sys.stderr)
            sys.exit(1)
        agent_skills = scan_skills_dir(skills_dir, agent_override, 'user')
        skills.extend(agent_skills)
        agents_scanned.append({
            'agent': agent_override,
            'path': str(skills_dir),
            'skill_count': len(agent_skills)
        })
    else:
        # 默认: 自动检测当前 Agent
        detected = detect_current_agent()
        if not detected:
            print("Error: cannot determine current agent from script path.", file=sys.stderr)
            print("Use --agent <name> or --all to specify manually.", file=sys.stderr)
            sys.exit(1)

        agent_name, skills_dir = detected
        agent_skills = scan_skills_dir(skills_dir, agent_name, 'user')
        skills.extend(agent_skills)
        agents_scanned.append({
            'agent': agent_name,
            'path': str(skills_dir),
            'skill_count': len(agent_skills)
        })

    # 扫描项目级技能
    if workspace:
        project_dir = Path(workspace) / '.workbuddy' / 'skills'
        project_skills = scan_skills_dir(project_dir, agents_scanned[0]['agent'] if agents_scanned else 'workbuddy', 'project')
        skills.extend(project_skills)

    # ── 输出 JSON ──
    output = {
        'audit_time': time.strftime('%Y-%m-%d %H:%M:%S'),
        'total_skills': len(skills),
        'agents_scanned': agents_scanned,
        'user_skills': sum(1 for s in skills if s['scope'] == 'user'),
        'project_skills': sum(1 for s in skills if s['scope'] == 'project'),
        'skills': skills
    }