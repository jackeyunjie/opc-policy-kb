#!/usr/bin/env python3
"""check_links.py — 扫描 entries/*.md 的「来源」栏 URL，检查可达性。

规则（照抄生产者链路）：
- 只有确定失效（HTTP 404/410）才报错，退出码 1；
- 超时、403、连接拒绝等暂时不可达只记警告，不失败；
- --check 只读模式（本脚本本就不写文件，--check 仅作显式声明）。

用法：python3 tools/check_links.py [--check]
"""
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRIES = ROOT / "entries"
TIMEOUT = 10
URL_RE = re.compile(r"https?://[^\s)）>\"']+")
SRC_RE = re.compile(r"^- \*\*来源\*\*：", re.M)


def collect_urls():
    """返回 [(file, lineno, url), ...]，只取「来源」栏内的链接。"""
    out = []
    for f in sorted(ENTRIES.glob("*.md")):
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if line.startswith("- **来源**："):
                for u in URL_RE.findall(line):
                    out.append((f.name, i, u.rstrip("。，；")))
    return out


def probe(url):
    """返回 (status, note)。status: ok / dead / warn。"""
    req = urllib.request.Request(url, method="HEAD",
                                 headers={"User-Agent": "opc-policy-kb-link-checker/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return ("ok", r.status)
    except urllib.error.HTTPError as e:
        if e.code in (404, 410):
            return ("dead", e.code)
        if e.code == 405:  # HEAD 不被允许，回退 GET
            req = urllib.request.Request(url, method="GET",
                                         headers={"User-Agent": "opc-policy-kb-link-checker/1.0"})
            try:
                with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                    return ("ok", r.status)
            except urllib.error.HTTPError as e2:
                return ("dead", e2.code) if e2.code in (404, 410) else ("warn", e2.code)
            except Exception as e2:  # noqa: BLE001
                return ("warn", repr(e2))
        return ("warn", e.code)
    except Exception as e:  # noqa: BLE001 — 超时/断网/SSL 均按警告处理
        return ("warn", repr(e))


def main():
    _check_only = "--check" in sys.argv  # 本脚本天然只读，参数仅为显式语义
    urls = collect_urls()
    print(f"共发现 {len(urls)} 个来源链接")
    dead, warned = [], []
    for name, lineno, url in urls:
        status, note = probe(url)
        tag = {"ok": "OK  ", "dead": "DEAD", "warn": "WARN"}[status]
        print(f"[{tag}] {name}:{lineno} {url} -> {note}")
        if status == "dead":
            dead.append((name, lineno, url, note))
        elif status == "warn":
            warned.append((name, lineno, url, note))
    print(f"\n结果：{len(urls) - len(dead) - len(warned)} 可达，{len(warned)} 警告（暂不失败），{len(dead)} 失效")
    if dead:
        print("存在确定失效（404/410）链接，需修复：", file=sys.stderr)
        sys.exit(1)
    print("无确定失效链接，检查通过。")
    sys.exit(0)


if __name__ == "__main__":
    main()
