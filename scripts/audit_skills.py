#!/usr/bin/env python3
"""
技能减法 · 技能扫描脚本

扫描 ~/.workbuddy/skills/ 和当前工作区 .workbuddy/skills/ 下的所有已安装技能，
解析 SKILL.md frontmatter，输出结构化 JSON 报告。

用法：
    python3 audit_skills.py
    python3 audit_skills.py --workspace /path/to/workspace
"""

import json
import os
import sys
import re
import time
from pathlib import Path


def parse_frontmatter(content: str) -> dict:
    """解析 SKILL.md 的 YAML frontmatter，返回字典。"""
    meta = {}
    match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return meta

    frontmatter = match.group(1)
    # 简单 YAML 解析：支持 key: value 和 key: "value"
    for line in frontmatter.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if ':' in line:
            key, _, value = line.partition(':')
            key = key.strip()
            value = value.strip()
            # 去除引号
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            # 处理布尔值
            if value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False
            meta[key] = value
    return meta


def get_dir_info(path: Path) -> dict:
    """获取目录的文件数和大小。"""
    file_count = 0
    total_size = 0
    for root, dirs, files in os.walk(path):
        for f in files:
            file_path = os.path.join(root, f)
            try:
                total_size += os.path.getsize(file_path)
                file_count += 1
            except OSError:
                pass
    return {
        'file_count': file_count,
        'dir_size_kb': round(total_size / 1024, 1)
    }


def get_latest_mtime(path: Path) -> str:
    """获取目录中最近修改的文件时间。"""
    latest = 0
    for root, dirs, files in os.walk(path):
        for f in files:
            file_path = os.path.join(root, f)
            try:
                mtime = os.path.getmtime(file_path)
                if mtime > latest:
                    latest = mtime
            except OSError:
                pass
    if latest == 0:
        return 'unknown'
    # 转换为 YYYY-MM-DD HH:MM:SS
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(latest))


def scan_skill_dir(skill_path: Path, scope: str) -> dict | None:
    """扫描单个技能目录，返回技能信息字典。"""
    skill_md = skill_path / 'SKILL.md'
    if not skill_md.exists():
        return None

    try:
        content = skill_md.read_text(encoding='utf-8')
    except Exception:
        return None

    meta = parse_frontmatter(content)
    dir_info = get_dir_info(skill_path)
    latest_mtime = get_latest_mtime(skill_path)

    # 检查子目录
    has_scripts = (skill_path / 'scripts').is_dir()
    has_references = (skill_path / 'references').is_dir()
    has_assets = (skill_path / 'assets').is_dir()

    # 检查是否禁用
    disable_invocation = meta.get('disable-model-invocation', False)

    # 提取描述的前 100 字作为摘要
    description = meta.get('description', '')
    summary = description[:200] + '...' if len(description) > 200 else description

    return {
        'name': meta.get('name', skill_path.name),
        'scope': scope,
        'path': str(skill_path),
        'description': summary,
        'agent_created': meta.get('agent_created', False),
        'disable_model_invocation': bool(disable_invocation),
        'has_scripts': has_scripts,
        'has_references': has_references,
        'has_assets': has_assets,
        'file_count': dir_info['file_count'],
        'dir_size_kb': dir_info['dir_size_kb'],
        'last_modified': latest_mtime,
        'version': meta.get('version', 'unknown')
    }


def main():
    workspace = None
    if '--workspace' in sys.argv:
        idx = sys.argv.index('--workspace')
        if idx + 1 < len(sys.argv):
            workspace = sys.argv[idx + 1]

    skills = []

    # 1. 扫描用户级技能
    user_skills_dir = Path.home() / '.workbuddy' / 'skills'
    if user_skills_dir.exists():
        for entry in sorted(user_skills_dir.iterdir()):
            if entry.is_dir() and not entry.name.startswith('.') and not entry.name.startswith('_'):
                info = scan_skill_dir(entry, 'user')
                if info:
                    skills.append(info)

    # 2. 扫描项目级技能
    if workspace:
        project_skills_dir = Path(workspace) / '.workbuddy' / 'skills'
    else:
        # 尝试当前工作目录
        project_skills_dir = Path.cwd() / '.workbuddy' / 'skills'

    if project_skills_dir.exists():
        for entry in sorted(project_skills_dir.iterdir()):
            if entry.is_dir() and not entry.name.startswith('.') and not entry.name.startswith('_'):
                info = scan_skill_dir(entry, 'project')
                if info:
                    skills.append(info)

    # 输出 JSON
    output = {
        'audit_time': time.strftime('%Y-%m-%d %H:%M:%S'),
        'total_skills': len(skills),
        'user_skills': sum(1 for s in skills if s['scope'] == 'user'),
        'project_skills': sum(1 for s in skills if s['scope'] == 'project'),
        'skills': skills
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
