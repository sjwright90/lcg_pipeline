"""PathManager — central path and source management for an LCG task."""

import inspect
import json
import os
from datetime import datetime
from pathlib import Path

from .config import find_config, load_config


class OutputDir(os.PathLike):
    """
    A path-like object for output directories returned by PathManager.

    Parent directories are created lazily — only when the path is actually
    used (passed to ``open()``, ``fig.savefig()``, ``df.to_csv()``, etc.).

    Supports two low-friction syntaxes for subdirectory organisation::

        # division — chains naturally
        fig.savefig(pm.figs_out / "scatter" / "chart.png")

        # subscript — compact, full relative path in one string
        fig.savefig(pm.figs_out["scatter/chart.png"])

    Both create ``scatter/`` inside the dated output dir on first use.
    Subscript returns another ``OutputDir`` so further chaining works::

        sub = pm.figs_out["scatter"]        # OutputDir for the subdir
        fig.savefig(sub["chart.png"])
    """

    def __init__(self, path: Path) -> None:
        self._path = Path(path)

    # os.PathLike protocol — used by open(), matplotlib, pandas, etc.
    def __fspath__(self) -> str:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        return str(self._path)

    def __str__(self) -> str:
        return self.__fspath__()

    def __truediv__(self, other: str) -> "OutputDir":
        return OutputDir(self._path / other)

    def __getitem__(self, key: str) -> "OutputDir":
        return OutputDir(self._path / key)

    def __repr__(self) -> str:
        return f"OutputDir({self._path})"


def get_newest(path: Path, pattern: str = "*", recursive: bool = True) -> Path:
    """Return the most recently modified file matching *pattern* under *path*."""
    files = path.rglob(pattern) if recursive else path.glob(pattern)
    try:
        return max(files, key=lambda p: p.stat().st_mtime)
    except ValueError:
        raise FileNotFoundError(f"No files matching '{pattern}' in {path}")


class PathManager:
    """
    Manages all paths and data-source references for an LCG technical task.

    Discovers ``lcg.toml`` automatically by walking up the directory tree from
    the *calling script's* location — no hardcoded paths needed.

    Usage
    -----
    ::

        from lcg_pipeline import PathManager

        pm = PathManager()

        # Standard directories
        pm.project      # project root (anchored by [project] dir in lcg.toml)
        pm.technical    # task root (where lcg.toml lives)
        pm.raw_data     # task/02_raw_data/
        pm.processed    # task/03_processed_data/
        pm.figures      # task/04_figures/
        pm.scripts      # task/01_scripts/
        pm.received     # project/02 Received Files/

        # Auto-created, script-named, dated output dirs
        pm.output       # task/03_processed_data/{folder}/{script}/{date}/
        pm.figs_out     # task/04_figures/{folder}/{script}/{date}/

        # Named paths from [paths] in lcg.toml (resolved to absolute Path)
        pm["raw_0"]         # shorthand __getitem__
        pm.path("raw_0")    # explicit

        # Named connections from [connections] in lcg.toml (returned as str)
        pm.conn("db_0")         # connection string / URL
        pm.env("api_key_env")   # read env variable whose *name* is in config

        # File utilities
        pm.newest("02_raw_data", "*.csv")   # most-recently-modified match
    """

    def __init__(self, config_path: "str | Path | None" = None) -> None:
        # Capture the caller's __file__ at construction time so that dated
        # output paths are named after the *user's* script, not this module.
        frame = inspect.stack()[1]
        self._caller_file = Path(frame.filename).resolve()

        if config_path is None:
            config_path = find_config(self._caller_file.parent)
        else:
            config_path = Path(config_path).resolve()

        self._config_path = config_path
        self._config = load_config(config_path)

    # ------------------------------------------------------------------
    # Core anchor paths
    # ------------------------------------------------------------------

    @property
    def technical(self) -> Path:
        """Task root — the directory that contains ``lcg.toml``."""
        return self._config_path.parent

    @property
    def project(self) -> Path:
        """
        Project root — located by finding the project dir name (from
        ``[project] dir`` in lcg.toml) in the filesystem path.
        """
        proj_dir = self._config["project"]["dir"]
        parts = self._config_path.parts
        try:
            idx = parts.index(proj_dir)
        except ValueError:
            raise ValueError(
                f"Project dir '{proj_dir}' not found in path '{self._config_path}'. "
                "Check [project] dir = ... in lcg.toml."
            )
        return Path(*parts[: idx + 1])

    # ------------------------------------------------------------------
    # Standard task-level directories
    # ------------------------------------------------------------------

    @property
    def scripts(self) -> Path:
        """``01_scripts/`` inside the task root."""
        return self.technical / "01_scripts"

    @property
    def raw_data(self) -> Path:
        """``02_raw_data/`` inside the task root."""
        return self.technical / "02_raw_data"

    @property
    def processed(self) -> Path:
        """``03_processed_data/`` inside the task root."""
        return self.technical / "03_processed_data"

    @property
    def figures(self) -> Path:
        """``04_figures/`` inside the task root."""
        return self.technical / "04_figures"

    @property
    def models(self) -> Path:
        """``05_models/`` inside the task root."""
        return self.technical / "05_models"

    # ------------------------------------------------------------------
    # Standard project-level directories
    # ------------------------------------------------------------------

    @property
    def received(self) -> Path:
        """``02 Received Files/`` at the project root level."""
        return self.project / "02 Received Files"

    @property
    def deliverables(self) -> Path:
        """``04 Deliverables/`` at the project root level."""
        return self.project / "04 Deliverables"

    # ------------------------------------------------------------------
    # Metadata directory
    # ------------------------------------------------------------------

    @property
    def metadata(self) -> Path:
        """``03_processed_data/60_METADATA/`` — column maps, aesthetics, etc."""
        return self.technical / "03_processed_data" / "60_METADATA"

    def load_meta(self, filename: str) -> dict:
        """
        Load a metadata file from ``60_METADATA/`` and return its contents
        as a dict.

        Supports ``.json`` and ``.toml``. Subdirectory paths are fine::

            pm.load_meta("aesthetics.json")
            pm.load_meta("columns/water_quality.json")
            pm.load_meta("groups.toml")
        """
        path = self.metadata / filename
        if not path.exists():
            raise FileNotFoundError(
                f"Metadata file not found: {path}\n"
                f"Place it under {self.metadata}"
            )
        suffix = path.suffix.lower()
        if suffix == ".json":
            return json.loads(path.read_text(encoding="utf-8"))
        if suffix in (".toml", ".tml"):
            return load_config(path)
        raise ValueError(
            f"Unsupported metadata format '{suffix}' for {path}. "
            "Use .json or .toml"
        )

    # ------------------------------------------------------------------
    # Dated, script-named output directories (auto-created on access)
    # ------------------------------------------------------------------

    def _dated_output(self, root: Path) -> OutputDir:
        """
        Build and mkdir: ``root/{parent_folder}/{script_stem}/{YYYYMMDD}/``

        The folder and script name are taken from the *calling* script so
        that outputs are automatically organised without manual configuration.
        Returns an :class:`OutputDir` so subdirectory saves are zero-friction.
        """
        folder = self._caller_file.parent.stem
        script = self._caller_file.stem
        date = datetime.now().strftime("%Y%m%d")
        path = root / folder / script / date
        path.mkdir(parents=True, exist_ok=True)
        return OutputDir(path)

    @property
    def output(self) -> OutputDir:
        """Auto-created output dir under ``03_processed_data/``.

        Examples::

            df.to_csv(pm.output / "results.csv")
            df.to_csv(pm.output["cleaned/results.csv"])
        """
        return self._dated_output(self.processed)

    @property
    def figs_out(self) -> OutputDir:
        """Auto-created output dir under ``04_figures/``.

        Examples::

            fig.savefig(pm.figs_out / "chart.png")
            fig.savefig(pm.figs_out["scatter/chart.png"])
            fig.savefig(pm.figs_out["scatter"]["chart.png"])
        """
        return self._dated_output(self.figures)

    @property
    def models_out(self) -> OutputDir:
        """Auto-created output dir under ``05_models/``."""
        return self._dated_output(self.models)

    # ------------------------------------------------------------------
    # Named paths and connections from lcg.toml
    # ------------------------------------------------------------------

    def path(self, key: str) -> Path:
        """
        Resolve a named file-system path from ``[paths]`` in lcg.toml.

        The stored value is treated as relative to the task root and returned
        as an absolute ``Path``.
        """
        section = self._config.get("paths", {})
        if key not in section:
            raise KeyError(
                f"No path '{key}' in [paths] section of {self._config_path}. "
                "Add it as:  key = \"relative/path\""
            )
        return (self.technical / section[key]).resolve()

    def conn(self, key: str) -> str:
        """
        Return a named entry from ``[connections]`` in lcg.toml as a string.

        Use this for connection strings, API base URLs, or environment
        variable *names* (see :meth:`env`).
        """
        section = self._config.get("connections", {})
        if key not in section:
            raise KeyError(
                f"No connection '{key}' in [connections] section of {self._config_path}. "
                "Add it as:  key = \"value\""
            )
        return section[key]

    def env(self, key: str) -> str:
        """
        Read an environment variable whose *name* is stored in ``[connections]``.

        This lets you keep API keys and secrets out of the config file::

            # lcg.toml
            [connections]
            api_key_env = "MY_API_KEY"

            # script
            token = pm.env("api_key_env")  # reads os.environ["MY_API_KEY"]
        """
        var_name = self.conn(key)
        value = os.environ.get(var_name)
        if value is None:
            raise EnvironmentError(
                f"Environment variable '{var_name}' (referenced by '{key}' in "
                f"{self._config_path}) is not set."
            )
        return value

    def __getitem__(self, key: str) -> "Path | str":
        """
        Shorthand accessor: checks ``[paths]`` then ``[connections]``.

        Returns a resolved ``Path`` for file-system paths, or a ``str``
        for connection entries.
        """
        paths = self._config.get("paths", {})
        if key in paths:
            return (self.technical / paths[key]).resolve()
        conns = self._config.get("connections", {})
        if key in conns:
            return conns[key]
        raise KeyError(
            f"'{key}' not found in [paths] or [connections] in {self._config_path}"
        )

    # ------------------------------------------------------------------
    # File utilities
    # ------------------------------------------------------------------

    def newest(
        self, rel_path: str, pattern: str = "*", recursive: bool = True
    ) -> Path:
        """
        Find the most recently modified file matching *pattern*.

        *rel_path* is relative to the task root (i.e. ``self.technical``).

        Examples::

            pm.newest("02_raw_data", "*.csv")
            pm.newest("02_raw_data/Labs", "*.xlsx", recursive=False)
        """
        return get_newest(self.technical / rel_path, pattern, recursive)

    # ------------------------------------------------------------------
    # Repr / str
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        lines = [
            "PathManager",
            f"  config    : {self._config_path}",
            f"  project   : {self.project}",
            f"  technical : {self.technical}",
            f"  caller    : {self._caller_file}",
        ]
        paths = self._config.get("paths", {})
        if paths:
            lines.append("  [paths]")
            for k, v in paths.items():
                lines.append(f"    {k} = {v}")
        conns = self._config.get("connections", {})
        if conns:
            lines.append("  [connections]")
            for k, v in conns.items():
                lines.append(f"    {k} = {v}")
        return "\n".join(lines)
