"""Modular visualization library for holotomographic OME-Zarr compression benchmarks."""

from .benchmark_metrics import (
    bottleneck,
    compute_bottleneck_ranks,
    compute_grouped_benchmark,
    extract_filter_distributions,
    get_top_all_rounders,
    load_benchmark_tables,
)
from .benchmark_plots import (
    plot_bottleneck_ranking,
    plot_compression_ratio,
    plot_filter_boxplot,
    plot_method_comparison,
    plot_throughput,
)
from .config import (
    BenchmarkConfig,
    BottleneckConfig,
    DatasetSpec,
    SliceConfig,
    SliceDatasetSpec,
    load_benchmark_config,
    load_slice_config,
)
from .slice_renderer import (
    array_to_image,
    extract_slices,
    render_dataset_slices,
)

__all__ = [
    "BenchmarkConfig",
    "BottleneckConfig",
    "DatasetSpec",
    "SliceConfig",
    "SliceDatasetSpec",
    "array_to_image",
    "bottleneck",
    "compute_bottleneck_ranks",
    "compute_grouped_benchmark",
    "extract_filter_distributions",
    "extract_slices",
    "get_top_all_rounders",
    "load_benchmark_config",
    "load_benchmark_tables",
    "load_slice_config",
    "plot_bottleneck_ranking",
    "plot_compression_ratio",
    "plot_filter_boxplot",
    "plot_method_comparison",
    "plot_throughput",
    "render_dataset_slices",
]
