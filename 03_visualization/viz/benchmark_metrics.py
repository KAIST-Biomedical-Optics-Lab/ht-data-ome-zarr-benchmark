"""Data loading, aggregation, and bottleneck ranking calculations for benchmarks."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import BenchmarkConfig, BottleneckConfig


def load_benchmark_tables(
    config: BenchmarkConfig,
    filter_compressors: bool = False,
) -> dict[str, pd.DataFrame]:
    """Load all benchmark CSV files specified in the configuration.

    Args:
        config: Parsed BenchmarkConfig instance.
        filter_compressors: If True, keep only rows whose compressor name is in
            config.compression_options.

    Returns:
        Dictionary mapping dataset key to its pandas DataFrame.
    """
    tables: dict[str, pd.DataFrame] = {}
    valid_compressors = set(config.compression_options.keys())

    for key, spec in config.datasets.items():
        if not spec.path.exists():
            raise FileNotFoundError(
                f"Benchmark CSV for dataset '{key}' not found: {spec.path}"
            )
        df = pd.read_csv(spec.path)
        if filter_compressors and valid_compressors:
            df = df[
                df["compression option"].map(
                    lambda x: (
                        str(x).rsplit("-", 1)[0] in valid_compressors
                        or str(x) in valid_compressors
                    )
                )
            ]
        tables[key] = df

    return tables


def compute_grouped_benchmark(df: pd.DataFrame) -> pd.DataFrame:
    """Group benchmark DataFrame by compression and filter options and average metrics."""
    return df.groupby(["compression option", "filter option"]).mean(numeric_only=True)


def extract_filter_distributions(
    df: pd.DataFrame,
    filter_options: list[str],
    metric: str = "compression ratio",
) -> dict[str, pd.Series]:
    """Extract metric distributions per filter option (excluding 'none' compression)."""
    distributions: dict[str, pd.Series] = {}
    for filt_name in filter_options:
        mask = (df["filter option"] == filt_name) & (df["compression option"] != "none")
        distributions[filt_name] = df.loc[mask, metric]
    return distributions


def bottleneck(
    comp_ratio: float,
    comp_speed: float,
    decomp_speed: float,
    transfer_rate: float = float(2**7),
) -> float:
    """Compute effective throughput limited by network transfer, compression, or decompression.

    Higher values indicate better effective performance.
    """
    return float(min(comp_ratio * transfer_rate, comp_speed, decomp_speed))


def compute_bottleneck_ranks(
    benchmark_tables: dict[str, pd.DataFrame],
    bottleneck_cfg: BottleneckConfig | None = None,
) -> pd.DataFrame:
    """Evaluate ordinal rankings of compression options across network transfer rates."""
    if not benchmark_tables:
        raise ValueError("benchmark_tables cannot be empty")

    cfg = bottleneck_cfg or BottleneckConfig()
    concat_df = pd.concat(list(benchmark_tables.values()), axis=0, join="outer")

    # Exclude configured compressor prefixes and 'none'
    for prefix in cfg.exclude_compressors:
        concat_df = concat_df[
            concat_df["compression option"].map(
                lambda x, p=prefix: x != p and not str(x).startswith(p)
            )
        ]

    # Exclude configured filter prefixes
    for prefix in cfg.exclude_filters:
        concat_df = concat_df[
            concat_df["filter option"].map(lambda x, p=prefix: not str(x).startswith(p))
        ]

    # Separate codecs that operate without Shuffle (e.g. PCodec, ZFP) vs Shuffle-filtered codecs
    concat_df_none_only = concat_df[
        concat_df["compression option"].map(
            lambda x: any(tok in str(x) for tok in cfg.none_filter_compressors)
        )
    ]
    concat_df_shuffle_only = concat_df[
        concat_df["filter option"].map(lambda x: x == "Shuffle")
    ]
    filter_df = pd.concat(
        [concat_df_none_only, concat_df_shuffle_only], axis=0, join="outer"
    ).copy()

    if "filter option" in filter_df.columns:
        filter_df.pop("filter option")

    rank_df = filter_df.groupby(["compression option"]).mean(numeric_only=True)

    for base_rate in cfg.base_transfer_rate_range:
        transfer_rate = float(2**base_rate)
        scores = rank_df.apply(
            lambda row, tr=transfer_rate: bottleneck(
                float(row["compression ratio"]),
                float(row["compression speed (bytes/sec)"]),
                float(row["decompression speed (bytes/sec)"]),
                transfer_rate=tr,
            ),
            axis=1,
        ).sort_values()
        rank_df.loc[scores.index, f"rank-{base_rate}"] = np.arange(len(scores))

    return rank_df


def get_top_all_rounders(rank_df: pd.DataFrame, top_n: int = 7) -> pd.Series:
    """Return top compression options ranked by their worst-case (minimum) rank across transfer rates."""
    rank_cols = [c for c in rank_df.columns if str(c).startswith("rank-")]
    min_ranks = rank_df[rank_cols].min(axis=1)
    return min_ranks.sort_values(ascending=False).head(top_n)
