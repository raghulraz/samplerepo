python data_aggregator.py --input DAC.xlsx --group-by "1H" --stats min --plot


--input	  
    Path to the Excel file containing the data	DAC.xlsx
--group-by
	Resampling interval (Pandas frequency string)	1h (hourly), 30T (30 minutes), 1D (daily)
--stats	
    List of statistics to calculate	min, mean, max, median, mode
--columns	
    Short names of columns to include (maps to actual Excel columns)	PH_DAC02_Humidity PH_DAC02_Temperature
--timefrom	
    Start time filter in epoch milliseconds	1748808000000
--timeto	
    End time filter in epoch milliseconds	1749067200000
--plot	
    Optional flag to generate a plot of numeric columns