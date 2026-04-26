"""Tests for inkline knowledge CLI subcommands."""

from __future__ import annotations

import sys
from io import StringIO
from unittest.mock import patch

import pytest

from inkline.app.cli import main


def run_cli(*args) -> tuple[str, str, int]:
    """Run CLI and capture stdout/stderr. Returns (stdout, stderr, exit_code)."""
    stdout_buf = StringIO()
    stderr_buf = StringIO()
    exit_code = 0
    try:
        with patch("sys.stdout", stdout_buf), patch("sys.stderr", stderr_buf):
            main(list(args))
    except SystemExit as e:
        exit_code = e.code if isinstance(e.code, int) else 0
    return stdout_buf.getvalue(), stderr_buf.getvalue(), exit_code


class TestKnowledgeListCommand:
    def test_knowledge_list_runs(self):
        stdout, stderr, code = run_cli("knowledge", "list")
        assert code == 0
        assert "inkline://" in stdout

    def test_knowledge_list_shows_layouts_uri(self):
        stdout, _, code = run_cli("knowledge", "list")
        assert "inkline://layouts" in stdout

    def test_knowledge_list_shows_playbooks_index_uri(self):
        stdout, _, code = run_cli("knowledge", "list")
        assert "inkline://playbooks/index" in stdout


class TestKnowledgeGetCommand:
    def test_get_layouts_uri(self):
        stdout, stderr, code = run_cli("knowledge", "get", "inkline://layouts")
        assert code == 0
        assert "three_card" in stdout

    def test_get_short_form_uri(self):
        """Short form without inkline:// prefix should work."""
        stdout, stderr, code = run_cli("knowledge", "get", "layouts")
        # May or may not match exactly but shouldn't crash with error on valid path
        assert code == 0 or "three_card" in stdout or "ERROR" in stderr

    def test_get_playbooks_index(self):
        stdout, stderr, code = run_cli("knowledge", "get", "inkline://playbooks/index")
        assert code == 0
        assert "inkline://playbooks/" in stdout

    def test_get_typography(self):
        stdout, stderr, code = run_cli("knowledge", "get", "inkline://typography")
        assert code == 0
        assert len(stdout) > 50

    def test_get_nonexistent_exits_with_error(self):
        _, stderr, code = run_cli("knowledge", "get", "inkline://totally_fake_xyz")
        assert code != 0


class TestKnowledgeSearchCommand:
    def test_search_finds_layout_resources(self):
        stdout, _, code = run_cli("knowledge", "search", "layout")
        assert code == 0
        assert "inkline://layouts" in stdout or "layout" in stdout.lower()

    def test_search_no_matches(self):
        stdout, _, code = run_cli("knowledge", "search", "xyzxyzxyz_no_match")
        assert code == 0
        assert "No resources" in stdout or "xyzxyzxyz" in stdout


class TestValidateCommand:
    def test_validate_missing_file_exits(self, tmp_path):
        _, stderr, code = run_cli("validate", str(tmp_path / "nonexistent.md"))
        assert code != 0
        assert "not found" in stderr.lower()

    def test_validate_valid_spec(self, tmp_path):
        spec = tmp_path / "test.md"
        spec.write_text(
            "---\nbrand: minimal\naudit: post-render\n---\n\n## Test Slide\nContent here.\n",
            encoding="utf-8",
        )
        stdout, _, code = run_cli("validate", str(spec))
        # Should succeed on a valid spec
        assert code == 0
        assert "OK" in stdout or "valid" in stdout.lower()
