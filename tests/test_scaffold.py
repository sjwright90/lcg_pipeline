"""Tests for lcg_pipeline.scaffold (directory building)."""

from pathlib import Path

import pytest

from lcg_pipeline import scaffold
from lcg_pipeline.config import CONFIG_FILENAME, load_config


# ---------------------------------------------------------------------------
# build_base
# ---------------------------------------------------------------------------

def test_build_base_top_level_dirs(tmp_path):
    scaffold.build_base(tmp_path)
    expected = [
        "01 Project Management",
        "02 Received Files",
        "03 Technical Work",
        "04 Deliverables",
        "05 Meetings",
        "06 References",
        "07 Health and Safety",
    ]
    for name in expected:
        assert (tmp_path / name).is_dir(), f"Missing: {name}"


def test_build_base_technical_subdirs(tmp_path):
    scaffold.build_base(tmp_path)
    tech = tmp_path / "03 Technical Work"
    assert (tech / "00_RDBMS").is_dir()
    assert (tech / "01_GIS").is_dir()
    assert (tech / "10_TASKPLACEHOLDER").is_dir()


def test_build_base_hasp_shortcut(tmp_path):
    scaffold.build_base(tmp_path)
    shortcut = tmp_path / "07 Health and Safety" / "HASP Sharepoint Link.url"
    assert shortcut.exists()
    content = shortcut.read_text()
    assert "[InternetShortcut]" in content
    assert "URL=" in content


def test_build_base_readmes(tmp_path):
    scaffold.build_base(tmp_path)
    assert (tmp_path / "README.txt").exists()
    assert (tmp_path / "03 Technical Work" / "README.txt").exists()


# ---------------------------------------------------------------------------
# build_task
# ---------------------------------------------------------------------------

def test_build_task_dirs(tmp_path):
    scaffold.build_task(tmp_path, "01 Test Project", "11_TestTask")
    expected = [
        "01_scripts",
        "02_raw_data",
        "03_processed_data",
        "03_processed_data/60_METADATA",
        "04_figures",
        "05_models",
        "20_GIS",
        "30_phreeqc",
        "40_gwb",
        "50_gsim",
        "80_presentations",
    ]
    for rel in expected:
        assert (tmp_path / rel).is_dir(), f"Missing: {rel}"


def test_build_task_writes_config(tmp_path):
    scaffold.build_task(tmp_path, "01 Test Project", "11_TestTask")
    config_path = tmp_path / CONFIG_FILENAME
    assert config_path.exists()
    config = load_config(config_path)
    assert config["project"]["dir"] == "01 Test Project"
    assert config["task"]["dir"] == "11_TestTask"


def test_build_task_readmes(tmp_path):
    scaffold.build_task(tmp_path, "01 Test Project", "11_TestTask")
    assert (tmp_path / "README.txt").exists()
    assert (tmp_path / "01_scripts" / "README.txt").exists()
    assert (tmp_path / "03_processed_data" / "README.txt").exists()
    assert (tmp_path / "03_processed_data" / "60_METADATA" / "README.txt").exists()


def test_build_task_idempotent(tmp_path):
    """Running build_task twice on the same dir should not raise."""
    scaffold.build_task(tmp_path, "01 Test Project", "11_TestTask")
    scaffold.build_task(tmp_path, "01 Test Project", "11_TestTask")
