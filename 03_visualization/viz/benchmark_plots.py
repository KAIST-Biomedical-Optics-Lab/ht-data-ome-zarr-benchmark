"""Matplotlib plotting routines for compression benchmark visualizations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import colormaps as cm
from matplotlib.axes import Axes
from matplotlib.figure import Figure


def _save_and_return(
    fig: Figure,
    ax: Axes,
    save_path: str | Path | None,
    close_fig: bool,
) -> tuple[Figure, Axes]:
    """Save figure to disk (creating parent directories) if save_path is provided."""
    if save_path is not None:
        out_path = Path(save_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path)
        if close_fig:
            plt.close(fig)
    return fig, ax


def plot_compression_ratio(
    srs: pd.Series,
    compression_options: dict[str, tuple[int, ...]],
    filter_options: list[str],
    filter_display_colors: dict[str, list[tuple[float, float, float]]],
    save_path: str | Path | None = None,
    ax: Axes | None = None,
    close_fig: bool = True,
    **kwargs: Any,
) -> tuple[Figure, Axes]:
    """Plot bar chart of compression ratios across codecs, levels, and filters."""
    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.figure  # type: ignore[assignment]

    if kwargs:
        ax.set(**kwargs)

    x = np.zeros(len(filter_options))
    tick_loc: list[float] = []
    tick_label: list[str] = []

    for comp_name, comp_degree in compression_options.items():
        any_degree_plotted = False
        for d_idx, deg in enumerate(comp_degree):
            comp_opt = f"{comp_name}-{deg}"
            if comp_opt not in srs.index:
                continue
            sub_srs = srs.loc[comp_opt]
            avail_f_opt = [f for f in filter_options if f in sub_srs.index.tolist()]
            if not avail_f_opt:
                continue
            y = sub_srs.loc[avail_f_opt].sort_values(ascending=False)
            c = [
                filter_display_colors[filt_name][
                    min(d_idx, len(filter_display_colors[filt_name]) - 1)
                ]
                for filt_name in y.index
            ]
            ax.bar(x[0 : len(y)], y, color=c)
            tick_loc.append(float(x[0]))
            tick_label.append(comp_opt)
            x += 1
            any_degree_plotted = True
        if any_degree_plotted:
            x += 1

    if tick_loc:
        ax.set_xticks(tick_loc, tick_label, rotation=90)
        ax.set_xlim(-1, tick_loc[-1] + 1)

    return _save_and_return(fig, ax, save_path, close_fig)


def plot_throughput(
    srs: pd.Series,
    compression_options: dict[str, tuple[int, ...]],
    filter_options: list[str],
    filter_display_colors: dict[str, list[tuple[float, float, float]]],
    save_path: str | Path | None = None,
    ax: Axes | None = None,
    close_fig: bool = True,
    **kwargs: Any,
) -> tuple[Figure, Axes]:
    """Plot bar chart of compression or decompression throughput across codecs."""
    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.figure  # type: ignore[assignment]

    if kwargs:
        ax.set(**kwargs)

    x = np.zeros(len(filter_options))
    tick_loc: list[float] = []
    tick_label: list[str] = []

    for comp_name, comp_degree in compression_options.items():
        any_degree_plotted = False
        for d_idx, deg in enumerate(comp_degree):
            comp_opt = f"{comp_name}-{deg}"
            if comp_opt not in srs.index:
                continue
            sub_srs = srs.loc[comp_opt]
            avail_f_opt = [f for f in filter_options if f in sub_srs.index.tolist()]
            if not avail_f_opt:
                continue
            avail_f_opt = [avail_f_opt[0]]
            y = sub_srs.loc[avail_f_opt].sort_values(ascending=False)
            c = [
                filter_display_colors[filt_name][
                    min(d_idx, len(filter_display_colors[filt_name]) - 1)
                ]
                for filt_name in y.index
            ]
            ax.bar(x[0 : len(y)], y, color=c)
            any_degree_plotted = True
        if any_degree_plotted:
            tick_loc.append(float(x[0]))
            tick_label.append(comp_name)
            x += 1

    if tick_loc:
        ax.set_xticks(tick_loc, tick_label, rotation=90)
        ax.set_xlim(-1, tick_loc[-1] + 1)

    return _save_and_return(fig, ax, save_path, close_fig)


def plot_filter_boxplot(
    bench_by_filter: dict[str, pd.Series],
    save_path: str | Path | None = None,
    ax: Axes | None = None,
    close_fig: bool = True,
    **kwargs: Any,
) -> tuple[Figure, Axes]:
    """Plot boxplot comparing benchmark metric distributions across filter options."""
    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.figure  # type: ignore[assignment]

    if kwargs:
        ax.set(**kwargs)

    ax.boxplot(
        list(bench_by_filter.values()),
        tick_labels=list(bench_by_filter.keys()),
    )

    return _save_and_return(fig, ax, save_path, close_fig)


def _cm_map(v: float) -> np.ndarray:
    """Map normalized value in [0, 1] to darkened PiYG RGB color."""
    true_color = cm["PiYG"](v)[:-1]
    return np.array([c * 0.8 for c in true_color])


def plot_bottleneck_ranking(
    rank_df: pd.DataFrame,
    save_path: str | Path | None = None,
    ax: Axes | None = None,
    close_fig: bool = True,
    **kwargs: Any,
) -> tuple[Figure, Axes]:
    """Plot ordinal ranking trajectories across network transfer rates."""
    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.figure  # type: ignore[assignment]

    if kwargs:
        ax.set(**kwargs)

    base_transfer_rate_list = sorted(
        int(str(idx).rsplit("-", 1)[-1])
        for idx in rank_df.columns
        if str(idx).startswith("rank-")
    )
    if not base_transfer_rate_list:
        raise ValueError("rank_df must contain 'rank-<rate>' columns")

    x_transfer_rate = [2**bt for bt in base_transfer_rate_list]
    column_idx = [f"rank-{t}" for t in base_transfer_rate_list]
    x_min_text = 2 ** (base_transfer_rate_list[0] - 1)
    x_max_text = 2 ** (base_transfer_rate_list[-1] + 1)

    comp_option_names = rank_df.index.tolist()
    last_ranks = rank_df[column_idx[-1]]
    denom = max(len(last_ranks) - 1, 1)
    compression_options_color = {
        n: _cm_map(float(r) / denom) for n, r in zip(comp_option_names, last_ranks)
    }

    for comp_opt, color in compression_options_color.items():
        y_rank = rank_df.loc[comp_opt, column_idx]
        ax.plot(x_transfer_rate, y_rank, color=color, marker="o")
        ax.text(
            x_min_text,
            float(y_rank[f"rank-{base_transfer_rate_list[0]}"]),
            str(comp_opt),
            ha="right",
        )
        ax.text(
            x_max_text,
            float(y_rank[f"rank-{base_transfer_rate_list[-1]}"]),
            str(comp_opt),
        )

    return _save_and_return(fig, ax, save_path, close_fig)


def plot_method_comparison(
    grouped_tables: dict[str, pd.DataFrame],
    methods: list[dict[str, str]],
    metric: str = "compression ratio",
    save_path: str | Path | None = None,
    ax: Axes | None = None,
    close_fig: bool = True,
    bar_label_fmt: str | None = None,
    **kwargs: Any,
) -> tuple[Figure, Axes]:
    """Plot grouped bars of one metric for selected (compression, filter) pairs per dataset.

    Args:
        grouped_tables: Dataset display name -> output of compute_grouped_benchmark.
        methods: Each item has 'compression' and 'filter' keys, and optional
            'label' and 'color'. Pairs missing in a dataset are left blank.
        metric: Column to plot (e.g. 'compression ratio').
        bar_label_fmt: Optional format string (e.g. '{:.2f}') for bar value labels.
    """
    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.figure  # type: ignore[assignment]

    if kwargs:
        ax.set(**kwargs)

    names = list(grouped_tables)
    x = np.arange(len(names))
    width = 0.8 / max(len(methods), 1)

    for i, m in enumerate(methods):
        key = (m["compression"], m["filter"])
        vals = [
            float(grp.loc[key, metric]) if key in grp.index else np.nan
            for grp in grouped_tables.values()
        ]
        bars = ax.bar(
            x + (i - (len(methods) - 1) / 2) * width,
            vals,
            width=width * 0.92,
            color=m.get("color"),
            edgecolor="black",
            linewidth=0.6,
            label=m.get("label", f"{m['compression']} + {m['filter']}"),
        )
        if bar_label_fmt is not None:
            ax.bar_label(
                bars,
                labels=[
                    bar_label_fmt.format(v) if np.isfinite(v) else "" for v in vals
                ],
                fontsize=7,
                padding=2,
            )

    ax.set_xticks(x, names, rotation=20, ha="right")
    ax.legend(fontsize=7, loc="upper left", bbox_to_anchor=(1.0, 1.0))

    return _save_and_return(fig, ax, save_path, close_fig)
