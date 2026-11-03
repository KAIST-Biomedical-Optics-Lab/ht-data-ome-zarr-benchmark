import argparse
import glob
import pandas as pd
import os


def rename_squeeze_filter_to_none(df):
    """
    Replace 'Squeeze' with 'none' and 'Squeeze-BitRound-14' with 'BitRound-14' in the 'filter option' column.
    """
    df["filter option"] = df["filter option"].replace(
        {"Squeeze": "none", "Squeeze-BitRound-14": "BitRound-14"}
    )
    return df


def merge_csv_files(input_glob, output_path):
    patterns = [input_glob] if isinstance(input_glob, str) else input_glob
    csv_files = [file for pattern in patterns for file in glob.glob(pattern)]
    if not csv_files:
        print(f"No CSV files found for pattern: {patterns}")
        return

    dataframes = []
    first_columns = None

    for file in csv_files:
        df = pd.read_csv(file)
        if first_columns is None:
            first_columns = list(df.columns)
        elif list(df.columns) != first_columns:
            print(f"Error: Column names in {file} do not match the first file.")
            return
        if not dataframes:
            dataframes.append(df)
        else:
            dataframes.append(df.iloc[1:])

    merged_df = pd.concat(dataframes, ignore_index=True)
    merged_df = rename_squeeze_filter_to_none(merged_df)

    # Write the merged DataFrame to a CSV file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    merged_df.to_csv(output_path, index=False)
    print(f"Merged CSV saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Merge multiple CSV files with the same columns into one CSV file."
    )
    parser.add_argument(
        "input_glob",
        nargs="+",
        help="Glob pattern(s) for input CSV files (e.g., './data/*.csv'). The first matched file is kept whole; the first row of the others is dropped.",
    )
    parser.add_argument("output_path", help="Path to save the merged CSV file")
    args = parser.parse_args()
    merge_csv_files(args.input_glob, args.output_path)


if __name__ == "__main__":
    main()
