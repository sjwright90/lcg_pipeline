# lcg_pipeline

Python package for LCG project pipeline management. Handles directory scaffolding and all path resolution for project and task folders, replacing ad-hoc `.bat` scripts and copy-pasted path headers.

---

## Contents

- [Installation](#installation)
- [Quick start](#quick-start)
- [CLI — directory scaffolding](#cli--directory-scaffolding)
- [PathManager API](#pathmanager-api)
- [lcg.toml config reference](#lcgtoml-config-reference)
- [Directory structure conventions](#directory-structure-conventions)
- [Dependencies & requirements](#dependencies--requirements)
- [Development](#development)
- [Versioning](#versioning)

---

## Installation

Install directly from GitHub (no PyPI account needed):

```bash
# latest main
pip install git+https://github.com/sjwright90/lcg_pipeline.git

# pinned to a release tag — recommended for project environments
pip install git+https://github.com/sjwright90/lcg_pipeline.git@v0.1.0
```

In a `requirements.txt`:
```
lcg-pipeline @ git+https://github.com/sjwright90/lcg_pipeline.git@v0.1.0
```

In a conda `environment.yml`:
```yaml
dependencies:
  - pip
  - pip:
    - git+https://github.com/sjwright90/lcg_pipeline.git@v0.1.0
```

**Requires Python ≥ 3.9.**

---

## Quick start

### 1. Scaffold a new project

Navigate to the new project folder and run:

```bash
python -m lcg_pipeline build base
```

This creates the standard LCG top-level folder structure (see [Directory structure conventions](#directory-structure-conventions)).

### 2. Scaffold a new task

Navigate into the task folder (inside `03 Technical Work/`) and run:

```bash
python -m lcg_pipeline build task --project "01 25NEM Water Quality"
```

`--project` is the exact name of the project root folder. The task name defaults to the current directory name. This creates the task folder structure and writes an `lcg.toml` config file.

Then edit `lcg.toml` to add named input paths and data-source connections for the task.

### 3. Use PathManager in scripts

Drop this at the top of any script inside the task folder:

```python
from lcg_pipeline import PathManager

pm = PathManager(__file__)
```

Pass `__file__` so `PathManager` knows where your script lives — it walks up from there to find `lcg.toml` and uses the script name/folder for dated output directories. No hardcoded paths needed.

In a Jupyter notebook or interactive session, pass `None` instead — discovery falls back to `Path.cwd()`:

```python
pm = PathManager(None)
```

---

## CLI — directory scaffolding

```
python -m lcg_pipeline build <type> [options]
```

| Argument | Description |
|---|---|
| `build base` | Scaffold a top-level project directory |
| `build task` | Scaffold a technical task directory and write `lcg.toml` |
| `--project NAME` | Exact name of the project root folder (required for `build task`) |
| `--task NAME` | Task folder name (defaults to the current directory name) |
| `--dir PATH` | Target directory (defaults to current working directory) |

**Examples:**

```bash
# In the project root folder:
python -m lcg_pipeline build base

# In 03 Technical Work/11_WaterQuality/:
python -m lcg_pipeline build task --project "01 25NEM Water Quality"

# Explicit paths:
python -m lcg_pipeline build task --dir "path/to/task" --project "01 25NEM Water Quality" --task "11_WaterQuality"
```

---

## PathManager API

### Initialisation

```python
from lcg_pipeline import PathManager

pm = PathManager(__file__)                            # standard use in a .py script
pm = PathManager(None)                                # Jupyter / REPL — falls back to cwd
pm = PathManager(__file__, config_path="path/to/lcg.toml")  # explicit config override
```

### Core anchor paths

```python
pm.project      # Path — project root (located by [project] dir name in the filesystem path)
pm.technical    # Path — task root (the directory containing lcg.toml)
```

### Standard task directories

```python
pm.scripts      # task/01_scripts/
pm.raw_data     # task/02_raw_data/
pm.processed    # task/03_processed_data/
pm.figures      # task/04_figures/
pm.models       # task/05_models/
pm.metadata     # task/03_processed_data/60_METADATA/
```

### Standard project directories

```python
pm.received     # project/02 Received Files/
pm.deliverables # project/04 Deliverables/
```

### Dated output directories

These are created automatically, named after the calling script and folder, and dated:
`{root}/{script_folder}/{script_name}/{YYYYMMDD}/`

They return an [`OutputDir`](#outputdir) object, not a plain `Path`.

```python
pm.output       # under 03_processed_data/
pm.figs_out     # under 04_figures/
pm.models_out   # under 05_models/
```

### OutputDir

`OutputDir` is a path-like object (works anywhere a `Path` or string path is accepted) that auto-creates parent directories on first use. Supports two syntaxes for saving into subdirectories:

```python
# Division — chains naturally
fig.savefig(pm.figs_out / "scatter" / "chart.png")
df.to_csv(pm.output / "cleaned" / "results.csv", index=False)

# Subscript — compact, full relative path in one string
fig.savefig(pm.figs_out["scatter/chart.png"])
df.to_csv(pm.output["cleaned/results.csv"], index=False)

# Store a subdir for repeated use
scatter = pm.figs_out["scatter"]
fig1.savefig(scatter["site_overview.png"])
fig2.savefig(scatter["analyte_trends.png"])
```

The `scatter/` subdirectory is created the first time any path inside it is used.

### Named paths from `lcg.toml`

File-system paths defined under `[paths]` are resolved to absolute `Path` objects relative to the task root.

```python
pm["raw_0"]         # shorthand — checks [paths] then [connections]
pm.path("raw_0")    # explicit — [paths] only, returns Path
```

### Named connections from `lcg.toml`

Non-file sources (connection strings, API URLs, environment variable names) defined under `[connections]` are returned as strings.

```python
pm.conn("db_0")         # returns the connection string as-is
pm.env("api_key_env")   # reads os.environ[config_value] — keeps secrets out of config
```

### Metadata

```python
pm.metadata                             # Path to 03_processed_data/60_METADATA/
pm.load_meta("aesthetics/colours.json") # loads and returns a dict (.json or .toml)
pm.load_meta("columns/water_quality.json")
```

### File utilities

```python
pm.newest("02_raw_data", "*.csv")              # most recently modified match (recursive)
pm.newest("02_raw_data/Labs", "*.xlsx", recursive=False)

# Module-level, no PathManager needed:
from lcg_pipeline import get_newest
get_newest(some_path, "*.csv")
```

---

## lcg.toml config reference

Written automatically by `build task`. Edit to add named paths and connections.

```toml
[project]
dir = "01 25NEM Water Quality"    # exact name of the project root folder

[task]
dir = "11_WaterQuality"           # exact name of this task folder

# ---------------------------------------------------------------------------
# File-system paths — resolved relative to task root, returned as Path objects
# Access via: pm["key"]  or  pm.path("key")
# ---------------------------------------------------------------------------
[paths]
raw_0  = "02 Received Files/Labs/2024"
raw_1  = "02 Received Files/Partners"
proc_0 = "03_processed_data/50_DB"
meta_0 = "03_processed_data/60_METADATA"

# ---------------------------------------------------------------------------
# Non-file sources — returned as strings
# Access via: pm.conn("key")  or  pm["key"]
# For secrets: store the env variable NAME here, read value with pm.env("key")
# ---------------------------------------------------------------------------
[connections]
db_0         = "postgresql://user:pass@host/dbname"
api_endpoint = "https://api.example.com/v2"
api_key_env  = "MY_API_KEY_VAR"    # pm.env("api_key_env") reads os.environ["MY_API_KEY_VAR"]
```

---

## Directory structure conventions

### Project level (`build base`)

```
<project root>/
├── 01 Project Management/
├── 02 Received Files/         ← raw client/lab data, no manipulation
├── 03 Technical Work/
│   ├── 00_RDBMS/              ← static databases shared across tasks
│   ├── 01_GIS/                ← static GIS files shared across tasks
│   ├── 10_TASKPLACEHOLDER/    ← copy/rename for each new task (11_, 12_, ...)
│   └── README.txt
├── 04 Deliverables/
├── 05 Meetings/
├── 06 References/
├── 07 Health and Safety/      ← includes HASP SharePoint link
└── README.txt
```

### Task level (`build task`)

```
<task root>/
├── 01_scripts/                ← analysis scripts
├── 02_raw_data/               ← raw inputs for this task
├── 03_processed_data/
│   ├── 60_METADATA/           ← cross-script naming & aesthetic metadata
│   └── README.txt
├── 04_figures/
├── 05_models/
├── 20_GIS/
├── 30_phreeqc/
├── 40_gwb/
├── 50_gsim/
├── 80_presentations/
└── lcg.toml                   ← pipeline config (edit after scaffolding)
```

### Scripts prefix convention (`01_scripts/`)

| Prefix | Purpose |
|---|---|
| `00_*` | Extract, clean, impute raw data |
| `01_*` | Exploratory data analysis |
| `02_*` | Unsupervised learning (development) |
| `04_*` | Supervised learning (development) |
| `05_*` | Final modelling (production) |

### Processed data prefix convention (`03_processed_data/`)

| Prefix | Purpose |
|---|---|
| `00–09` | Pipeline outputs (script-generated only) |
| `50_DB` | Static master database |
| `60_METADATA` | Cross-script metadata (column maps, aesthetics) |
| `80+` | Compiled table views for reporting |

---

## Dependencies & requirements

Runtime dependencies are declared in `pyproject.toml` — there is no separate `requirements.txt` for the package itself.

| Dependency | When |
|---|---|
| `tomli >= 2.0` | Python < 3.11 only (`tomllib` is stdlib on 3.11+) |

All other dependencies (`pathlib`, `json`, `inspect`, etc.) are Python stdlib.

**For development / running tests:**

```bash
pip install -e ".[dev]"   # installs the package + pytest
pytest
```

---

## Development

```bash
git clone https://github.com/sjwright90/lcg_pipeline.git
cd lcg_pipeline
pip install -e ".[dev]"
pytest
```

Tests live in `tests/` and cover scaffold directory creation, `OutputDir` behaviour, `PathManager` path resolution, named paths/connections, metadata loading, and error handling.

---

## Versioning

Releases are tagged on `main`. To install a specific version:

```bash
pip install git+https://github.com/sjwright90/lcg_pipeline.git@v0.2.0
```

To cut a new release:

```bash
# 1. Bump version in lcg_pipeline/__init__.py and pyproject.toml
# 2. Commit
git tag v0.2.0
git push && git push --tags
```
