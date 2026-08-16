# -*- coding: utf-8 -*-
"""e2e 测试：完整使用路径（金字塔顶层，最少最慢）

模拟最小闭环：init 生成 personal 骨架 → 复制 demo 数据 → 跑 scan-sensitive。
用 tempfile 临时目录，测试后自动清理，不触碰真实仓库。

真实 ixxi 中对应：`./ixxi init`（step 2 骨架）→ raw 输入放 demo-note.md →
`python engine/scripts/scan-sensitive.py --repo <root>`。
"""
import importlib.util
import io
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
SAMPLES = SCRIPTS.parent.parent / "samples"  # framework/samples（demo 数据）

scan = None


def load_scan():
    global scan
    if scan is None:
        spec = importlib.util.spec_from_file_location("scan_sensitive_e2e", SCRIPTS / "scan-sensitive.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        scan = mod
    return scan


def make_personal_skeleton(root: Path) -> None:
    """镜像 ixxi init（./ixxi）step 2 的 personal 骨架生成逻辑"""
    p = root / "personal"
    (p / "system" / "skills").mkdir(parents=True)
    for d in ("system/patterns", "system/anti-patterns", "system/rules", "system/queries"):
        (p / d).mkdir(parents=True)
    for d in ("knowledge/projects", "knowledge/learning", "knowledge/archive"):
        (p / d).mkdir(parents=True)
    for d in ("data/feedback", "data/sessions", "data/inbox", "data/memory"):
        (p / d).mkdir(parents=True)
    (p / "README.md").write_text("# personal 实例层\n", encoding="utf-8")
    (p / "index.md").write_text("# 实例导航\n", encoding="utf-8")
    (p / "CLAUDE.md").write_text("# 个人规则覆盖层\n", encoding="utf-8")
    (p / "data" / "用户画像.md").write_text("---\nstatus: active\n---\n# 用户画像\n", encoding="utf-8")
    (p / "data" / "scene-registry.md").write_text("# 场景注册表\n", encoding="utf-8")
    (p / "data" / "queue.md").write_text("", encoding="utf-8")
    (p / "data" / "log.md").write_text("", encoding="utf-8")


class TestInitScanLoop(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        make_personal_skeleton(self.root)

    def _assert_skeleton_files(self):
        p = self.root / "personal"
        for rel in ("README.md", "index.md", "CLAUDE.md",
                    "data/用户画像.md", "data/scene-registry.md", "data/queue.md", "data/log.md"):
            self.assertTrue((p / rel).is_file(), f"骨架缺 {rel}")
        self.assertTrue((p / "system" / "skills").is_dir())
        for d in ("system/patterns", "system/anti-patterns", "system/rules", "system/queries",
                  "knowledge/projects", "knowledge/learning", "knowledge/archive",
                  "data/feedback", "data/sessions", "data/inbox", "data/memory"):
            self.assertTrue((p / d).is_dir(), f"骨架缺目录 {d}")

    def test_full_loop_personal_skeleton_demo_data_scan_pass(self):
        """init 骨架 → 复制 demo 数据 → scan-sensitive 通过"""
        # 步骤 2（模拟）：复制 demo 数据到 raw 输入
        src_demo = SAMPLES / "demo-note.md"
        self.assertTrue(src_demo.is_file(), f"缺少 demo 数据: {src_demo}")
        shutil.copy(src_demo, self.root / "personal" / "data" / "inbox" / "demo-note.md")

        self._assert_skeleton_files()
        self.assertTrue((self.root / "personal" / "data" / "inbox" / "demo-note.md").is_file())

        # 步骤 3：跑 scan-sensitive（库函数 + CLI 路径双验证）
        mod = load_scan()
        self.assertEqual(mod.scan_repo(self.root), [])

        old_argv = sys.argv
        self.addCleanup(setattr, sys, "argv", old_argv)
        sys.argv = ["scan-sensitive.py", "--repo", str(self.root)]
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = mod.main()
        self.assertEqual(code, 0, buf.getvalue())
        self.assertIn("安全扫描通过", buf.getvalue())

    def test_scan_detects_real_secret_in_private_data(self):
        """反证扫描有意义：private 数据里藏密码 → 扫描必须报失败"""
        (self.root / "personal" / "knowledge" / "projects" / "secret-note.md").write_text(
            "账号密码：password: hunter2 千万别泄露\n", encoding="utf-8")

        mod = load_scan()
        hits = mod.scan_repo(self.root)
        self.assertTrue(any(h["type"] == "密码明文" for h in hits))

        old_argv = sys.argv
        self.addCleanup(setattr, sys, "argv", old_argv)
        sys.argv = ["scan-sensitive.py", "--repo", str(self.root)]
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = mod.main()
        self.assertEqual(code, 1)
        self.assertIn("发现 1 处", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
