# Merge the benchmark CSVs in output/ and generate the error-bounded comparison figures in figure/.
# Run from the repository root.
#   Merge: explicit folder lists (no catch-all glob), so each (compressor, filter) pair comes from one run:
#     - bench-<ds>-8G{,-v2,-v3}      original benchmark (bacteria, embryo, tissue-on)
#     - bench-<ds>-8G-fso*           FixedScaleOffset (+ zstd) runs
#     - bench-<ds>-8G-htpack         HTPack v0.6.0b1 (float RI path)
#     - bench-<ds>-8G-sz3-sperr      SZ3 (pysz 1.1.0) rows; SPERR-1 rows there are eps = 1e-4 (not plotted)
#     - bench-<ds>-8G-sperr-g99      SPERR pwe eps = 0.99e-4 (SPERR_G99-1)
#     HeLa/organoid use the float32 samples (bench-<ds>-8G-f32-*).
#   bench-<ds>-8G-errorbounded (current imagecodecs SZ3/SPERR/LERC runs) is intentionally not merged here.

$merge_code = "03_visualization/merge_output_table.py"
# Non-interactive matplotlib backend: otherwise PyQt5 (napari dependency) is picked and fails without a display session
$env:MPLBACKEND = "Agg"

foreach ($ds in @("bacteria", "embryo", "tissue-on")) {
    uv run python $merge_code `
        "output/bench-$ds-8G/*.csv" "output/bench-$ds-8G-v2/*.csv" "output/bench-$ds-8G-v3/*.csv" `
        "output/bench-$ds-8G-fso*/*.csv" "output/bench-$ds-8G-htpack/*.csv" `
        "output/bench-$ds-8G-sz3-sperr/*.csv" "output/bench-$ds-8G-sperr-g99/*.csv" `
        "output/merged-$ds-8G-errorbounded.csv"
}
foreach ($ds in @("HeLa", "organoid")) {
    uv run python $merge_code "output/bench-$ds-8G-f32-*/*.csv" "output/merged-$ds-8G-errorbounded.csv"
}

$config = "03_visualization/config/benchmark_errorbounded.toml"
foreach ($fmt in @("svg", "png")) {
    uv run python 03_visualization/visualize_benchmark.py --config $config --format $fmt
    # Manuscript comparison (HeLa, organoid): Fourier, BitRound-Pcodec, FSO-Pcodec, SZ3, SPERR
    uv run python 03_visualization/visualize_benchmark.py --config 03_visualization/config/benchmark_paper_comparison.toml --figures comparison --format $fmt
}
