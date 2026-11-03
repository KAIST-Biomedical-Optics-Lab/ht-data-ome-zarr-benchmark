# Holotomographic data management test code collections

This repository contains the following code blocks:

 - data converter into OME-Zarr
 - compression benchmark automation
 - simple visualization tool used in publication.

The related paper is under review, and the link will be added when published.

## Requirements

### Benchmark Datasets

The following benchmark datasets are used in this project:

 - Embryo cells in a well
 - Birefringent tissue

We place the data at `data/embryo.ome.zarr` and `data/birefringent-data.ome.zarr`. The basic running environemnt assumes this location dependency.

We are planning to provde link for dowloading data. The documentation will actively revised until publishing a tentative article "Towards Efficient Holotomographic Data Management: Compression Strategies in OME-Zarr".

For additional information, contact me with email (dleh428@kaist.ac.kr).

### Python Environment

[uv](https://github.com/astral-sh/uv) can manage project environments automatically. Installing  `uv` is all you need.

If you want to choose other options, please see package dependencies at `pyproject.toml`.

## Execution

All python files are scripts. They are executed with the followed format: `uv run python SCRIPT_NAME.py ARGS...` or `python SCRIPT_NAME.py ARGS...`.

For a quick execution, run the following scripts sequentially:
 1. `01_compression_benchmark/execution-example/generate-benchmark.sh`
 2. `01_compression_benchmark/execution-example/bulk-benchmark.sh`
 3. `03_visualization/execution-example/run-visualization.sh` (or `uv run python 03_visualization/visualize_benchmark.py`)

### Descripion of each directories and executable files
 - `00_data_processing` : You don't have use it basically for benchmarking. It is the preprocessing tools of converting non-OME-Zarr files into OME-zarr files.
    - `convert_mat73_to_ngff.py` : Convert mat file (Our lab use this matlab file format internally) into OME-Zarr
    - `convert_tcf2ngff.py` : Convert Tomocube file into OME-Zarr
    - `convert_zarr2noisy_zarr.py` : Add noise to the file whose values are truncated with significant digits.
    - `stitch_ngff.py` : Stitch OME-Zarr files into one OME-Zarr file. It utilize the location information in the source files for stitching.
 - `01_compression_benchmark` : Benchmark toolsets
    - `excution-example/` : List of script use for benchmarking.
    - `generate_benchmark_sample.py`: Randomly select chunks for benchmarking
    - `benchmark_sampled_compression.py`: Return single benchmark result for a specific encoding option.
    - `benchmark_sampled_compression_preset_bulk.py`: Run multiple benchmark sequentially and return the result as a table. The example of benchmarking list is at `01_compression_benchmark/benchmark_recipe.toml`.
 - `02_remote_access` : Not described in article. Simple server to validate the remote access of OME-Zarr file through network.
    - `simple-server.py`: Simple OME-Zarr server. It is slow because it does not support parallel transfer. The running example is at `02_remote_access\example\simple-server.sh`.
 - `03_visualization` : CLI scripts, modular Python library (`viz/`), declarative configurations (`config/`), and interactive notebook wrappers for visualizing benchmark results
    - `visualize_benchmark.py`: CLI script to generate overall compression ratio/throughput charts, filter boxplots, and network bottleneck ranking figures using `config/benchmark_visualization.toml` (or `config/benchmark_gpu.toml`).
    - `generate_slice_images.py`: CLI script to extract and save 9 orthogonal cross-sectional slices of OME-Zarr holotomographic volumes using `config/slice_visualization.toml`.
    - `generate_whole_benchmark_table.py`: Merge multiple dataset CSV files into a single summary table using `whole_benchmark_script.toml`.
    - `view_compression_benchmark.ipynb` & `view_slice_image.ipynb`: Lightweight interactive notebook wrappers importing `viz`.
The results of the benchmarks will be documented here.

## Troubleshooting

There was a case that `stitch_ngff.py` does not properly work in "Windows 10/11" returning 'OSError'.
A workaround is to use "Windows subsystem for linux, version 2".
File I/O handler of Windows seems not perfectly suitable with Zarr I/O operations.

If you are using WSL2 with nvCOMP, you probably need the following environment variable to call `libcuda.so`.
```bash
export LD_LIBRARY_PATH=/usr/lib/wsl/lib/
```
