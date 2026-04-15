#! /usr/bin/env python3

# Sysdiagnose Jupyter visualization helpers
# Author: EC-DIGIT-CSIRC

"""
Visualization helpers for sysdiagnose Jupyter integration.

Provides timeline plotting and geolocation map rendering
using matplotlib and folium.
"""
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from sysdiagnose.utils.logger import logger


def plot_timeline(df: pd.DataFrame, datetime_col: str = 'datetime',
                  color_col: str = 'module', title: str = 'Event Timeline',
                  figsize: tuple = (16, 6)):
    """
    Plot an event timeline from a DataFrame.

    Args:
        df: DataFrame with a datetime column.
        datetime_col: Name of the datetime column.
        color_col: Column to use for color-coding events.
        title: Plot title.
        figsize: Figure size tuple.

    Returns:
        matplotlib Figure, or None if no valid data.
    """
    if datetime_col not in df.columns:
        logger.warning(f"Column '{datetime_col}' not found. Available: {list(df.columns)}")
        return None

    plot_df = df.dropna(subset=[datetime_col]).copy()
    if plot_df.empty:
        logger.warning("No valid datetime entries to plot.")
        return None

    plot_df[datetime_col] = pd.to_datetime(plot_df[datetime_col], errors='coerce', utc=True)
    plot_df = plot_df.dropna(subset=[datetime_col])

    fig, ax = plt.subplots(figsize=figsize)

    if color_col and color_col in plot_df.columns:
        groups = plot_df.groupby(color_col)
        for name, group in groups:
            ax.scatter(group[datetime_col], [name] * len(group), label=name, alpha=0.6, s=10)
        ax.set_ylabel('Module')
    else:
        ax.scatter(plot_df[datetime_col], range(len(plot_df)), alpha=0.6, s=10)
        ax.set_ylabel('Event index')

    ax.set_xlabel('Time')
    ax.set_title(title)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
    fig.autofmt_xdate()
    plt.tight_layout()
    return fig


def plot_event_density(df: pd.DataFrame, datetime_col: str = 'datetime',
                       freq: str = '1h', title: str = 'Event Density',
                       figsize: tuple = (16, 4)):
    """
    Plot event density over time (histogram of events per time bucket).

    Args:
        df: DataFrame with a datetime column.
        datetime_col: Name of the datetime column.
        freq: Pandas frequency string for bucketing (e.g. '1h', '15min', '1D').
        title: Plot title.
        figsize: Figure size tuple.

    Returns:
        matplotlib Figure, or None if no valid data.
    """
    if datetime_col not in df.columns:
        logger.warning(f"Column '{datetime_col}' not found.")
        return None

    plot_df = df.dropna(subset=[datetime_col]).copy()
    plot_df[datetime_col] = pd.to_datetime(plot_df[datetime_col], errors='coerce', utc=True)
    plot_df = plot_df.dropna(subset=[datetime_col]).set_index(datetime_col)

    counts = plot_df.resample(freq).size()

    fig, ax = plt.subplots(figsize=figsize)
    counts.plot(kind='bar', ax=ax, width=1.0, edgecolor='none', alpha=0.7)
    ax.set_title(title)
    ax.set_xlabel('Time')
    ax.set_ylabel('Event count')

    n_ticks = min(20, len(counts))
    step = max(1, len(counts) // n_ticks)
    ax.set_xticks(range(0, len(counts), step))
    ax.set_xticklabels([str(counts.index[i])[:16] for i in range(0, len(counts), step)], rotation=45, ha='right')

    plt.tight_layout()
    return fig


def plot_time_gaps(df: pd.DataFrame, datetime_col: str = 'datetime',
                   min_gap_minutes: int = 30, figsize: tuple = (16, 4)):
    """
    Identify and plot time gaps in event data.

    Args:
        df: DataFrame with a datetime column.
        datetime_col: Name of the datetime column.
        min_gap_minutes: Minimum gap in minutes to highlight.
        figsize: Figure size tuple.

    Returns:
        DataFrame of gaps found, or None if datetime column is missing.
    """
    if datetime_col not in df.columns:
        logger.warning(f"Column '{datetime_col}' not found.")
        return None

    plot_df = df.dropna(subset=[datetime_col]).copy()
    plot_df[datetime_col] = pd.to_datetime(plot_df[datetime_col], errors='coerce', utc=True)
    plot_df = plot_df.dropna(subset=[datetime_col]).sort_values(datetime_col).reset_index(drop=True)

    plot_df['prev_time'] = plot_df[datetime_col].shift(1)
    plot_df['gap_minutes'] = (plot_df[datetime_col] - plot_df['prev_time']).dt.total_seconds() / 60
    gaps = plot_df[plot_df['gap_minutes'] > min_gap_minutes][['prev_time', datetime_col, 'gap_minutes']].copy()
    gaps.columns = ['gap_start', 'gap_end', 'gap_minutes']
    gaps = gaps.sort_values('gap_minutes', ascending=False).reset_index(drop=True)

    if gaps.empty:
        logger.info(f"No gaps > {min_gap_minutes} minutes found.")
        return gaps

    _fig, ax = plt.subplots(figsize=figsize)
    for _, row in gaps.iterrows():
        ax.barh(0, row['gap_minutes'], left=row['gap_start'].timestamp(), height=0.5, alpha=0.5, color='red')
    ax.set_title(f'Time gaps > {min_gap_minutes} min ({len(gaps)} found)')
    ax.set_xlabel('Time')
    plt.tight_layout()
    plt.show()

    return gaps


def plot_wifi_map(df: pd.DataFrame, lat_col: str = 'latitude', lon_col: str = 'longitude',
                  label_col: str = 'ssid'):
    """
    Plot wifi geolocations on an interactive map using folium.

    Args:
        df: DataFrame with latitude/longitude columns.
        lat_col: Name of the latitude column.
        lon_col: Name of the longitude column.
        label_col: Column to use for marker labels.

    Returns:
        folium.Map object (renders inline in Jupyter), or None.
    """
    try:
        import folium  # noqa: PLC0415
    except ImportError:
        logger.error("folium is required for map visualization: pip install sysdiagnose[jupyter]")
        return None

    plot_df = df.dropna(subset=[lat_col, lon_col])
    if plot_df.empty:
        logger.warning("No valid coordinates to plot.")
        return None

    center_lat = plot_df[lat_col].mean()
    center_lon = plot_df[lon_col].mean()
    m = folium.Map(location=[center_lat, center_lon], zoom_start=12)

    for _, row in plot_df.iterrows():
        label = str(row.get(label_col, ''))
        folium.Marker(
            location=[row[lat_col], row[lon_col]],
            popup=label,
            tooltip=label,
        ).add_to(m)

    return m
