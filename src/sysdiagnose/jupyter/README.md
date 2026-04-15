# Sysdiagnose Jupyter Plugin

Interactive forensic analysis of iOS sysdiagnose data in Jupyter notebooks.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
  - [Design Rationale](#design-rationale)
  - [Alternatives Considered](#alternatives-considered)
  - [Module Structure](#module-structure)
- [Installation](#installation)
- [Quickstart](#quickstart)
- [Magic Commands Reference](#magic-commands-reference)
  - [Case Management](#case-management)
  - [Parsing and Analysis](#parsing-and-analysis)
  - [Loading Results](#loading-results)
- [Python API Reference](#python-api-reference)
  - [sysdiagnose.jupyter](#sysdiagnosejupyter)
  - [sysdiagnose.jupyter.display](#sysdiagnosejupyterdisplay)
  - [sysdiagnose.jupyter.viz](#sysdiagnosejupyterviz)
- [Visualization Guide](#visualization-guide)
  - [Event Timeline](#event-timeline)
  - [Event Density](#event-density)
  - [Time Gap Detection](#time-gap-detection)
  - [WiFi Geolocation Map](#wifi-geolocation-map)
- [Data Format](#data-format)
- [Configuration](#configuration)
- [Example Notebook](#example-notebook)
- [Extending the Plugin](#extending-the-plugin)

---

## Overview

The Jupyter plugin for the Sysdiagnose Analysis Framework (SAF) provides an interactive environment for iOS forensic analysis. It bridges the existing CLI-based sysdiagnose tooling with the Jupyter notebook ecosystem, enabling analysts to:

- Manage cases, run parsers, and execute analysers interactively
- Load all parser/analyser output as pandas DataFrames
- Visualize event timelines, detect time gaps, and render geolocation data on maps
- Leverage the full pandas/matplotlib/seaborn ecosystem for ad-hoc forensic queries

## Architecture

### Design Rationale

Three architectural approaches were evaluated:

1. **Magic Commands Only** — Wrap the CLI with IPython magics. Minimal code, but limited programmatic access.
2. **ipywidgets Dashboard** — Interactive widgets for case/parser selection. Rich UX, but heavy and opinionated.
3. **Hybrid: Magic + Python API** — Thin magic layer for convenience, full Python API for power users, rich DataFrame output as the common data format. ✅ **Selected.**

Approach 3 was chosen because:

- **Forensic analysts need flexibility.** A fixed dashboard cannot anticipate every query. DataFrames are the natural "lingua franca" of Jupyter — once data is in a DataFrame, the entire Python data science ecosystem is available (filtering, groupby, correlation, export to CSV/Excel, plotting with any library).
- **Minimal new code.** The plugin is a thin adapter layer over the existing `Sysdiagnose` class. No duplication of parsing/analysis logic.
- **Progressive disclosure.** Beginners use `%sd parse ps` and get a table. Advanced users import functions directly and build custom pipelines.

### Alternatives Considered

| Approach | Pros | Cons |
|----------|------|------|
| Magic commands only | ~50 lines of code | No programmatic API, no visualization |
| ipywidgets dashboard | Point-and-click UX | Heavy dependency, rigid workflow, harder to maintain |
| **Hybrid (selected)** | Best of both, DataFrame-native | Slightly more code than magics-only |

### Module Structure

```
src/sysdiagnose/jupyter/
├── __init__.py      # Extension loader (%load_ext entry point), get_sd() helper
├── magic.py         # %sd IPython magic commands
├── display.py       # DataFrame converters for cases, parsers, analysers, results
└── viz.py           # Timeline, density, time-gap, and map visualizations

notebooks/
└── getting_started.ipynb   # Example notebook demonstrating the full workflow
```

Dependencies are isolated as an optional extra in `pyproject.toml`:

```toml
[project.optional-dependencies]
jupyter = [
  "jupyter>=1.0.0",
  "ipython>=8.0.0",
  "folium>=0.14.0",
]
```

Core sysdiagnose remains lightweight — the Jupyter extras are only needed when running in notebooks.

## Installation

```bash
# From the sysdiagnose project root
pip install -e ".[jupyter]"
```

Or if installing from a release:

```bash
pip install sysdiagnose[jupyter]
```

Verify the installation:

```bash
python -c "from sysdiagnose.jupyter import load_ipython_extension; print('OK')"
```

## Quickstart

```python
# In a Jupyter notebook cell:
%load_ext sysdiagnose.jupyter

# List cases
%sd cases

# Select a case
%sd use 1

# Run a parser — result is auto-loaded as a DataFrame
%sd parse shutdownlogs

# The DataFrame is now available as sd_shutdownlogs and _sd_result
sd_shutdownlogs.head()

# Filter for suspicious processes
sd_shutdownlogs[sd_shutdownlogs['data.command'].str.contains('staging', na=False)]
```

## Magic Commands Reference

All magic commands use the `%sd` prefix.

### Case Management

| Command | Description |
|---------|-------------|
| `%sd cases` | List all cases as a DataFrame |
| `%sd use <case_id>` | Set the active case for subsequent commands |
| `%sd info` | Show metadata for the active case |

### Parsing and Analysis

| Command | Description |
|---------|-------------|
| `%sd parsers` | List available parsers |
| `%sd analysers` | List available analysers |
| `%sd parse <name>` | Run a parser on the active case, auto-load result |
| `%sd parse all` | Run all parsers on the active case |
| `%sd analyse <name>` | Run an analyser on the active case, auto-load result |
| `%sd analyse all` | Run all analysers on the active case |

### Loading Results

| Command | Description |
|---------|-------------|
| `%sd load <name>` | Load a cached parser/analyser result as a DataFrame |
| `%sd help` | Show help text |

When `%sd parse`, `%sd analyse`, or `%sd load` completes, the resulting DataFrame is stored in two notebook variables:

- `sd_<name>` — e.g. `sd_ps`, `sd_shutdownlogs`, `sd_timesketch`
- `_sd_result` — always points to the most recently loaded result

## Python API Reference

### sysdiagnose.jupyter

```python
from sysdiagnose.jupyter import get_sd
```

**get_sd() → Sysdiagnose**

Returns the shared `Sysdiagnose` instance used by the Jupyter extension. If the extension has been loaded via `%load_ext`, this returns the same instance used by the magic commands (preserving the active case context). Otherwise, creates a new instance.

### sysdiagnose.jupyter.display

```python
from sysdiagnose.jupyter.display import (
    cases_to_df, parsers_to_df, analysers_to_df,
    case_info_to_df, result_to_df, load_result_file,
)
```

| Function | Signature | Description |
|----------|-----------|-------------|
| `cases_to_df` | `(sd: Sysdiagnose) → DataFrame` | All cases with metadata columns |
| `parsers_to_df` | `(sd: Sysdiagnose) → DataFrame` | Available parsers (name, description) |
| `analysers_to_df` | `(sd: Sysdiagnose) → DataFrame` | Available analysers (name, description) |
| `case_info_to_df` | `(sd: Sysdiagnose, case_id: str) → DataFrame` | Single-row case metadata |
| `result_to_df` | `(parsed_folder: str, name: str) → DataFrame \| None` | Load a parser/analyser result by name |
| `load_result_file` | `(filepath: str, fmt: str) → DataFrame` | Load a specific json/jsonl file |

**JSONL flattening:** Event-based JSONL records (the standard sysdiagnose output format) contain a nested `data` dict. The loader flattens these into top-level columns with a `data.` prefix:

```
# Original JSONL record:
{"datetime": "...", "module": "shutdownlogs", "data": {"command": "/usr/sbin/cfprefsd", "pid": 42}}

# Resulting DataFrame columns:
datetime | module | message | timestamp_desc | data.command | data.pid
```

This avoids column name collisions while keeping the data accessible for pandas operations.

### sysdiagnose.jupyter.viz

```python
from sysdiagnose.jupyter.viz import (
    plot_timeline, plot_event_density, plot_time_gaps, plot_wifi_map,
)
```

| Function | Signature | Description |
|----------|-----------|-------------|
| `plot_timeline` | `(df, datetime_col='datetime', color_col='module', title='Event Timeline', figsize=(16,6)) → Figure` | Scatter plot of events over time, color-coded by module |
| `plot_event_density` | `(df, datetime_col='datetime', freq='1h', title='Event Density', figsize=(16,4)) → Figure` | Histogram of event counts per time bucket |
| `plot_time_gaps` | `(df, datetime_col='datetime', min_gap_minutes=30, figsize=(16,4)) → DataFrame` | Detect and visualize gaps in event data |
| `plot_wifi_map` | `(df, lat_col='latitude', lon_col='longitude', label_col='ssid') → folium.Map` | Interactive map of WiFi geolocations |

## Visualization Guide

### Event Timeline

Scatter plot showing when events occurred, color-coded by source module. Useful for getting an overview of activity patterns.

```python
from sysdiagnose.jupyter.viz import plot_timeline
from sysdiagnose.jupyter.display import result_to_df

df = result_to_df(parsed_folder, 'logarchive')
plot_timeline(df, title='Logarchive Events')
```

### Event Density

Histogram showing how many events occurred per time bucket. Spikes may indicate automated activity; drops may indicate tampering.

```python
from sysdiagnose.jupyter.viz import plot_event_density

plot_event_density(df, freq='1h', title='Events per Hour')
plot_event_density(df, freq='15min', title='Events per 15 Minutes')
```

The `freq` parameter accepts any pandas frequency string: `'1h'`, `'15min'`, `'1D'`, `'6h'`, etc.

### Time Gap Detection

Identifies periods where no events were logged. Gaps can indicate device shutdown, airplane mode, or log tampering. This is directly relevant to the forensic analysis workflow described in the forensic notes.

```python
from sysdiagnose.jupyter.viz import plot_time_gaps

gaps = plot_time_gaps(df, min_gap_minutes=30)
gaps  # DataFrame with gap_start, gap_end, gap_minutes columns
```

> **Note:** Gaps of approximately 720 minutes are normal for `battery_bdc` reporting cycles.

### WiFi Geolocation Map

Renders WiFi geolocation data on an interactive Leaflet map via folium. Requires the `wifi_geolocation` analyser to have been run first.

```python
from sysdiagnose.jupyter.viz import plot_wifi_map

df_wifi = result_to_df(parsed_folder, 'wifi_geolocation')
plot_wifi_map(df_wifi)
```

The map renders inline in Jupyter and supports zoom, pan, and marker popups.

## Data Format

All sysdiagnose parsers output either JSON or JSONL files in the `<cases>/<case_id>/parsed_data/` folder.

- **JSONL** (event-based): Each line is a JSON object with `datetime`, `message`, `module`, `timestamp_desc`, and `data` fields. These are the primary format for timeline-capable data.
- **JSON** (structured): A single JSON object or array. Used for non-temporal data like device info or process lists.

The Jupyter display module handles both formats transparently. JSONL files are sorted by `datetime` after loading, and the `datetime` column is converted to pandas `Timestamp` with UTC timezone.

## Configuration

The cases folder defaults to `./cases` relative to the notebook's working directory. Override it with the `SYSDIAGNOSE_CASES_PATH` environment variable:

```python
import os
os.environ['SYSDIAGNOSE_CASES_PATH'] = '/path/to/your/cases'

%load_ext sysdiagnose.jupyter
```

Or set it before launching Jupyter:

```bash
export SYSDIAGNOSE_CASES_PATH='/path/to/your/cases'
jupyter notebook
```

## Example Notebook

A complete example notebook is provided at `notebooks/getting_started.ipynb`. It demonstrates:

1. Loading the extension
2. Listing and selecting cases
3. Running parsers and viewing results as DataFrames
4. Timeline visualization
5. Event density analysis
6. Time gap detection
7. WiFi geolocation mapping
8. Filtering for suspicious processes (e.g. processes in `/private/var/db/com.apple.xpc.roleaccountd.staging`)

## Extending the Plugin

### Adding new visualizations

Add functions to `viz.py`. Follow the existing pattern:

1. Accept a DataFrame and column name parameters with sensible defaults
2. Validate that required columns exist
3. Return the matplotlib Figure or folium Map object (so Jupyter renders it inline)

### Adding new display converters

Add functions to `display.py`. The convention is:

- `<thing>_to_df(...)` for converting sysdiagnose objects to DataFrames
- `result_to_df(parsed_folder, name)` for loading output files

### Adding new magic commands

Extend the dispatch dict in `SysdiagnoseMagic.sd()` and add a corresponding `_cmd_<name>` method.
