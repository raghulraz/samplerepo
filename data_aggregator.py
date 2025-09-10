import argparse
import pandas as pd
import numpy as np
import re
import sys
import matplotlib.pyplot as plt
from scipy import stats as sp_stats


class TimeSeriesAggregator:
    def __init__(self, file_path: str, group_by: str, stats: list, columns: list = None, 
                 timefrom: int = None, timeto: int = None, plot: bool = False):
        self.file_path = file_path
        self.group_by = group_by
        self.stats = stats
        self.columns = columns
        self.timefrom = timefrom
        self.timeto = timeto
        self.plot_enabled = plot
        self.df = None
        self.grouped = None
        self.col_map = {}


    def normalize_col_name(self, col: str) -> str:
        """Convert column name to a simplified format for matching."""
        col = col.lower()
        col = re.sub(r"[^a-z]+", "", col)  # keep only letters
        return col

    def map_columns(self, requested_cols):
        """Map simplified CLI names to actual Excel column names."""
        mapped = []
        for req in requested_cols:
            norm_req = self.normalize_col_name(req)
            match = next((v for k, v in self.col_map.items() if norm_req in k), None)
            if match:
                mapped.append(match)
            else:
                print(f"⚠ Column not found in Excel: {req}")
        return mapped

    def load_and_merge_excel(self) -> pd.DataFrame:
        """Load multiple sheets and merge them into one DataFrame."""
        xls = pd.ExcelFile(self.file_path)
        merged_df = None
        count = 0
        for sheet in xls.sheet_names:
            if count == 2:  # custom skip logic
                print(f"Skipping sheet: {sheet}")
                continue

            device_name = sheet.replace("Input ", "").rsplit("_", 1)[0].strip()
            df = pd.read_excel(self.file_path, sheet_name=sheet)
            df["Date Time"] = pd.to_datetime(df["Date Time"], errors="coerce")

            # Keep original column names but store normalized mapping
            for col in df.columns:
                if col != "Date Time":
                    prefixed_col = f"{device_name}_{col}"  # keep original with prefix
                    df.rename(columns={col: prefixed_col}, inplace=True)

                    # Store mapping: normalized CLI name → prefixed column name
                    norm_name = self.normalize_col_name(prefixed_col)
                    self.col_map[norm_name] = prefixed_col

            if merged_df is None:
                merged_df = df
            else:
                merged_df = pd.merge(merged_df, df, on="Date Time", how="outer")
            count += 1

        self.df = merged_df
        return self.df

    def apply_time_filters(self):
        """Filter rows based on optional epoch ms time range."""
        if self.timefrom:
            self.df = self.df[self.df["Date Time"] >= pd.to_datetime(self.timefrom, unit="ms")]
        if self.timeto:
            self.df = self.df[self.df["Date Time"] <= pd.to_datetime(self.timeto, unit="ms")]
        print(f"Rows after time filter: {len(self.df)}")
        return self.df

    def aggregate_data(self) -> pd.DataFrame:
        """Aggregate data using the specified statistics and grouping."""
        df = self.df.set_index("Date Time")

        # Map requested columns to actual Excel columns
        if self.columns:
            available = self.map_columns(self.columns)
            if not available:
                raise ValueError(f"No requested columns matched: {self.columns}")
            df = df[available]

        numeric_cols = df.select_dtypes(include=[np.number]).columns
        non_numeric_cols = df.select_dtypes(exclude=[np.number]).columns

        agg_funcs = {}
        for col in numeric_cols:
            funcs = []
            for s in self.stats:
                if s == "min":
                    funcs.append("min")
                elif s == "max":
                    funcs.append("max")
                elif s == "mean":
                    funcs.append("mean")
                elif s == "median":
                    funcs.append("median")
                elif s == "mode":
                    funcs.append(lambda x: sp_stats.mode(x, keepdims=True).mode[0] if len(x) > 0 else np.nan)
            agg_funcs[col] = funcs

        for col in non_numeric_cols:
            agg_funcs[col] = "last"

        grouped = df.resample(self.group_by.lower()).agg(agg_funcs)

        # Flatten multi-index columns
        new_columns = []
        for col in grouped.columns.to_flat_index():
            if isinstance(col, tuple):
                colname, stat = col
                new_columns.append(f"{colname}_{stat}" if len(self.stats) > 1 else colname)
            else:
                new_columns.append(col)
        grouped.columns = new_columns

        self.grouped = grouped.reset_index()
        return self.grouped

    def save_results(self, output_file="aggregated_output.csv"):
        self.grouped.to_csv(output_file, index=False)
        print(self.grouped.head())
        print(f"Aggregated data saved to {output_file}")

    def plot_results(self):
        """Plot numeric columns if plotting is enabled, using original Excel names."""
        if not self.plot_enabled:
            return
        numeric_cols = self.grouped.select_dtypes(include=[np.number]).columns
        if numeric_cols.empty:
            print("⚠ No numeric columns to plot.")
            return

        plt.figure(figsize=(12, 6))
        for col in numeric_cols:
            # Map back to original prefixed Excel name
            original_name = next((v for k, v in self.col_map.items() if v in col), col)
            plt.plot(self.grouped["Date Time"], self.grouped[col], label=original_name)

        plt.xlabel("Date Time")
        plt.ylabel("Values")
        plt.title("Time-Series Aggregated Data")
        plt.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    def run(self):
        self.load_and_merge_excel()
        self.apply_time_filters()
        self.aggregate_data()
        self.save_results()
        self.plot_results()

def interactive_menu():
    print("=== Time-Series Aggregator Interactive Menu ===")
    file_path = input("Enter path to Excel file: ").strip()
    group_by = input("Enter grouping interval (e.g., 1h, 30T, 1D): ").strip()
    
    stats = input("Enter stats to compute (min, max, mean, median, mode) separated by space [default=mean]: ").strip()
    stats_list = stats.split() if stats else ["mean"]

    columns = input("Enter columns to include (short names) separated by space [press Enter for all]: ").strip()
    columns_list = columns.split() if columns else None

    timefrom = input("Enter start time in epoch ms (optional): ").strip()
    timefrom = int(timefrom) if timefrom else None

    timeto = input("Enter end time in epoch ms (optional): ").strip()
    timeto = int(timeto) if timeto else None

    plot_input = input("Enable plotting? (y/n) [default=n]: ").strip().lower()
    plot = plot_input == "y"

    return {
        "file_path": file_path,
        "group_by": group_by,
        "stats": stats_list,
        "columns": columns_list,
        "timefrom": timefrom,
        "timeto": timeto,
        "plot": plot
    }

def main():
    if len(sys.argv) > 1:
        # Use argparse if command-line args are provided
        parser = argparse.ArgumentParser(description="Time-Series Data Aggregator")
        parser.add_argument("--input", required=True, help="Input Excel file path")
        parser.add_argument("--group-by", required=True, help="Grouping interval, e.g., 1h, 30T, 1D")
        parser.add_argument("--stats", nargs="+", default=["mean"], help="Stats to compute (min, max, mean, median, mode)")
        parser.add_argument("--columns", nargs="*", help="Columns to include (short names)")
        parser.add_argument("--timefrom", type=int, help="Start time in epoch ms (optional)")
        parser.add_argument("--timeto", type=int, help="End time in epoch ms (optional)")
        parser.add_argument("--plot", action="store_true", help="Enable plotting of results")
        args = parser.parse_args()
        params = {
            "file_path": args.input,
            "group_by": args.group_by,
            "stats": args.stats,
            "columns": args.columns,
            "timefrom": args.timefrom,
            "timeto": args.timeto,
            "plot": args.plot
        }
    else:
        # Otherwise, use interactive menu
        params = interactive_menu()

    aggregator = TimeSeriesAggregator(**params)
    aggregator.run()

if __name__ == "__main__":
    main()
