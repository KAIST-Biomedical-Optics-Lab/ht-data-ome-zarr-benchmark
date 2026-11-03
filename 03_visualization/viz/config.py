"""Configuration loader and path resolution for visualization tools."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
VIZ_ROOT = Path(__file__).resolve().parents[1]


def resolve_config_file(config_path: str | Path) -> Path:
    """Resolve a configuration file path from current dir, viz dir, or repo root."""
    candidate = Path(config_path)
    if candidate.is_file():
        return candidate.resolve()

    for base in (REPO_ROOT, VIZ_ROOT):
        alt = base / candidate
        if alt.is_file():
            return alt.resolve()

    raise FileNotFoundError(f"Configuration file not found: {config_path}")


def resolve_resource_path(path_str: str | Path, base_dir: Path | None = None) -> Path:
    """Resolve a data or output path relative to base_dir (defaults to REPO_ROOT)."""
    p = Path(path_str)
    if p.is_absolute():
        return p
    root = base_dir if base_dir is not None else REPO_ROOT
    return root / p


def parse_color(
    color_val: str | list[float] | tuple[float, ...],
) -> tuple[float, float, float]:
    """Convert a hex color string or RGB sequence to a normalized (r, g, b) float tuple."""
    if isinstance(color_val, str):
        hex_str = color_val.lstrip("#")
        if len(hex_str) != 6:
            raise ValueError(f"Invalid hex color: {color_val}")
        r = int(hex_str[0:2], 16) / 255.0
        g = int(hex_str[2:4], 16) / 255.0
        b = int(hex_str[4:6], 16) / 255.0
        return (r, g, b)
    if isinstance(color_val, (list, tuple)) and len(color_val) == 3:
        vals = [float(x) for x in color_val]
        if any(v > 1.0 for v in vals):
            return (vals[0] / 255.0, vals[1] / 255.0, vals[2] / 255.0)
        return (vals[0], vals[1], vals[2])
    raise ValueError(f"Unsupported color specification: {color_val!r}")


@dataclass
class DatasetSpec:
    """Specification for a single benchmark CSV dataset."""

    key: str
    name: str
    path: Path


@dataclass
class BottleneckConfig:
    """Configuration parameters for network bottleneck ranking analysis."""

    base_transfer_rate_range: range = field(default_factory=lambda: range(18, 36, 3))
    exclude_compressors: list[str] = field(
        default_factory=lambda: ["none", "Nvcomp", "Zlibng"]
    )
    exclude_filters: list[str] = field(default_factory=lambda: ["BitRound"])
    none_filter_compressors: list[str] = field(
        default_factory=lambda: ["PCodec", "ZFP"]
    )


@dataclass
class BenchmarkConfig:
    """Parsed configuration for compression benchmark visualizations."""

    output_dir: Path
    overall_subdir: str
    filter_subdir: str
    bottleneck_subdir: str
    datasets: dict[str, DatasetSpec]
    compression_options: dict[str, tuple[int, ...]]
    filter_options: list[str]
    throughput_filter_options: list[str]
    filter_display_colors: dict[str, list[tuple[float, float, float]]]
    default_axis_limits: dict[str, dict[str, Any]]
    dataset_overrides: dict[str, dict[str, dict[str, Any]]]
    bottleneck: BottleneckConfig | None = None

    def get_axis_kwargs(self, dataset_key: str, metric: str) -> dict[str, Any]:
        """Return matplotlib axis kwargs (ylim, yscale, etc.) for a dataset and metric."""
        base = dict(self.default_axis_limits.get(metric, {}))
        overrides = self.dataset_overrides.get(dataset_key, {}).get(metric, {})
        merged = {**base, **overrides}
        if "ylim" in merged and isinstance(merged["ylim"], list):
            merged["ylim"] = tuple(merged["ylim"])
        return merged


@dataclass
class SliceDatasetSpec:
    """Specification for slicing a single OME-Zarr dataset."""

    key: str
    path: Path
    tcz: tuple[int, int, int]
    y_crop: tuple[int | None, int | None]
    x_crop: tuple[int | None, int | None]
    crange: tuple[float, float]
    cmap: str


@dataclass
class SliceConfig:
    """Parsed configuration for OME-Zarr orthogonal slice rendering."""

    output_dir: Path
    datasets: dict[str, SliceDatasetSpec]


def _parse_crop_bounds(
    bounds: list[int | None] | None,
) -> tuple[int | None, int | None]:
    """Convert [0, 0] or None into (None, None) for full-axis slicing."""
    if not bounds or len(bounds) != 2:
        return (None, None)
    start, stop = bounds[0], bounds[1]
    if start == 0 and stop == 0:
        return (None, None)
    return (start, stop)


def load_benchmark_config(
    config_path: str | Path, base_dir: Path | None = None
) -> BenchmarkConfig:
    """Load and validate a benchmark visualization TOML configuration file."""
    resolved_cfg = resolve_config_file(config_path)
    with open(resolved_cfg, "rb") as f:
        raw = tomllib.load(f)

    general = raw.get("general", {})
    output_dir = resolve_resource_path(general.get("output_dir", "figure"), base_dir)
    overall_subdir = general.get("overall_subdir", "view-bench-1-overall")
    filter_subdir = general.get("filter_subdir", "view-bench-3-filter")
    bottleneck_subdir = general.get("bottleneck_subdir", "view-bench-5-bottlneck")

    datasets: dict[str, DatasetSpec] = {}
    for key, val in raw.get("datasets", {}).items():
        if isinstance(val, str):
            ds_path = resolve_resource_path(val, base_dir)
            ds_name = key
        else:
            ds_path = resolve_resource_path(val["path"], base_dir)
            ds_name = val.get("name", key)
        datasets[key] = DatasetSpec(key=key, name=ds_name, path=ds_path)

    compression_options = {
        comp: tuple(int(level) for level in levels)
        for comp, levels in raw.get("compression_options", {}).items()
    }

    filter_cfg = raw.get("filter_options", {})
    filter_options = list(
        filter_cfg.get(
            "names", ["none", "Shuffle", "BitRound-14", "BitRound-14-Shuffle"]
        )
    )
    throughput_filter_options = list(
        filter_cfg.get("throughput_names", ["Shuffle", "none"])
    )

    colors_raw = raw.get("filter_display_colors", {})
    filter_display_colors = {
        filt: [parse_color(c) for c in color_list]
        for filt, color_list in colors_raw.items()
    }

    defaults_raw = raw.get("defaults", {}).get("axis_limits", {})
    default_axis_limits: dict[str, dict[str, Any]] = {
        metric: dict(params) for metric, params in defaults_raw.items()
    }

    overrides_raw = raw.get("dataset_overrides", {})
    dataset_overrides: dict[str, dict[str, dict[str, Any]]] = {
        ds_key: {metric: dict(params) for metric, params in ds_metrics.items()}
        for ds_key, ds_metrics in overrides_raw.items()
    }

    bottleneck_cfg: BottleneckConfig | None = None
    if "bottleneck" in raw:
        b_raw = raw["bottleneck"]
        r_vals = b_raw.get("base_transfer_rate_range", [18, 36, 3])
        bottleneck_cfg = BottleneckConfig(
            base_transfer_rate_range=range(
                int(r_vals[0]), int(r_vals[1]), int(r_vals[2])
            ),
            exclude_compressors=list(
                b_raw.get("exclude_compressors", ["none", "Nvcomp", "Zlibng"])
            ),
            exclude_filters=list(b_raw.get("exclude_filters", ["BitRound"])),
            none_filter_compressors=list(
                b_raw.get("none_filter_compressors", ["PCodec", "ZFP"])
            ),
        )

    return BenchmarkConfig(
        output_dir=output_dir,
        overall_subdir=overall_subdir,
        filter_subdir=filter_subdir,
        bottleneck_subdir=bottleneck_subdir,
        datasets=datasets,
        compression_options=compression_options,
        filter_options=filter_options,
        throughput_filter_options=throughput_filter_options,
        filter_display_colors=filter_display_colors,
        default_axis_limits=default_axis_limits,
        dataset_overrides=dataset_overrides,
        bottleneck=bottleneck_cfg,
    )


def load_slice_config(
    config_path: str | Path, base_dir: Path | None = None
) -> SliceConfig:
    """Load and validate an OME-Zarr slice visualization TOML configuration file."""
    resolved_cfg = resolve_config_file(config_path)
    with open(resolved_cfg, "rb") as f:
        raw = tomllib.load(f)

    general = raw.get("general", {})
    output_dir = resolve_resource_path(
        general.get("output_dir", "figure/slice-image"), base_dir
    )

    datasets: dict[str, SliceDatasetSpec] = {}
    for key, val in raw.get("datasets", {}).items():
        tcz_list = val.get("tcz", [0, 0, 0])
        crange_list = val.get("crange", [0.0, 1.0])
        datasets[key] = SliceDatasetSpec(
            key=key,
            path=resolve_resource_path(val["path"], base_dir),
            tcz=(int(tcz_list[0]), int(tcz_list[1]), int(tcz_list[2])),
            y_crop=_parse_crop_bounds(val.get("y_crop")),
            x_crop=_parse_crop_bounds(val.get("x_crop")),
            crange=(float(crange_list[0]), float(crange_list[1])),
            cmap=str(val.get("cmap", "gray")),
        )

    return SliceConfig(output_dir=output_dir, datasets=datasets)
