"""Tests for lcg_pipeline.manager (OutputDir, PathManager, get_newest)."""

import json
import os
import time
from pathlib import Path

import pytest

from lcg_pipeline import scaffold
from lcg_pipeline.manager import OutputDir, PathManager, get_newest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_task(tmp_path: Path, proj: str = "01 Test Project", task: str = "11_Test") -> Path:
    """Build a minimal task directory tree and return the task root."""
    task_root = tmp_path / proj / "03 Technical Work" / task
    task_root.mkdir(parents=True)
    scaffold.build_task(task_root, proj, task)
    return task_root


# ---------------------------------------------------------------------------
# OutputDir
# ---------------------------------------------------------------------------

class TestOutputDir:
    def test_fspath_creates_parent(self, tmp_path):
        target = tmp_path / "subdir" / "file.png"
        od = OutputDir(target)
        result = os.fspath(od)
        assert (tmp_path / "subdir").is_dir()
        assert result == str(target)

    def test_str_creates_parent(self, tmp_path):
        target = tmp_path / "nested" / "deep" / "file.csv"
        od = OutputDir(target)
        str(od)
        assert (tmp_path / "nested" / "deep").is_dir()

    def test_truediv_returns_output_dir(self, tmp_path):
        base = OutputDir(tmp_path / "base")
        child = base / "subdir" / "file.png"
        assert isinstance(child, OutputDir)

    def test_truediv_chain_creates_parents(self, tmp_path):
        base = OutputDir(tmp_path / "base")
        child = base / "scatter" / "chart.png"
        os.fspath(child)
        assert (tmp_path / "base" / "scatter").is_dir()

    def test_getitem_returns_output_dir(self, tmp_path):
        base = OutputDir(tmp_path / "base")
        child = base["scatter/chart.png"]
        assert isinstance(child, OutputDir)

    def test_getitem_compact_path(self, tmp_path):
        base = OutputDir(tmp_path / "base")
        child = base["scatter/chart.png"]
        os.fspath(child)
        assert (tmp_path / "base" / "scatter").is_dir()

    def test_getitem_chaining(self, tmp_path):
        base = OutputDir(tmp_path / "base")
        child = base["scatter"]["chart.png"]
        os.fspath(child)
        assert (tmp_path / "base" / "scatter").is_dir()


# ---------------------------------------------------------------------------
# get_newest
# ---------------------------------------------------------------------------

class TestGetNewest:
    def test_returns_newest_file(self, tmp_path):
        (tmp_path / "a.csv").write_text("a")
        time.sleep(0.05)
        b = tmp_path / "b.csv"
        b.write_text("b")
        assert get_newest(tmp_path, "*.csv") == b

    def test_raises_if_no_match(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            get_newest(tmp_path, "*.csv")

    def test_non_recursive(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "nested.csv").write_text("n")
        (tmp_path / "top.csv").write_text("t")
        result = get_newest(tmp_path, "*.csv", recursive=False)
        assert result == tmp_path / "top.csv"


# ---------------------------------------------------------------------------
# PathManager
# ---------------------------------------------------------------------------

class TestPathManager:
    def test_technical_is_task_root(self, tmp_path):
        task_root = _make_task(tmp_path)
        pm = PathManager(config_path=task_root / "lcg.toml")
        assert pm.technical == task_root

    def test_project_resolution(self, tmp_path):
        task_root = _make_task(tmp_path, proj="01 Test Project")
        pm = PathManager(config_path=task_root / "lcg.toml")
        assert pm.project == tmp_path / "01 Test Project"

    def test_standard_dirs(self, tmp_path):
        task_root = _make_task(tmp_path)
        pm = PathManager(config_path=task_root / "lcg.toml")
        assert pm.raw_data == task_root / "02_raw_data"
        assert pm.processed == task_root / "03_processed_data"
        assert pm.figures == task_root / "04_figures"
        assert pm.scripts == task_root / "01_scripts"
        assert pm.models == task_root / "05_models"
        assert pm.metadata == task_root / "03_processed_data" / "60_METADATA"

    def test_output_returns_output_dir(self, tmp_path):
        task_root = _make_task(tmp_path)
        pm = PathManager(config_path=task_root / "lcg.toml")
        assert isinstance(pm.output, OutputDir)
        assert isinstance(pm.figs_out, OutputDir)
        assert isinstance(pm.models_out, OutputDir)

    def test_output_dir_is_created(self, tmp_path):
        task_root = _make_task(tmp_path)
        pm = PathManager(config_path=task_root / "lcg.toml")
        out = pm.output
        # The dated base dir is created eagerly
        assert Path(str(out)).parent.exists()

    def test_named_path_resolution(self, tmp_path):
        task_root = _make_task(tmp_path)
        # Append a [paths] entry to the config
        config_path = task_root / "lcg.toml"
        config_path.write_text(
            config_path.read_text() + '\n[paths]\nraw_0 = "02_raw_data/subfolder"\n'
        )
        pm = PathManager(config_path=config_path)
        assert pm["raw_0"] == (task_root / "02_raw_data" / "subfolder").resolve()
        assert pm.path("raw_0") == pm["raw_0"]

    def test_named_path_missing_raises(self, tmp_path):
        task_root = _make_task(tmp_path)
        pm = PathManager(config_path=task_root / "lcg.toml")
        with pytest.raises(KeyError):
            pm.path("nonexistent")

    def test_conn(self, tmp_path):
        task_root = _make_task(tmp_path)
        config_path = task_root / "lcg.toml"
        config_path.write_text(
            config_path.read_text()
            + '\n[connections]\ndb_0 = "postgresql://localhost/test"\n'
        )
        pm = PathManager(config_path=config_path)
        assert pm.conn("db_0") == "postgresql://localhost/test"
        assert pm["db_0"] == "postgresql://localhost/test"

    def test_load_meta_json(self, tmp_path):
        task_root = _make_task(tmp_path)
        meta_file = task_root / "03_processed_data" / "60_METADATA" / "colours.json"
        data = {"site_id": {"MW-01": "#1f77b4"}}
        meta_file.write_text(json.dumps(data))
        pm = PathManager(config_path=task_root / "lcg.toml")
        result = pm.load_meta("colours.json")
        assert result == data

    def test_load_meta_subdir(self, tmp_path):
        task_root = _make_task(tmp_path)
        sub = task_root / "03_processed_data" / "60_METADATA" / "aesthetics"
        sub.mkdir()
        meta_file = sub / "colours.json"
        data = {"site_id": {"MW-01": "#1f77b4"}}
        meta_file.write_text(json.dumps(data))
        pm = PathManager(config_path=task_root / "lcg.toml")
        result = pm.load_meta("aesthetics/colours.json")
        assert result == data

    def test_load_meta_missing_raises(self, tmp_path):
        task_root = _make_task(tmp_path)
        pm = PathManager(config_path=task_root / "lcg.toml")
        with pytest.raises(FileNotFoundError):
            pm.load_meta("nonexistent.json")

    def test_project_dir_not_in_path_raises(self, tmp_path):
        task_root = _make_task(tmp_path, proj="01 Test Project")
        config_path = task_root / "lcg.toml"
        # Overwrite with a wrong project dir
        config_path.write_text(
            '[project]\ndir = "99 Wrong Project"\n[task]\ndir = "11_Test"\n'
        )
        pm = PathManager(config_path=config_path)
        with pytest.raises(ValueError):
            _ = pm.project
