"""Render every ```mermaid block in the given Markdown files and report failures.

Usage: python3 tools/check_mermaid.py spec/03-shipments.md [more.md ...]
Requires Node (npx downloads @mermaid-js/mermaid-cli on first run).
"""
import os, re, subprocess, sys, tempfile

BLOCK = re.compile(r"```mermaid\n(.*?)```", re.S)

def check(path):
    text = open(path).read()
    failures = 0
    blocks = BLOCK.findall(text)
    with tempfile.TemporaryDirectory() as tmp:
        for i, src in enumerate(blocks, 1):
            mmd, svg = os.path.join(tmp, f"{i}.mmd"), os.path.join(tmp, f"{i}.svg")
            open(mmd, "w").write(src)
            r = subprocess.run(["npx", "-y", "@mermaid-js/mermaid-cli@latest", "-i", mmd, "-o", svg, "-q"],
                               capture_output=True, text=True)
            if r.returncode != 0 or not os.path.exists(svg):
                failures += 1
                first = src.strip().splitlines()[0] if src.strip() else ""
                err = (r.stderr or r.stdout).strip().splitlines()
                print(f"FAIL {path} block {i} ({first}): {' | '.join(err[:4])}")
    print(f"{path}: {len(blocks)} diagram(s), {failures} failure(s)")
    return failures

if __name__ == "__main__":
    sys.exit(1 if sum(check(p) for p in sys.argv[1:]) else 0)
