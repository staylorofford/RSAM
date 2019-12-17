#!/usr/bin/env bash

# Sam Taylor-Offord's wrapper for Steve Sherburn's RSAM code to run the RSAM calculation and plotting
# for White Island seismograms without using docker. To run this code you need to have all dependencies
# of the RSAM code setup and the code must be executed from the RSAM git repository root. Note that the operator
# must be using the modified version of the RSAM code which excludes all non-White Island stations and is in Python3.

# Set daterange if rsam needs to be calculated over more than one UTC day

startdate=`date -u +%Y%m%d`
enddate=`date -u +%Y%m%d`

mkdir -p ./output

# Convert start and end times into useful formats

startstr=`echo ${startdate} | awk '{printf"%4d-%02d-%02d",substr($1,1,4),substr($1,5,2),substr($1,7,2)}'`
starttimes=(${startstr//-/ })

endstr=`echo ${enddate} | awk '{printf"%4d-%02d-%02d",substr($1,1,4),substr($1,5,2),substr($1,7,2)}'`
endtimes=(${startstr//-/ })

# Prepare time variables: decrease of 1hour here to allow for a correct loop (and hour increment) in the while loop below

data=`date -d "$startstr -1day" +%Y%m%d`
dateend=`date -d "$endstr -1day" +%Y%m%d`

# Calculate RSAM values over time period

while [ $data -le $dateend ]; do
    incr=`echo $data | awk '{printf"%4d-%02d-%02d",substr($1,1,4),substr($1,5,2),substr($1,7,2)}'`
    data=`date -d "$incr +1day" +%Y%m%d`
    yyyymm=`echo $data | awk '{print substr($1,1,6)}'`
    dd=`echo $data | awk '{print substr($1,7,2)}'`
    ./my_rsam.sh -d ${data}
done

./my_rsam_plot.csh
./my_rsam_day.sh  # Uncomment this row to calculate daily average RSAM values - requires RSAM data for each day
./my_rsam_plot_day.csh  # Uncomment this row to plot daily average RSAM values - requires prior line to run