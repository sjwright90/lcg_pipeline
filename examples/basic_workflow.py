"""
basic_workflow.py — end-to-end example of lcg_pipeline usage.

This file lives at:
    <project>/03 Technical Work/<task>/01_scripts/00_cleaning/basic_workflow.py

It assumes:
  1. The project was scaffolded:   python -m lcg_pipeline build base
  2. The task was scaffolded:      python -m lcg_pipeline build task --project "<project dir name>"
  3. lcg.toml has been edited to add any named paths / connections needed.
"""

# %%
from lcg_pipeline import PathManager

pm = PathManager(__file__)      # pass __file__ so lcg.toml discovery and
                                # output dir naming are anchored to this script
# In Jupyter: pm = PathManager(None)

# ── Core anchors ──────────────────────────────────────────────────────────────
print("Project root :", pm.project)
print("Task root    :", pm.technical)

# ── Standard directories (plain Path objects) ─────────────────────────────────
raw      = pm.raw_data    # 02_raw_data/
received = pm.received    # project/02 Received Files/
proc     = pm.processed   # 03_processed_data/
meta_dir = pm.metadata    # 03_processed_data/60_METADATA/

# ── Find the newest CSV in raw_data ───────────────────────────────────────────
# raw_file = pm.newest("02_raw_data", "*.csv")
# df = pd.read_csv(raw_file)

# ── Named paths from lcg.toml [paths] ────────────────────────────────────────
# Uncomment after adding to lcg.toml:
#   raw_0 = "02 Received Files/Labs/2024"
#
# raw_0_path = pm["raw_0"]           # resolves to absolute Path
# df = pd.read_csv(pm.newest(raw_0_path, "*.csv"))

# ── Named connections from lcg.toml [connections] ────────────────────────────
# Uncomment after adding to lcg.toml:
#   db_0 = "postgresql://user:pass@host/dbname"
#   api_key_env = "MY_API_KEY"
#
# conn_str = pm.conn("db_0")
# api_key  = pm.env("api_key_env")   # reads os.environ["MY_API_KEY"]

# ── Metadata ──────────────────────────────────────────────────────────────────
# aes = pm.load_meta("aesthetics/colours.json")
# mrk = pm.load_meta("aesthetics/markers.json")
# cols = pm.load_meta("columns/water_quality.json")
#
# palette = aes["site_id"]
# markers = mrk["site_id"]
# sns.scatterplot(data=df, x="date", y="conc",
#                 hue="site_id",   palette=palette,
#                 style="site_id", markers=markers)

# ── Dated output directories (OutputDir — auto-creates, supports subdirs) ─────
# pm.output   → 03_processed_data/{script_folder}/{script_name}/{YYYYMMDD}/
# pm.figs_out → 04_figures/{script_folder}/{script_name}/{YYYYMMDD}/
#
# Save a dataframe:
#   df_clean.to_csv(pm.output / "cleaned.csv", index=False)
#   df_clean.to_csv(pm.output["stage1/cleaned.csv"], index=False)
#
# Save a figure — two equivalent syntaxes:
#   fig.savefig(pm.figs_out / "overview.png", dpi=150)
#   fig.savefig(pm.figs_out["scatter/site_overview.png"], dpi=150)
