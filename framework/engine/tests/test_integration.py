# -*- coding: utf-8 -*-
"""集成测试：sync 流程（金字塔中层）

构造临时 skill 目录（含 SKILL.md）→ import 脚本模块调 collect_sources →
断言收集到正确 skill 数 → 跑 sync / 生成索引 → 断言产物 → tempfile 自动清理。

不触碰真实仓库：monkeypatch 模块级路径常量（SRC/DST/OUT/REPO）到临时目录。
"""
import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


def load(module_name: str, file_name: str):
    spec = importlib.util.spec_from_file_location(module_name, SCRIPTS / file_name)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sync_claude = load("sync_skills_to_claude", "sync-skills-to-claude.py")
sync_hermes = load("sync_skills_to_hermes", "sync-skills-to-hermes.py")


def make_skill(dirpath: Path, name: str, body: str = "正文\n") -> Path:
    """写一个带 SKILL.md 的技能目录，返回 SKILL.md 路径"""
    d = dirpath / name
    d.mkdir(parents=True)
    sk = d / "SKILL.md"
    sk.write_text(f"---\nname: {name}\ndescription: {name} 的触发场景\n---\n{body}", encoding="utf-8")
    return sk


class SyncFlowBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.mgmt = self.root / "core" / "skills"
        self.mgmt.mkdir(parents=True)
        # 4 个管理技能（一个不带 frontmatter name → 目录名兜底）
        make_skill(self.mgmt, "kb-query", "调用 engine/scripts/check-inbox.py。\n")
        make_skill(self.mgmt, "kb-lint", "调用 engine/scripts/check-links.py。\n")
        make_skill(self.mgmt, "kb-session-close", "见 ops/rules/反馈闭环流程.md。\n")
        no_name = self.mgmt / "kb-no-frontmatter"
        no_name.mkdir()
        (no_name / "SKILL.md").write_text("# 没有 frontmatter\n", encoding="utf-8")


class TestSyncToClaudeFlow(SyncFlowBase):
    """核心/skills → .claude/skills 一级平铺：收集 → 同步 → 校验"""

    def setUp(self):
        super().setUp()
        self.dst = self.root / ".claude" / "skills"
        self.dst.mkdir(parents=True)
        self._old = (sync_claude.SRC, sync_claude.DST)
        sync_claude.SRC, sync_claude.DST = self.mgmt, self.dst
        self.addCleanup(setattr, sync_claude, "SRC", self._old[0])
        self.addCleanup(setattr, sync_claude, "DST", self._old[1])

    def test_collect_gets_correct_skill_count(self):
        sources = sync_claude.collect_sources()
        # 4 个技能目录全部收集；无 SKILL.md 的目录不收集
        self.assertEqual(len(sources), 4)
        self.assertIn("kb-query", sources)
        self.assertIn("kb-no-frontmatter", sources)

    def test_sync_produces_flattened_entries(self):
        sources = sync_claude.collect_sources()
        sync_claude.sync(sources, prune=False)
        for name in sources:
            self.assertTrue((self.dst / name / "SKILL.md").is_file(),
                            f"平铺缺失: {self.dst / name}")
        self.assertEqual(sync_claude.check_only(sources), 0)

    def test_sync_content_matches_source(self):
        sources = sync_claude.collect_sources()
        sync_claude.sync(sources, prune=False)
        copied = (self.dst / "kb-query" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("check-inbox.py", copied)


class TestSyncToHermesFlow(SyncFlowBase):
    """核心/skills + _external → Hermes 命令索引"""

    def setUp(self):
        super().setUp()
        # 外部技能：_external/<分类>/<技能>/SKILL.md（跳过分类级 SKILL.md）
        make_skill(self.mgmt / "_external" / "writing", "kb-novel")
        (self.mgmt / "_external" / "writing" / "SKILL.md").write_text(
            "分类级 SKILL，不收集\n", encoding="utf-8")
        self.ext = self.mgmt / "_external"
        self.out = self.root / "ops" / "hermes" / "Hermes-命令索引.md"
        self._old = (sync_hermes.SRC_MGMT, sync_hermes.SRC_EXT, sync_hermes.REPO, sync_hermes.OUT)
        sync_hermes.SRC_MGMT, sync_hermes.SRC_EXT = self.mgmt, self.ext
        sync_hermes.REPO, sync_hermes.OUT = self.root, self.out
        self.addCleanup(setattr, sync_hermes, "SRC_MGMT", self._old[0])
        self.addCleanup(setattr, sync_hermes, "SRC_EXT", self._old[1])
        self.addCleanup(setattr, sync_hermes, "REPO", self._old[2])
        self.addCleanup(setattr, sync_hermes, "OUT", self._old[3])

    def test_collect_includes_mgmt_and_external(self):
        sources = sync_hermes.collect_sources()
        names = [n for n, _ in sources]
        # 4 管理 + 1 外部，分类级 SKILL.md 被跳过
        self.assertEqual(len(names), 5)
        self.assertIn("kb-query", names)
        self.assertIn("kb-novel", names)

    def test_build_and_write_index(self):
        sources = sync_hermes.collect_sources()
        mgmt = [(n, sync_hermes.skill_description(p / "SKILL.md"), p / "SKILL.md",
                 sync_hermes.ref_scripts(p / "SKILL.md"), sync_hermes.ref_rules(p / "SKILL.md"))
                for n, p in sources if "_external" not in p.parts]
        ext = [(n, sync_hermes.skill_description(p / "SKILL.md"), p / "SKILL.md",
                sync_hermes.ref_scripts(p / "SKILL.md"), sync_hermes.ref_rules(p / "SKILL.md"))
               for n, p in sources if "_external" in p.parts]
        self.assertEqual(len(mgmt), 4)
        self.assertEqual(len(ext), 1)
        self.out.parent.mkdir(parents=True)
        self.out.write_text(sync_hermes.build_index(mgmt, ext), encoding="utf-8")
        content = self.out.read_text(encoding="utf-8")
        self.assertIn("管理 skill（4）", content)
        self.assertIn("外部 skill（1）", content)
        for n in ("kb-query", "kb-lint", "kb-session-close", "kb-no-frontmatter", "kb-novel"):
            self.assertIn(n, content)


if __name__ == "__main__":
    unittest.main()
