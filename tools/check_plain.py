#!/usr/bin/env python3
"""check_plain.py — 逐条检查「说人话」栏是否符合平民语言标准。

规则（照抄 entry-schema.md）：
- 禁统计行话：HR / RR / OR（整词）、队列、样本量数字（n=120、样本量 300 之类）；
- 禁空转加强词：值得注意的是、也就是说、也就是、综上、总而言之、不难发现、众所周知、换句话说；
- 长度 ≤ 120 字（不含 Markdown 加粗符号与空白）；
- 违规逐条列出并退出码 1；须修条目本身，禁止放宽脚本。

用法：python3 tools/check_plain.py [--check]（本脚本天然只读）
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRIES = ROOT / "entries"

PLAIN_RE = re.compile(r"^- \*\*说人话\*\*：(.+)$", re.M)
ENTRY_RE = re.compile(r"(?m)^### (\d+)\. (.+)$")
MAX_LEN = 120

JARGON_RES = [
    (re.compile(r"\b(HR|RR|OR)\b"), "统计行话 HR/RR/OR"),
    (re.compile(r"队列"), "统计行话「队列」"),
    (re.compile(r"[nN]\s*=\s*\d+"), "样本量数字（n=…）"),
    (re.compile(r"样本量\s*\d+"), "样本量数字（样本量…）"),
]
EMPTY_WORDS = ["值得注意的是", "也就是说", "也就是", "综上", "总而言之",
               "不难发现", "众所周知", "换句话说"]


def main():
    _check_only = "--check" in sys.argv
    errors, checked = [], 0
    for f in sorted(ENTRIES.glob("*.md")):
        text = f.read_text(encoding="utf-8")
        entries = [(m.group(1), m.group(2)) for m in ENTRY_RE.finditer(text)]
        plains = PLAIN_RE.findall(text)
        if len(plains) != len(entries):
            errors.append(f"{f.name}：条目数 {len(entries)} 与说人话字段数 {len(plains)} 不一致（有缺字段）")
        for (num, title), raw in zip(entries, plains):
            checked += 1
            body = raw.replace("**", "").strip()
            label = f"{f.name} 第 {num} 条「{title.strip()}」"
            if len(body) > MAX_LEN:
                errors.append(f"{label}：说人话 {len(body)} 字，超过 {MAX_LEN} 字上限")
            for pat, what in JARGON_RES:
                if pat.search(body):
                    errors.append(f"{label}：含{what}")
            for w in EMPTY_WORDS:
                if w in body:
                    errors.append(f"{label}：含空转词「{w}」")
    print(f"共检查 {checked} 条说人话字段")
    if errors:
        for e in errors:
            print("ERROR: " + e, file=sys.stderr)
        sys.exit(1)
    print("全部说人话字段合规，检查通过。")
    sys.exit(0)


if __name__ == "__main__":
    main()
