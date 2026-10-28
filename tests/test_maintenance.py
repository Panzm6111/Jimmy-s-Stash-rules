#!/usr/bin/env python3
"""Maintenance simulations only: no network, personal files, or Stash runtime."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import maintain


OLD_REVISION = "1" * 40
NEW_REVISION = "2" * 40
RULE_REPO = "blackmatrix7/ios_rule_script"
SCRIPT_REPO = "app2smile/rules"
AI_REPO = "v2fly/domain-list-community"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def public_url(repository, revision, path):
    return f"https://raw.githubusercontent.com/{repository}/{revision}/{path}"


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def git(root, *args):
    return subprocess.check_output(
        ["git", "-C", str(root), *args], stderr=subprocess.DEVNULL, text=True
    ).strip()


class SourceFixture:
    """Small, explicitly simulated upstream resources with real hash comparisons."""

    def __init__(self, root):
        self.root = root
        self.data = {}
        self.rule_path = "rule/Clash/AdvertisingLite/AdvertisingLite_Classical.yaml"
        self.script_path = "js/bilibili-json.js"
        self.rule_bytes = b"payload:\n  - DOMAIN,ads.example.invalid\n"
        self.script_bytes = b"// simulated script, never executed\n"
        self.license_bytes = b"simulated license text\n"
        self.ai_bytes = b"example.invalid\n"
        for repository, path, body in [
            (RULE_REPO, self.rule_path, self.rule_bytes),
            (SCRIPT_REPO, self.script_path, self.script_bytes),
            (AI_REPO, "data/openai", self.ai_bytes),
            (RULE_REPO, "LICENSE", self.license_bytes),
            (SCRIPT_REPO, "LICENSE.md", self.license_bytes),
            (AI_REPO, "LICENSE", self.license_bytes),
        ]:
            self.data[public_url(repository, NEW_REVISION, path)] = body
            self.data[public_url(repository, OLD_REVISION, path)] = body
        for name in ["blackmatrix7-GPL-2.0.txt", "app2smile-MIT.txt", "v2fly-MIT.txt"]:
            path = root / "licenses" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(self.license_bytes)
        write_json(root / "research/sources.lock.json", {
            "upstream": {
                "repository": RULE_REPO,
                "revision": OLD_REVISION,
                "license_file": "licenses/blackmatrix7-GPL-2.0.txt",
            },
            "resources": [{
                "url": public_url(RULE_REPO, OLD_REVISION, self.rule_path),
                "source_path": self.rule_path,
                "source_sha256": digest(self.rule_bytes),
                "output": "rules/vendor/ads-expanded.yaml",
                "output_sha256": digest(self.rule_bytes),
                "retained": 1,
            }],
            "ad_scripts": [{
                "source_url": public_url(SCRIPT_REPO, OLD_REVISION, self.script_path),
                "source_sha256": digest(self.script_bytes),
                "output": "scripts/ads/bilibili-json.js",
                "output_sha256": digest(self.script_bytes),
                "license_file": "licenses/app2smile-MIT.txt",
            }],
            "ad_supporting_sources": [],
        })
        write_json(root / "research/ad-catalog.json", {"sources": {}, "modules": []})
        write_json(root / "research/ai-sources.json", {
            "output": "rules/openai.yaml",
            "upstream": {
                "repository": f"https://github.com/{AI_REPO}",
                "revision": OLD_REVISION,
                "license_url": public_url(AI_REPO, OLD_REVISION, "LICENSE"),
                "license_file": "licenses/v2fly-MIT.txt",
                "license_sha256": digest(self.license_bytes),
            },
            "sources": [{
                "url": public_url(AI_REPO, OLD_REVISION, "data/openai"),
                "sha256": digest(self.ai_bytes),
            }],
        })

    def fetch(self, url):
        return self.data[url]

    def check(self):
        return maintain.check_upstreams(
            self.root, fetcher=self.fetch, head_resolver=lambda _: NEW_REVISION
        )


class UpstreamMaintenanceTests(unittest.TestCase):
    def test_source_urls_must_be_public_pinned_and_allowlisted(self):
        url = public_url(RULE_REPO, OLD_REVISION, "rule/Clash/China/China.yaml")
        self.assertEqual(
            maintain.parse_source_url(url),
            (RULE_REPO, OLD_REVISION, "rule/Clash/China/China.yaml"),
        )
        rejected = [
            url.replace("https://", "http://"),
            url.replace(OLD_REVISION, "main"),
            url + "?token=EXAMPLE_NOT_A_SECRET",
            url.replace(RULE_REPO, "unreviewed/another-repo"),
            url.replace("rule/Clash/China/China.yaml", "../private.yaml"),
        ]
        for value in rejected:
            with self.subTest(value=value), self.assertRaises(maintain.MaintenanceError):
                maintain.parse_source_url(value)

    def test_new_commit_with_same_relevant_bytes_needs_no_update(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            report = fixture.check()
            files = report["files"]
            self.assertTrue(files)
            self.assertEqual({item["status"] for item in files}, {"unchanged"})

    def test_rules_and_scripts_are_reported_separately(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            fixture.data[public_url(RULE_REPO, NEW_REVISION, fixture.rule_path)] += (
                b"  - DOMAIN,new-ad.example.invalid\n"
            )
            fixture.data[public_url(SCRIPT_REPO, NEW_REVISION, fixture.script_path)] += (
                b"// upstream logic changed\n"
            )
            files = {item["path"]: item for item in fixture.check()["files"]}
            self.assertEqual(files[fixture.rule_path]["status"], "rules-update")
            self.assertEqual(files[fixture.script_path]["status"], "review-required")
            # Inspection never replaces a local adapted script.
            self.assertFalse((fixture.root / "scripts/ads/bilibili-json.js").exists())

    def test_network_error_reports_type_without_sensitive_exception(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            marker = "PRIVATE_TEST_MARKER_NOT_A_SECRET"

            def failed(_):
                raise RuntimeError("https://private.invalid/?" + marker)

            report = maintain.check_upstreams(
                fixture.root, fetcher=failed, head_resolver=lambda _: NEW_REVISION
            )
            self.assertTrue(any(item["status"] == "error" for item in report["files"]))
            self.assertNotIn(marker, json.dumps(report))
            self.assertNotIn("private.invalid", json.dumps(report))

    def test_empty_download_is_an_error_not_an_update(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            fixture.data[public_url(RULE_REPO, NEW_REVISION, fixture.rule_path)] = b""
            report = fixture.check()
            files = {item["path"]: item for item in report["files"]}
            self.assertEqual(files[fixture.rule_path]["status"], "error")
            self.assertFalse(report["ok"])

    def test_license_change_never_becomes_a_rule_update(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            fixture.data[public_url(RULE_REPO, NEW_REVISION, "LICENSE")] += b"changed\n"
            report = fixture.check()
            licenses = [
                item for item in report["files"]
                if item["repository"] == RULE_REPO and item["path"] == "LICENSE"
            ]
            self.assertEqual(len(licenses), 1)
            self.assertEqual(licenses[0]["status"], "review-required")

    def test_changed_bytes_at_same_commit_are_integrity_error(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = SourceFixture(Path(directory))
            fixture.data[public_url(RULE_REPO, OLD_REVISION, fixture.rule_path)] += (
                b"  - DOMAIN,unexpected.example.invalid\n"
            )
            report = maintain.check_upstreams(
                fixture.root, fetcher=fixture.fetch, head_resolver=lambda _: OLD_REVISION
            )
            files = {item["path"]: item for item in report["files"]}
            self.assertEqual(files[fixture.rule_path]["status"], "error")

    def test_small_rule_increment_is_allowed(self):
        old = [f"DOMAIN,a{i}.example.invalid" for i in range(100)]
        new = old + ["DOMAIN,new.example.invalid"]
        delta = maintain.rule_delta(old, new)
        self.assertFalse(delta["blocked"])
        self.assertEqual(delta["added"], 1)
        self.assertEqual(delta["removed"], 0)

    def test_existing_top_level_suffixes_do_not_block_ordinary_increment(self):
        reviewed_suffixes = ["DOMAIN-SUFFIX,cn", "DOMAIN-SUFFIX,youtube", "DOMAIN-SUFFIX,ms"]
        old = [f"DOMAIN,a{i}.example.invalid" for i in range(100)] + reviewed_suffixes
        new = old + ["DOMAIN-SUFFIX,ads.example.invalid"]
        for rule in reviewed_suffixes:
            maintain.validate_rule(rule)
        delta = maintain.rule_delta(old, new)
        self.assertFalse(delta["blocked"])
        self.assertEqual(delta["added"], 1)
        self.assertEqual(delta["removed"], 0)

    def test_new_top_level_suffix_requires_review_but_exact_domain_does_not(self):
        old = [f"DOMAIN,a{i}.example.invalid" for i in range(100)]
        suffix_delta = maintain.rule_delta(old, old + ["DOMAIN-SUFFIX,cn"])
        self.assertTrue(suffix_delta["blocked"])
        self.assertIn("new_top_level_suffix", suffix_delta["reasons"])
        exact_delta = maintain.rule_delta(old, old + ["DOMAIN,cn"])
        self.assertFalse(exact_delta["blocked"])
        self.assertNotIn("new_top_level_suffix", exact_delta["reasons"])

    def test_large_deletion_or_replacement_is_blocked(self):
        old = [f"DOMAIN,a{i}.example.invalid" for i in range(100)]
        for new in [
            [],
            old[:89],
            old[:80] + [f"DOMAIN,b{i}.example.invalid" for i in range(20)],
            old + [f"DOMAIN,b{i}.example.invalid" for i in range(26)],
        ]:
            with self.subTest(size=len(new)):
                delta = maintain.rule_delta(old, new)
                self.assertTrue(delta["blocked"])
                self.assertTrue(delta["reasons"])

    def test_empty_invalid_or_duplicate_key_rule_documents_are_rejected(self):
        for raw in [
            b"",
            b"payload: []\n",
            b"payload: [1]\n",
            b"payload: [DOMAIN,example.invalid]\nextra: true\n",
            b"payload: [one]\npayload: [two]\n",
            b"proxies: []\n",
        ]:
            with self.subTest(raw=raw), self.assertRaises(maintain.MaintenanceError):
                maintain.rule_payload(raw)

    def test_rule_action_injection_and_bad_networks_are_rejected(self):
        for rule in [
            "DOMAIN,ads.example.invalid,DIRECT",
            "DOMAIN-SUFFIX,https://example.invalid/path",
            "DOMAIN-KEYWORD,*",
            "MATCH,REJECT",
            "IP-CIDR,not-a-network",
            "IP-CIDR,2001:db8::/32",
            "IP-CIDR6,192.0.2.0/24",
        ]:
            with self.subTest(rule=rule), self.assertRaises(maintain.MaintenanceError):
                maintain.validate_rule(rule)
        maintain.validate_rule("IP-CIDR,192.0.2.0/24,no-resolve")


class MaintenanceTransactionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repository"
        self.root.mkdir()
        git(self.root, "init", "-q")
        git(self.root, "config", "user.name", "Maintenance simulation")
        git(self.root, "config", "user.email", "simulation@example.invalid")
        git(self.root, "config", "commit.gpgsign", "false")
        hooks = Path(self.temp.name) / "empty-hooks"
        hooks.mkdir()
        git(self.root, "config", "core.hooksPath", str(hooks))
        (self.root / ".gitignore").write_text(".local/\n", encoding="utf-8")
        self.paths = {"rules/vendor/ads-expanded.yaml", "config/stash.yaml"}
        for relative in self.paths:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(("before:" + relative).encode())
        git(self.root, "add", ".")
        git(self.root, "commit", "-qm", "Initial simulated content")
        self.base_head = git(self.root, "rev-parse", "HEAD")
        self.candidate = Path(self.temp.name) / "candidate"
        self.candidate.mkdir()
        shutil.copyfile(self.root / ".gitignore", self.candidate / ".gitignore")
        for relative in self.paths:
            path = self.candidate / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(("after:" + relative).encode())

    def apply(self):
        return maintain.apply_verified_changes(
            self.root, self.candidate, self.paths, self.base_head
        )

    def test_apply_preserves_head_and_rollback_restores_exact_bytes(self):
        before = {path: (self.root / path).read_bytes() for path in self.paths}
        backup_id = self.apply()
        self.assertTrue(backup_id)
        self.assertEqual(git(self.root, "rev-parse", "HEAD"), self.base_head)
        for path in self.paths:
            self.assertEqual((self.root / path).read_bytes(), (self.candidate / path).read_bytes())
        maintain.rollback(self.root, backup_id)
        for path in self.paths:
            self.assertEqual((self.root / path).read_bytes(), before[path])
        self.assertEqual(git(self.root, "status", "--porcelain"), "")

    def test_dirty_working_tree_is_not_overwritten(self):
        path = self.root / "config/stash.yaml"
        path.write_bytes(b"user edit")
        with self.assertRaises(maintain.MaintenanceError):
            self.apply()
        self.assertEqual(path.read_bytes(), b"user edit")

    def test_noop_candidate_does_not_write_or_create_backup(self):
        for path in self.paths:
            shutil.copyfile(self.root / path, self.candidate / path)
        mtimes = {path: (self.root / path).stat().st_mtime_ns for path in self.paths}
        self.assertIsNone(self.apply())
        self.assertEqual(git(self.root, "status", "--porcelain"), "")
        for path in self.paths:
            self.assertEqual((self.root / path).stat().st_mtime_ns, mtimes[path])

    def test_unapproved_candidate_change_is_not_applied(self):
        (self.candidate / ".gitignore").write_text("changed outside allowlist\n", encoding="utf-8")
        with self.assertRaises(maintain.MaintenanceError):
            self.apply()
        self.assertEqual(git(self.root, "status", "--porcelain"), "")

    def test_candidate_file_removal_is_not_applied(self):
        (self.candidate / "config/stash.yaml").unlink()
        with self.assertRaises(maintain.MaintenanceError):
            self.apply()
        self.assertEqual(git(self.root, "status", "--porcelain"), "")

    def test_candidate_symlink_is_not_applied(self):
        path = self.candidate / "config/stash.yaml"
        path.unlink()
        outside = Path(self.temp.name) / "untrusted.yaml"
        outside.write_bytes(b"outside")
        try:
            path.symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable for this local account")
        with self.assertRaises(maintain.MaintenanceError):
            self.apply()
        self.assertEqual(git(self.root, "status", "--porcelain"), "")
        self.assertEqual(outside.read_bytes(), b"outside")

    def test_changed_head_is_not_overwritten(self):
        git(self.root, "commit", "--allow-empty", "-qm", "Concurrent commit")
        with self.assertRaises(maintain.MaintenanceError):
            self.apply()
        self.assertTrue((self.root / "config/stash.yaml").read_bytes().startswith(b"before:"))

    def test_rollback_refuses_to_overwrite_edit_after_update(self):
        backup_id = self.apply()
        path = self.root / "config/stash.yaml"
        path.write_bytes(b"newer user edit")
        before_rollback = {p: (self.root / p).read_bytes() for p in self.paths}
        with self.assertRaises(maintain.MaintenanceError):
            maintain.rollback(self.root, backup_id)
        for relative in self.paths:
            self.assertEqual((self.root / relative).read_bytes(), before_rollback[relative])

    def test_concurrent_maintenance_is_blocked_and_lock_released(self):
        with maintain.maintenance_lock(self.root):
            with self.assertRaises(maintain.MaintenanceError):
                with maintain.maintenance_lock(self.root):
                    self.fail("second owner acquired maintenance lock")
        with maintain.maintenance_lock(self.root):
            pass

    def test_interrupted_apply_restores_all_previously_written_files(self):
        atomic_write = maintain.atomic_write
        fail_path = self.root / "rules/vendor/ads-expanded.yaml"

        def fail_once(path, data):
            if Path(path) == fail_path and data.startswith(b"after:"):
                raise OSError("simulated write failure")
            atomic_write(path, data)

        with mock.patch.object(maintain, "atomic_write", side_effect=fail_once):
            with self.assertRaises(maintain.MaintenanceError) as caught:
                self.apply()
        self.assertEqual(caught.exception.code, "apply_failed_restored")
        self.assertEqual(git(self.root, "status", "--porcelain"), "")
        for path in self.paths:
            self.assertTrue((self.root / path).read_bytes().startswith(b"before:"))

    def test_interrupted_rollback_preserves_complete_post_update_content(self):
        backup_id = self.apply()
        atomic_write = maintain.atomic_write
        fail_path = self.root / "rules/vendor/ads-expanded.yaml"

        def fail_once(path, data):
            if Path(path) == fail_path and data.startswith(b"before:"):
                raise OSError("simulated rollback failure")
            atomic_write(path, data)

        with mock.patch.object(maintain, "atomic_write", side_effect=fail_once):
            with self.assertRaises(maintain.MaintenanceError):
                maintain.rollback(self.root, backup_id)
        for path in self.paths:
            self.assertEqual((self.root / path).read_bytes(), (self.candidate / path).read_bytes())

    def test_backup_pointer_failure_restores_pre_update_content(self):
        atomic_write = maintain.atomic_write
        pointer = self.root / ".local/maintenance/latest-backup.json"

        def fail_pointer(path, data):
            if Path(path) == pointer:
                raise OSError("simulated backup metadata failure")
            atomic_write(path, data)

        with mock.patch.object(maintain, "atomic_write", side_effect=fail_pointer):
            with self.assertRaises(maintain.MaintenanceError) as caught:
                self.apply()
        self.assertEqual(caught.exception.code, "apply_failed_restored")
        self.assertEqual(git(self.root, "status", "--porcelain"), "")
        self.assertFalse(pointer.exists())

    def test_corrupted_backup_is_not_restored(self):
        backup_id = self.apply()
        path = self.root / ".local/maintenance/backups" / backup_id / "before/config/stash.yaml"
        path.write_bytes(b"corrupted simulated backup")
        with self.assertRaises(maintain.MaintenanceError) as caught:
            maintain.rollback(self.root, backup_id)
        self.assertEqual(caught.exception.code, "backup_corrupted")
        for relative in self.paths:
            self.assertEqual(
                (self.root / relative).read_bytes(),
                (self.candidate / relative).read_bytes(),
            )

    def source_fixture(self):
        fixture = SourceFixture(self.root)
        git(self.root, "add", ".")
        git(self.root, "commit", "-qm", "Public source simulation")
        return fixture

    def test_noop_update_keeps_pins_and_skips_build(self):
        fixture = self.source_fixture()
        before = (self.root / "research/sources.lock.json").read_bytes()
        with mock.patch.object(maintain.shutil, "which", return_value="node"):
            with mock.patch.object(maintain, "run_step") as run:
                self.assertIsNone(maintain.update(self.root, fixture.check()))
        run.assert_not_called()
        self.assertEqual((self.root / "research/sources.lock.json").read_bytes(), before)
        self.assertEqual(git(self.root, "status", "--porcelain"), "")

    def test_license_change_stops_update_before_clone(self):
        fixture = self.source_fixture()
        fixture.data[public_url(RULE_REPO, NEW_REVISION, "LICENSE")] += b"changed\n"
        with mock.patch.object(maintain.shutil, "which", return_value="node"):
            with mock.patch.object(maintain, "run_step") as run:
                with self.assertRaises(maintain.MaintenanceError) as caught:
                    maintain.update(self.root, fixture.check())
        self.assertEqual(caught.exception.code, "license_changed")
        run.assert_not_called()
        self.assertEqual(git(self.root, "status", "--porcelain"), "")

    def prepare_rule_increment(self):
        fixture = self.source_fixture()
        old = b"payload:\n" + b"".join(
            f"  - DOMAIN,a{i}.example.invalid\n".encode() for i in range(100)
        )
        new = old + b"  - DOMAIN,new-ad.example.invalid\n"
        fixture.data[public_url(RULE_REPO, OLD_REVISION, fixture.rule_path)] = old
        fixture.data[public_url(RULE_REPO, NEW_REVISION, fixture.rule_path)] = new
        (self.root / "rules/vendor/ads-expanded.yaml").write_bytes(old)
        lock_path = self.root / "research/sources.lock.json"
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        lock["resources"][0].update(
            source_sha256=digest(old), output_sha256=digest(old), retained=100
        )
        write_json(lock_path, lock)
        git(self.root, "add", ".")
        git(self.root, "commit", "-qm", "Initial simulated rule payload")
        return fixture, new

    def simulated_refresh_runner(self, payload, *, reported_hash=None, fail_label="project_and_scripts"):
        real_run = maintain.run_step

        def run(directory, command, label, timeout=240):
            if label == "clone":
                return real_run(directory, command, label, timeout=timeout)
            if label == "refresh_rules":
                path = Path(directory) / "research/sources.lock.json"
                lock = json.loads(path.read_text(encoding="utf-8"))
                lock["upstream"]["revision"] = NEW_REVISION
                resource = lock["resources"][0]
                resource["url"] = public_url(RULE_REPO, NEW_REVISION, resource["source_path"])
                resource["source_sha256"] = reported_hash or digest(payload)
                resource["output_sha256"] = digest(payload)
                resource["retained"] = 101
                (Path(directory) / resource["output"]).write_bytes(payload)
                write_json(path, lock)
            elif label == fail_label:
                raise maintain.MaintenanceError("simulated_validation_failed")

        return run

    def test_failed_candidate_validation_leaves_source_tree_untouched(self):
        fixture, payload = self.prepare_rule_increment()
        before = {
            path: (self.root / path).read_bytes()
            for path in ["research/sources.lock.json", "rules/vendor/ads-expanded.yaml", "config/stash.yaml"]
        }
        with mock.patch.object(maintain.shutil, "which", return_value="node"):
            with mock.patch.object(
                maintain, "run_step", side_effect=self.simulated_refresh_runner(payload)
            ):
                with self.assertRaises(maintain.MaintenanceError) as caught:
                    maintain.update(self.root, fixture.check())
        self.assertEqual(caught.exception.code, "simulated_validation_failed")
        self.assertEqual(git(self.root, "status", "--porcelain"), "")
        for path, body in before.items():
            self.assertEqual((self.root / path).read_bytes(), body)
        self.assertFalse((self.root / ".local/maintenance/latest-backup.json").exists())

    def test_second_download_must_match_checked_hash(self):
        fixture, payload = self.prepare_rule_increment()
        with mock.patch.object(maintain.shutil, "which", return_value="node"):
            with mock.patch.object(
                maintain, "run_step",
                side_effect=self.simulated_refresh_runner(payload, reported_hash="0" * 64),
            ):
                with self.assertRaises(maintain.MaintenanceError) as caught:
                    maintain.update(self.root, fixture.check())
        self.assertEqual(caught.exception.code, "source_changed_after_check")
        self.assertEqual(git(self.root, "status", "--porcelain"), "")
        self.assertFalse((self.root / ".local/maintenance/latest-backup.json").exists())

    def test_comments_only_update_keeps_source_tree_and_pins(self):
        fixture, payload = self.prepare_rule_increment()
        original = (self.root / "rules/vendor/ads-expanded.yaml").read_bytes()
        comments = b"# changed upstream publication date only\n" + original
        fixture.data[public_url(RULE_REPO, NEW_REVISION, fixture.rule_path)] = comments
        runner = self.simulated_refresh_runner(comments, fail_label="build")
        with mock.patch.object(maintain.shutil, "which", return_value="node"):
            with mock.patch.object(maintain, "run_step", side_effect=runner):
                self.assertIsNone(maintain.update(self.root, fixture.check()))
        self.assertEqual(git(self.root, "status", "--porcelain"), "")
        self.assertEqual((self.root / "rules/vendor/ads-expanded.yaml").read_bytes(), original)
        report = json.loads((self.root / ".local/maintenance/latest.json").read_text(encoding="utf-8"))
        self.assertEqual(report["update"]["status"], "no_semantic_rule_changes")


if __name__ == "__main__":
    unittest.main()
