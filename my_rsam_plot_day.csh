#!/bin/csh
#my_rsam_plot_day.csh

set last_year = `date -u -d '1 year ago' +%Y`
set this_year = `date -u +%Y`

#WIZ.10-HHZ.NZ
set first_year = 2007
python ./rsam_plot_day.py WIZ.10-HHZ.NZ ./workdir $first_year $this_year ./workdir/my_rsam bp 2 5
\mv ./workdir/my_rsam/rsam_plot_day.png ./output/WIZ.rsam_plot_day.bp_2.00-5.00.png
\mv ./workdir/my_rsam/rsam_plot_day.svg ./output/WIZ.rsam_plot_day.bp_2.00-5.00.svg

#WSRZ.10-HHZ.NZ
set first_year = 2013
python ./rsam_plot_day.py WSRZ.10-HHZ.NZ ./workdir $first_year $this_year ./workdir/my_rsam bp 2 5
\mv ./workdir/my_rsam/rsam_plot_day.png ./output/WSRZ.rsam_plot2_day.bp_2.00-5.00.png
\mv ./workdir/my_rsam/rsam_plot_day.svg ./output/WRSZ.rsam_plot2_day.bp_2.00-5.00.svg