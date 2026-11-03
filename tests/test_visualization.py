"""Unit and integration tests for the modular 03_visualization package and CLI tools."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", tempfile.gettempdir())

import dask.array as da
import matplotlib
import numpy as np
import pandas as pd
from PIL import Image

matplotlib.use("Agg")

REPO_ROOT = Path(__file__).resolve().parents[1]
VIZ_DIR = REPO_ROOT / "03_visualization"
if str(VIZ_DIR) not in sys.path:
    sys.path.insert(0, str(VIZ_DIR))

import generate_slice_images
import visualize_benchmark
from viz import (
    array_to_image,
    bottleneck,
    compute_bottleneck_ranks,
    compute_grouped_benchmark,
    extract_filter_distributions,
    extract_slices,
    get_top_all_rounders,
    load_benchmark_config,
    load_slice_config,
)


class TestVisualizationSuite(unittest.TestCase):
    """Test suite verifying configuration separation, metrics, plotting, and slice rendering."""

    def test_benchmark_config_loading(self) -> None:
        """Verify TOML benchmark config parsing, colors, and per-dataset axis overrides."""
        cfg = load_benchmark_config(VIZ_DIR / "config" / "benchmark_visualization.toml")
        self.assertIn("bacteria", cfg.datasets)
        self.assertIn("organoid", cfg.datasets)
        self.assertIn("gzip", cfg.compression_options)
        self.assertEqual(cfg.compression_options["gzip"], (1, 5, 9))

        # Check normalized RGB color conversion
        none_colors = cfg.filter_display_colors["none"]
        self.assertEqual(len(none_colors), 3)
        for rgb in none_colors:
            self.assertEqual(len(rgb), 3)
            self.assertTrue(all(0.0 <= c <= 1.0 for c in rgb))

        # Check default vs dataset-overridden axis kwargs
        bact_ratio_kw = cfg.get_axis_kwargs("bacteria", "compression ratio")
        org_ratio_kw = cfg.get_axis_kwargs("organoid", "compression ratio")
        toff_ratio_kw = cfg.get_axis_kwargs("tissue-off", "compression ratio")
        self.assertEqual(bact_ratio_kw["ylim"], (1.0, 8.0))
        self.assertEqual(org_ratio_kw["ylim"], (1.0, 10.0))
        self.assertEqual(toff_ratio_kw["ylim"], (1.0, 2.0))

        # Verify GPU config profile
        gpu_cfg = load_benchmark_config(VIZ_DIR / "config" / "benchmark_gpu.toml")
        self.assertIn("NvcompGDeflate", gpu_cfg.compression_options)
        self.assertIsNone(gpu_cfg.bottleneck)

    def test_slice_config_loading(self) -> None:
        """Verify TOML slice config parsing and crop bound normalization."""
        cfg = load_slice_config(VIZ_DIR / "config" / "slice_visualization.toml")
        self.assertIn("bacteria", cfg.datasets)
        self.assertIn("embryo", cfg.datasets)
        self.assertEqual(cfg.datasets["bacteria"].y_crop, (None, None))
        self.assertEqual(cfg.datasets["embryo"].y_crop, (5, -5))
        self.assertEqual(cfg.datasets["tissue-off"].cmap, "PiYG")

    def test_bottleneck_formula_and_ranking(self) -> None:
        """Verify network bottleneck calculation and ranking across transfer rates."""
        # Network-limited
        self.assertAlmostEqual(
            bottleneck(
                comp_ratio=2.0,
                comp_speed=1000.0,
                decomp_speed=2000.0,
                transfer_rate=100.0,
            ),
            200.0,
        )
        # Compression-limited
        self.assertAlmostEqual(
            bottleneck(
                comp_ratio=4.0,
                comp_speed=150.0,
                decomp_speed=2000.0,
                transfer_rate=100.0,
            ),
            150.0,
        )
        # Decompression-limited
        self.assertAlmostEqual(
            bottleneck(
                comp_ratio=4.0,
                comp_speed=1000.0,
                decomp_speed=120.0,
                transfer_rate=100.0,
            ),
            120.0,
        )

        # Synthetic benchmark table
        df = pd.DataFrame(
            [
                {
                    "compression option": "gzip-1",
                    "filter option": "Shuffle",
                    "compression ratio": 2.5,
                    "compression speed (bytes/sec)": 1e8,
                    "decompression speed (bytes/sec)": 3e8,
                },
                {
                    "compression option": "zstd-1",
                    "filter option": "Shuffle",
                    "compression ratio": 3.0,
                    "compression speed (bytes/sec)": 5e8,
                    "decompression speed (bytes/sec)": 8e8,
                },
                {
                    "compression option": "PCodec-6",
                    "filter option": "none",
                    "compression ratio": 4.2,
                    "compression speed (bytes/sec)": 2e8,
                    "decompression speed (bytes/sec)": 4e8,
                },
                {
                    "compression option": "none",
                    "filter option": "none",
                    "compression ratio": 1.0,
                    "compression speed (bytes/sec)": 1e9,
                    "decompression speed (bytes/sec)": 1e9,
                },
            ]
        )

        rank_df = compute_bottleneck_ranks({"sample": df})
        self.assertNotIn("none", rank_df.index)
        self.assertIn("zstd-1", rank_df.index)
        self.assertIn("PCodec-6", rank_df.index)
        self.assertIn("rank-18", rank_df.columns)

        top = get_top_all_rounders(rank_df, top_n=2)
        self.assertEqual(len(top), 2)

    def test_benchmark_cli_and_plotting_end_to_end(self) -> None:
        """Verify end-to-end CLI execution and SVG output creation using synthetic CSV data."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            tmp_dir = Path(tmp)
            csv_path = tmp_dir / "synthetic.csv"
            out_dir = tmp_dir / "figures"
            cfg_path = tmp_dir / "test_bench.toml"

            rows = []
            for comp in ("gzip-1", "gzip-5", "zstd-1"):
                for filt in ("none", "Shuffle", "BitRound-14", "BitRound-14-Shuffle"):
                    rows.append(
                        {
                            "compression option": comp,
                            "filter option": filt,
                            "compression ratio": 2.2 if "gzip" in comp else 3.1,
                            "compression speed (bytes/sec)": 1.5e8,
                            "decompression speed (bytes/sec)": 4.0e8,
                        }
                    )
            pd.DataFrame(rows).to_csv(csv_path, index=False)

            cfg_path.write_text(
                f"""
[general]
output_dir = "{out_dir.as_posix()}"

[datasets]
bacteria = {{ name = "Bacteria", path = "{csv_path.as_posix()}" }}

[compression_options]
gzip = [1, 5]
zstd = [1]

[filter_options]
names = ["none", "Shuffle", "BitRound-14", "BitRound-14-Shuffle"]
throughput_names = ["Shuffle", "none"]

[filter_display_colors]
none = ["#1f78b4", "#63a3cc"]
Shuffle = ["#33a02c", "#73c05b"]
BitRound-14 = ["#e31a1c", "#ef5a5b"]
BitRound-14-Shuffle = ["#ff7f00", "#fe9f38"]

[defaults.axis_limits]
"compression ratio" = {{ ylim = [1.0, 8.0], yscale = "linear" }}
"compression speed (bytes/sec)" = {{ ylim = [1e7, 1e9], yscale = "log" }}
"decompression speed (bytes/sec)" = {{ ylim = [1e7, 1e9], yscale = "log" }}

[bottleneck]
base_transfer_rate_range = [18, 24, 3]
exclude_compressors = ["none"]
exclude_filters = ["BitRound"]
none_filter_compressors = ["PCodec"]
""",
                encoding="utf-8",
            )

            # Test grouping and filter distribution helpers directly
            df = pd.read_csv(csv_path)
            grp = compute_grouped_benchmark(df)
            self.assertFalse(grp.empty)
            dist = extract_filter_distributions(df, ["none", "Shuffle"])
            self.assertEqual(set(dist.keys()), {"none", "Shuffle"})

            # Run CLI main
            exit_code = visualize_benchmark.main(
                ["--config", str(cfg_path), "--figures", "all"]
            )
            self.assertEqual(exit_code, 0)

            self.assertTrue(
                (
                    out_dir / "view-bench-1-overall" / "bacteria-compression ratio.svg"
                ).is_file()
            )
            self.assertTrue(
                (
                    out_dir / "view-bench-1-overall" / "bacteria-compression speed.svg"
                ).is_file()
            )
            self.assertTrue(
                (
                    out_dir / "view-bench-3-filter" / "bacteria-compression ratio.svg"
                ).is_file()
            )
            self.assertTrue(
                (out_dir / "view-bench-5-bottlneck" / "ranking.svg").is_file()
            )

    def test_slice_extraction_and_cli_end_to_end(self) -> None:
        """Verify orthogonal slice extraction, image normalization, and CLI execution."""
        vol = np.linspace(1.30, 1.40, 1 * 1 * 6 * 12 * 14, dtype=np.float32).reshape(
            (1, 1, 6, 12, 14)
        )
        slices = extract_slices(vol, tcz=(0, 0, 3), y_crop=(1, -1), x_crop=(2, -2))
        self.assertEqual(len(slices), 9)
        self.assertEqual(slices["zmiddle-slice"].shape, (10, 10))
        self.assertEqual(slices["ymiddle-slice"].shape, (6, 10))
        self.assertEqual(slices["xmiddle-slice"].shape, (6, 10))

        img = array_to_image(slices["zmiddle-slice"], "gray", 1.33, 1.39)
        self.assertEqual(img.mode, "RGB")
        self.assertEqual(img.size, (10, 10))

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            tmp_dir = Path(tmp)
            zarr_path = tmp_dir / "sample.ome.zarr" / "0"
            out_dir = tmp_dir / "slices"
            cfg_path = tmp_dir / "test_slice.toml"

            da.from_array(vol, chunks=(1, 1, 6, 12, 14)).to_zarr(str(zarr_path))

            cfg_path.write_text(
                f"""
[general]
output_dir = "{out_dir.as_posix()}"

[datasets.sample]
path = "{zarr_path.as_posix()}"
tcz = [0, 0, 3]
y_crop = [1, -1]
x_crop = [2, -2]
crange = [1.33, 1.39]
cmap = "gray"
""",
                encoding="utf-8",
            )

            exit_code = generate_slice_images.main(["--config", str(cfg_path)])
            self.assertEqual(exit_code, 0)

            expected_slice = out_dir / "sample-zmiddle-slice.png"
            self.assertTrue(expected_slice.is_file())
            with Image.open(expected_slice) as rendered:
                self.assertEqual(rendered.size, (10, 10))


if __name__ == "__main__":
    unittest.main()
