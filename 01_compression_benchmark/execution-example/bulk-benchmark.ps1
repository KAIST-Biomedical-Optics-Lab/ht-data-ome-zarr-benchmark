$benchmark_code="01_compression_benchmark/benchmark_sampled_compression_preset_bulk.py"
$benchmark_recipe="01_compression_benchmark/benchmark_recipe.toml"

uv run python $benchmark_code $benchmark_recipe data/test-embryo-8G output/bench-embryo-8G
uv run python $benchmark_code $benchmark_recipe data/test-tissue-on-8G output/bench-tissue-on-8G
uv run python $benchmark_code $benchmark_recipe data/test-tissue-off-8G output/bench-tissue-off-8G
uv run python $benchmark_code $benchmark_recipe data/test-organoid-8G output/bench-organoid-8G
uv run python $benchmark_code $benchmark_recipe data/test-HeLa-8G output/bench-HeLa-8G
uv run python $benchmark_code $benchmark_recipe data/test-bacteria-8G output/bench-bacteria-8G

$benchmark_recipe="01_compression_benchmark/benchmark_recipe-2.toml"

uv run python $benchmark_code $benchmark_recipe data/test-embryo-8G output/bench-embryo-8G-v2
uv run python $benchmark_code $benchmark_recipe data/test-tissue-on-8G output/bench-tissue-on-8G-v2
uv run python $benchmark_code $benchmark_recipe data/test-tissue-off-8G output/bench-tissue-off-8G-v2
uv run python $benchmark_code $benchmark_recipe data/test-organoid-8G output/bench-organoid-8G-v2
uv run python $benchmark_code $benchmark_recipe data/test-HeLa-8G output/bench-HeLa-8G-v2
uv run python $benchmark_code $benchmark_recipe data/test-bacteria-8G output/bench-bacteria-8G-v2

$benchmark_recipe="01_compression_benchmark/benchmark_recipe-3.toml"

uv run python $benchmark_code $benchmark_recipe data/test-embryo-8G output/bench-embryo-8G-v3
uv run python $benchmark_code $benchmark_recipe data/test-tissue-on-8G output/bench-tissue-on-8G-v3
uv run python $benchmark_code $benchmark_recipe data/test-tissue-off-8G output/bench-tissue-off-8G-v3
uv run python $benchmark_code $benchmark_recipe data/test-organoid-8G output/bench-organoid-8G-v3
uv run python $benchmark_code $benchmark_recipe data/test-HeLa-8G output/bench-HeLa-8G-v3
uv run python $benchmark_code $benchmark_recipe data/test-bacteria-8G output/bench-bacteria-8G-v3

$benchmark_recipe="01_compression_benchmark/benchmark_recipe-fso.toml"

uv run python $benchmark_code $benchmark_recipe data/test-embryo-8G output/bench-embryo-8G-fso
uv run python $benchmark_code $benchmark_recipe data/test-tissue-on-8G output/bench-tissue-on-8G-fso
uv run python $benchmark_code $benchmark_recipe data/test-organoid-8G output/bench-organoid-8G-fso
uv run python $benchmark_code $benchmark_recipe data/test-HeLa-8G output/bench-HeLa-8G-fso
uv run python $benchmark_code $benchmark_recipe data/test-bacteria-8G output/bench-bacteria-8G-fso

$benchmark_recipe="01_compression_benchmark/benchmark_recipe-fso-pcodec.toml"

uv run python $benchmark_code $benchmark_recipe data/test-embryo-8G output/bench-embryo-8G-fso-pcodec
uv run python $benchmark_code $benchmark_recipe data/test-tissue-on-8G output/bench-tissue-on-8G-fso-pcodec
uv run python $benchmark_code $benchmark_recipe data/test-HeLa-8G output/bench-HeLa-8G-fso-pcodec
uv run python $benchmark_code $benchmark_recipe data/test-organoid-8G output/bench-organoid-8G-fso-pcodec
uv run python $benchmark_code $benchmark_recipe data/test-bacteria-8G output/bench-bacteria-8G-fso-pcodec

$benchmark_recipe="01_compression_benchmark/benchmark_recipe-htpack.toml"

uv run python $benchmark_code $benchmark_recipe data/test-embryo-8G output/bench-embryo-8G-htpack
uv run python $benchmark_code $benchmark_recipe data/test-tissue-on-8G output/bench-tissue-on-8G-htpack
uv run python $benchmark_code $benchmark_recipe data/test-bacteria-8G output/bench-bacteria-8G-htpack
uv run python $benchmark_code $benchmark_recipe data/test-HeLa-8G output/bench-HeLa-8G-htpack
uv run python $benchmark_code $benchmark_recipe data/test-organoid-8G output/bench-organoid-8G-htpack
