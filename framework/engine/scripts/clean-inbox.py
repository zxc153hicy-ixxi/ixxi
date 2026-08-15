#!/usr/bin/env python3
"""入库完成后清理 personal/data/inbox/ 临时文件，删除前比对 personal/knowledge/ 确认已入库"""
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
INBOX = REPO.parent / "personal" / "data" / "inbox"
KNOWLEDGE = REPO.parent / "personal" / "knowledge"

missing = []   # personal/data/inbox 里有但 personal/knowledge/ 里找不到的
orphan = []    # 可以安全删的

# 1. 检查 personal/data/inbox/converted/ 中的 md 是否已搬进 personal/knowledge/
converted_dir = INBOX / "converted"
if converted_dir.exists():
    for md in converted_dir.rglob("*.md"):
        stem = md.stem
        # 在 personal/knowledge/ 中按文件名搜索
        found = list(KNOWLEDGE.rglob(f"{stem}.md"))
        if found:
            orphan.append(md)
        else:
            missing.append(("converted", md, "personal/knowledge/ 中未找到同名文件"))

# 2. 检查 personal/data/inbox/sources/ 中的原始文件是否有对应 personal/knowledge/ 内容
sources_dir = INBOX / "sources"
if sources_dir.exists():
    for f in sources_dir.rglob("*"):
        if f.is_file():
            stem = f.stem
            found = list(KNOWLEDGE.rglob(f"{stem}.md"))
            if found:
                orphan.append(f)
            else:
                missing.append(("sources", f, "personal/knowledge/ 中未找到对应 md"))

# 3. 输出比对结果
print("=" * 50)
print(f"可安全删除: {len(orphan)} 个文件")
print(f"未入库(保留): {len(missing)} 个文件")
print("=" * 50)

if missing:
    print("\n[未入库文件]")
    for dtype, fpath, reason in missing:
        print(f"  [{dtype}] {fpath.name}")
        print(f"          {reason}")
    print(f"\n以上 {len(missing)} 个文件未入库，跳过不删。")

if orphan:
    print(f"\n正在删除 {len(orphan)} 个已入库文件...")
    for f in orphan:
        f.unlink()
        print(f"  已删除: {f.relative_to(INBOX)}")
    print("OK")

# 4. 清理空目录
for d in ["sources", "converted", "_extracted", "_failed"]:
    target = INBOX / d
    if target.exists():
        for subdir in sorted(target.rglob("*"), reverse=True):
            if subdir.is_dir() and not any(subdir.iterdir()):
                subdir.rmdir()

if not missing and not orphan:
    print("\npersonal/data/inbox/ 无可清理文件。")
