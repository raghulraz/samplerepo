Data Aggregator Script

This Python script aggregates time-series data from Excel files, allows filtering by time, selecting columns, computing statistics, and optionally plotting the results.

python data_aggregator.py --input DAC.xlsx --group-by "1H" --stats min --plot

Arguments
Argument	Description	Example
--input	Path to the Excel file containing the data	DAC.xlsx
--group-by	Resampling interval (Pandas frequency string). Examples: hourly 1H, 30 minutes 30T, daily 1D	1H
--stats	List of statistics to calculate. Options: min, max, mean, median, mode	min
--columns	Short names of columns to include (maps to actual Excel columns)	PH_DAC02_Humidity PH_DAC02_Temperature
--timefrom	Start time filter in epoch milliseconds	1748808000000
--timeto	End time filter in epoch milliseconds	1749067200000
--plot	Optional flag to generate a plot of numeric columns	(no value needed)
Notes


Aggregated results are saved by default to aggregated_output.csv.

Including the --plot flag will display a chart of numeric columns over time.