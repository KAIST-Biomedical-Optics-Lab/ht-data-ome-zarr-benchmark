#!/usr/bin/env bash
set -e

echo "=== Generating Benchmark Figures ==="
uv run python 03_visualization/visualize_benchmark.py --config 03_visualization/config/benchmark_visualization.toml

echo "=== Generating GPU Benchmark Figures ==="
uv run python 03_visualization/visualize_benchmark.py --config 03_visualization/config/benchmark_gpu.toml

echo "=== Generating Slice Images ==="
uv run python 03_visualization/generate_slice_images.py --config 03_visualization/config/slice_visualization.toml
