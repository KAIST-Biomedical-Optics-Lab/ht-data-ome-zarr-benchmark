#!/usr/bin/env python3
"""CLI tool for generating compression benchmark visualizations from declarative TOML configs."""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", tempfile.gettempdir())
os.environ.setdefault("MPLBACKEND", "Agg")  # file output only; avoids the PyQt5 backend

# Ensure 03_visualization is importable regardless of working directory
VIZ_DIR = Path(__file__).resolve().parent
if str(VIZ_DIR) not in sys.path:
    sys.path.insert(0, str(VIZ_DIR))

from viz import (
    BenchmarkConfig,
    compute_bottleneck_ranks,
    compute_grouped_benchmark,
    extract_filter_distributions,
    get_top_all_rounders,
    load_benchmark_config,
    load_benchmark_tables,
    plot_bottleneck_ranking,
    plot_compression_ratio,
    plot_filter_boxplot,
    plot_throughput,
)


def run_overall_visualizations(
    config: BenchmarkConfig,
    tables: dict,
    output_dir: Path,
    fmt: str = "svg",
) -> list[Path]:
    """Generate Visualization 1: overall compression ratio and throughput bar charts."""
    saved: list[Path] = []
    overall_dir = output_dir / config.overall_subdir

    for name, df in tables.items():
        grp_df = compute_grouped_benchmark(df)

        # 1. Compression ratio
        bench_param = "compression ratio"
        kwargs = config.get_axis_kwargs(name, bench_param)
        srs = grp_df.loc[:, bench_param]
        save_path = overall_dir / f"{name}-{bench_param.split('(')[0].strip()}.{fmt}"
        plot_compression_ratio(
            srs=srs,
            compression_options=config.compression_options,
            filter_options=config.filter_options,
            filter_display_colors=config.filter_display_colors,
            save_path=save_path,
            **kwargs,
        )
        saved.append(save_path)

        # 2. Compression & decompression throughput
        for speed_param in (
            "compression speed (bytes/sec)",
            "decompression speed (bytes/sec)",
        ):
            kwargs = config.get_axis_kwargs(name, speed_param)
            srs = grp_df.loc[:, speed_param]
            metric_short = speed_param.split("(")[0].strip()
            save_path = overall_dir / f"{name}-{metric_short}.{fmt}"
            plot_throughput(
                srs=srs,
                compression_options=config.compression_options,
                filter_options=config.throughput_filter_options,
                filter_display_colors=config.filter_display_colors,
                save_path=save_path,
                **kwargs,
            )
            saved.append(save_path)

    return saved


def run_filter_visualizations(
    config: BenchmarkConfig,
    tables: dict,
    output_dir: Path,
    fmt: str = "svg",
) -> list[Path]:
    """Generate Visualization 3: compression ratio improvement boxplot per filter."""
    saved: list[Path] = []
    filter_dir = output_dir / config.filter_subdir
    bench_param = "compression ratio"

    for name, df in tables.items():
        sub_bench_by_filter = extract_filter_distributions(
            df, config.filter_options, metric=bench_param
        )
        medians = {
            k: float(v.median()) for k, v in sub_bench_by_filter.items() if not v.empty
        }
        print(f"[{name}] Filter medians ({bench_param}): {medians}")

        kwargs = config.get_axis_kwargs(name, bench_param)
        metric_short = bench_param.split("(")[0].strip()
        save_path = filter_dir / f"{name}-{metric_short}.{fmt}"
        plot_filter_boxplot(
            bench_by_filter=sub_bench_by_filter,
            save_path=save_path,
            **kwargs,
        )
        saved.append(save_path)

    return saved


def run_bottleneck_visualization(
    config: BenchmarkConfig,
    tables: dict,
    output_dir: Path,
    fmt: str = "svg",
) -> Path:
    """Generate Visualization 5: network bottleneck ranking trajectory plot."""
    rank_df = compute_bottleneck_ranks(tables, config.bottleneck)
    save_path = output_dir / config.bottleneck_subdir / f"ranking.{fmt}"
    plot_bottleneck_ranking(
        rank_df=rank_df,
        save_path=save_path,
        xscale="log",
    )
    top_all_rounders = get_top_all_rounders(rank_df, top_n=7)
    print("\nTop all-rounder compression options (by worst-case rank):")
    print(top_all_rounders)
    return save_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments for benchmark visualization."""
    parser = argparse.ArgumentParser(
        description="Generate compression benchmark figures from a TOML configuration."
    )
    parser.add_argument(
        "--config",
        default="03_visualization/config/benchmark_visualization.toml",
        help="Path to benchmark visualization TOML config (default: 03_visualization/config/benchmark_visualization.toml)",
    )
    parser.add_argument(
        "--figures",
        choices=["all", "overall", "filter", "bottleneck"],
        default="all",
        help="Which figure suite to generate (default: all)",
    )
    parser.add_argument(
        "--dataset",
        action="append",
        dest="datasets",
        help="Optional dataset key(s) to process (can be specified multiple times)",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Optional override for base figure output directory",
    )
    parser.add_argument(
        "--format",
        choices=["svg", "png", "pdf"],
        default="svg",
        help="Output figure file format (default: svg)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate configuration and print planned actions without reading CSVs or saving figures",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Main entry point for CLI execution."""
    args = parse_args(argv)
    config = load_benchmark_config(args.config)

    if args.datasets:
        selected = set(args.datasets)
        config.datasets = {k: v for k, v in config.datasets.items() if k in selected}
        if not config.datasets:
            raise ValueError(f"No matching datasets found for: {args.datasets}")

    output_dir = Path(args.output_dir) if args.output_dir else config.output_dir

    if args.dry_run:
        print(f"Configuration loaded successfully from: {args.config}")
        print(f"Output directory: {output_dir}")
        print(f"Datasets ({len(config.datasets)}): {list(config.datasets.keys())}")
        for k, spec in config.datasets.items():
            status = "FOUND" if spec.path.exists() else "MISSING"
            print(f"  - {k} ({spec.name}): {spec.path} [{status}]")
        print(
            f"Compressors ({len(config.compression_options)}): {list(config.compression_options.keys())}"
        )
        print(f"Filters: {config.filter_options}")
        print(f"Selected figure suite: {args.figures} (format: {args.format})")
        return 0

    tables = load_benchmark_tables(config)
    saved_files: list[Path] = []

    if args.figures in ("all", "overall"):
        saved_files.extend(
            run_overall_visualizations(config, tables, output_dir, fmt=args.format)
        )

    if args.figures in ("all", "filter") and (
        args.figures == "filter" or config.bottleneck is not None
    ):
        saved_files.extend(
            run_filter_visualizations(config, tables, output_dir, fmt=args.format)
        )

    if args.figures in ("all", "bottleneck") and (
        args.figures == "bottleneck" or config.bottleneck is not None
    ):
        saved_files.append(
            run_bottleneck_visualization(config, tables, output_dir, fmt=args.format)
        )

    print(f"\nGenerated {len(saved_files)} figure(s) in {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
