#!/usr/bin/env python3
"""CLI tool for extracting and rendering orthogonal slice images from OME-Zarr datasets."""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", tempfile.gettempdir())

VIZ_DIR = Path(__file__).resolve().parent
if str(VIZ_DIR) not in sys.path:
    sys.path.insert(0, str(VIZ_DIR))

from viz import load_slice_config, render_dataset_slices


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments for OME-Zarr slice rendering."""
    parser = argparse.ArgumentParser(
        description="Render 9 orthogonal slice images per OME-Zarr dataset from a TOML configuration."
    )
    parser.add_argument(
        "--config",
        default="03_visualization/config/slice_visualization.toml",
        help="Path to slice visualization TOML config (default: 03_visualization/config/slice_visualization.toml)",
    )
    parser.add_argument(
        "--dataset",
        action="append",
        dest="datasets",
        help="Optional dataset key(s) to render (can be specified multiple times)",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Optional override for output directory",
    )
    parser.add_argument(
        "--format",
        choices=["png", "jpg", "tiff"],
        default="png",
        help="Output image file format (default: png)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing slice images instead of skipping them",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate configuration and print planned actions without reading OME-Zarr data",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Main entry point for slice image CLI execution."""
    args = parse_args(argv)
    config = load_slice_config(args.config)

    if args.datasets:
        selected = set(args.datasets)
        config.datasets = {k: v for k, v in config.datasets.items() if k in selected}
        if not config.datasets:
            raise ValueError(f"No matching datasets found for: {args.datasets}")

    output_dir = Path(args.output_dir) if args.output_dir else config.output_dir

    if args.dry_run:
        print(f"Slice configuration loaded successfully from: {args.config}")
        print(f"Output directory: {output_dir}")
        print(f"Datasets ({len(config.datasets)}): {list(config.datasets.keys())}")
        for k, spec in config.datasets.items():
            status = "FOUND" if spec.path.exists() else "MISSING"
            print(
                f"  - {k}: path={spec.path} [{status}], tcz={spec.tcz}, "
                f"y_crop={spec.y_crop}, x_crop={spec.x_crop}, crange={spec.crange}, cmap={spec.cmap}"
            )
        return 0

    total_saved: list[Path] = []
    for key, spec in config.datasets.items():
        print(f"Rendering orthogonal slices for dataset: {key}...")
        saved = render_dataset_slices(
            spec=spec,
            output_dir=output_dir,
            overwrite=args.overwrite,
            fmt=args.format,
        )
        total_saved.extend(saved)

    print(f"\nProcessed {len(total_saved)} slice image(s) in {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
