
export merge_code="03_visualization/merge_output_table.py"

uv run python $merge_code "output/bench-embryo-8G*/*.csv" output/merged-embryo-8G.csv
uv run python $merge_code "output/bench-tissue-on-8G*/*.csv" output/merged-tissue-on-8G.csv
uv run python $merge_code "output/bench-tissue-off-8G*/*.csv" output/merged-tissue-off-8G.csv
uv run python $merge_code "output/bench-organoid-8G*/*.csv" output/merged-organoid-8G.csv
uv run python $merge_code "output/bench-HeLa-8G*/*.csv" output/merged-HeLa-8G.csv
uv run python $merge_code "output/bench-bacteria-8G*/*.csv" output/merged-bacteria-8G.csv

# HTPack: append HTPack and FixedScaleOffset results to the merged tables above
uv run python $merge_code output/merged-embryo-8G.csv "output/bench-embryo-8G-htpack/*.csv" "output/bench-embryo-8G-fso*/*.csv" output/merged-embryo-8G-htpack.csv
uv run python $merge_code output/merged-tissue-on-8G.csv "output/bench-tissue-on-8G-htpack/*.csv" "output/bench-tissue-on-8G-fso*/*.csv" output/merged-tissue-on-8G-htpack.csv
uv run python $merge_code output/merged-organoid-8G.csv "output/bench-organoid-8G-f32-htpack/*.csv" "output/bench-organoid-8G-f32-fso*/*.csv" output/merged-organoid-8G-htpack.csv
uv run python $merge_code output/merged-HeLa-8G.csv "output/bench-HeLa-8G-f32-htpack/*.csv" "output/bench-HeLa-8G-f32-fso*/*.csv" output/merged-HeLa-8G-htpack.csv
uv run python $merge_code output/merged-bacteria-8G.csv "output/bench-bacteria-8G-htpack/*.csv" "output/bench-bacteria-8G-fso*/*.csv" output/merged-bacteria-8G-htpack.csv
