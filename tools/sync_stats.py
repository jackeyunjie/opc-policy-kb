#!/usr/bin/env python3
"""sync_stats.py — 统计条目总数 / A/B/C 分布 / 争议数 / 待核实数，写回 README stats 标记块。

- 默认模式：重新计算并覆写 README.md 中 <!-- stats:start --> 与 <!-- stats:end --> 之间的内容；
- --check 模式：只比对不写入，不一致则退出码 1。

用法：python3 tools/sync_stats.py [--check]
"""
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRIES = ROOT / "entries"
README = ROOT / "README.md"
START = "<!-- stats:start -->"
END = "<!-- stats:end -->"

ENTRY_RE = re.compile(r"(?m)^### \d+\. ")
GRADE_RE = re.compile(r"- \*\*证据等级\*\*：\s*([ABC])")


def collect():
    total, grades, dispute, pending = 0, {"A": 0, "B": 0, "C": 0}, 0, 0
    for f in sorted(ENTRIES.glob("*.md")):
        text = f.read_text(encoding="utf-8")
        blocks = ENTRY_RE.split(text)[1:]
        for b in blocks:
            total += 1
            m = GRADE_RE.search(b)
            if m:
                grades[m.group(1)] += 1
                grade_line = next(l for l in b.splitlines() if l.startswith("- **证据等级**"))
                if "争议" in grade_line:
                    dispute += 1
            else:
                print(f"警告：{f.name} 中有条目缺证据等级字段", file=sys.stderr)
            pending += b.count("待核实")
    return total, grades, dispute, pending


def render(total, grades, dispute, pending):
    return (
        f"{START}\n"
        f"- 条目总数：{total}\n"
        f"- 证据等级分布：A {grades['A']} 条 / B {grades['B']} 条 / C {grades['C']} 条\n"
        f"- 争议条目：{dispute} 条\n"
        f"- 待核实：{pending} 处\n"
        f"- 统计更新：{date.today().isoformat()}\n"
        f"{END}"
    )


def main():
    check_only = "--check" in sys.argv
    total, grades, dispute, pending = collect()
    block = render(total, grades, dispute, pending)
    text = README.read_text(encoding="utf-8")
    pat = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    m = pat.search(text)
    if not m:
        print("README.md 中未找到 stats 标记块", file=sys.stderr)
        sys.exit(1)
    if check_only:
        if m.group(0) == block:
            print(f"stats 一致：总数 {total}，A {grades['A']} / B {grades['B']} / C {grades['C']}，争议 {dispute}，待核实 {pending}")
            sys.exit(0)
        print("stats 与 README 不一致，请运行 python3 tools/sync_stats.py 重新同步", file=sys.stderr)
        print("--- 应为 ---\n" + block, file=sys.stderr)
        sys.exit(1)
    README.write_text(pat.sub(lambda _: block, text), encoding="utf-8")
    print(f"已写回 README：总数 {total}，A {grades['A']} / B {grades['B']} / C {grades['C']}，争议 {dispute}，待核实 {pending}")
    sys.exit(0)


if __name__ == "__main__":
    main()
