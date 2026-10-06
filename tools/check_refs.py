#!/usr/bin/env python3
"""check_refs.py — 校验条目间「见第 X 节第 Y 条（锚点词）」交叉引用。

规则：
- 节号 X 必须有对应 entries 文件（文件头 `# 第 X 节 …`）；
- 条号 Y 必须在该节内真实存在（`### Y. …`）；
- 锚点词必须出现在目标条目的标题或正文中；
- 增删条目导致条号顺延时本脚本会报错，须修条目本身，禁止放宽脚本。

用法：python3 tools/check_refs.py [--check]（本脚本天然只读）
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRIES = ROOT / "entries"

SEC_HEADER_RE = re.compile(r"(?m)^# 第 (\d+) 节")
ENTRY_RE = re.compile(r"(?m)^### (\d+)\. ")
REF_RE = re.compile(r"见第\s*(\d+)\s*节第\s*(\d+)\s*条（([^）]+)）")


def load_sections():
    """返回 {节号: {条号: 条目全文}} 与 {节号: 文件名}。"""
    sections, names = {}, {}
    for f in sorted(ENTRIES.glob("*.md")):
        text = f.read_text(encoding="utf-8")
        m = SEC_HEADER_RE.search(text)
        if not m:
            print(f"警告：{f.name} 缺少「# 第 N 节」文件头", file=sys.stderr)
            continue
        sec = int(m.group(1))
        names[sec] = f.name
        entries = {}
        matches = list(ENTRY_RE.finditer(text))
        for i, em in enumerate(matches):
            start = em.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            entries[int(em.group(1))] = text[start:end]
        sections[sec] = entries
    return sections, names


def main():
    _check_only = "--check" in sys.argv
    sections, names = load_sections()
    errors = []
    ref_count = 0
    for f in sorted(ENTRIES.glob("*.md")):
        text = f.read_text(encoding="utf-8")
        for sec_s, idx_s, anchor in REF_RE.findall(text):
            ref_count += 1
            sec, idx = int(sec_s), int(idx_s)
            where = f"{f.name} → 见第 {sec} 节第 {idx} 条（{anchor}）"
            if sec not in sections:
                errors.append(f"{where}：第 {sec} 节不存在")
                continue
            if idx not in sections[sec]:
                errors.append(f"{where}：第 {sec} 节（{names[sec]}）内不存在第 {idx} 条")
                continue
            if anchor not in sections[sec][idx]:
                errors.append(f"{where}：锚点词「{anchor}」未出现在目标条目标题或正文")
    print(f"共校验 {ref_count} 处交叉引用")
    if errors:
        for e in errors:
            print("ERROR: " + e, file=sys.stderr)
        sys.exit(1)
    print("全部交叉引用有效，检查通过。")
    sys.exit(0)


if __name__ == "__main__":
    main()
