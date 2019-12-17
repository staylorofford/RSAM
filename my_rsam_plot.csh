#!/bin/csh
#my_rsam_plot.csh

set date = `date -u +%Y%m%d`
set monthdate = `date -u -d '1 month ago' +%Y%m%d`
set weekdate = `date -u -d '1 week ago' +%Y%m%d`
set daydate = `date -u -d '2 days ago' +%Y%m%d`

mkdir -p ./workdir/my_rsam
#WIZ.10-HHZ.NZ
#last month
python ./rsam_plot.py WIZ.10-HHZ.NZ ./workdir $monthdate $date ./workdir/my_rsam 1500 bp 2 5
\mv ./workdir/my_rsam/rsam_plot.png ./output/WIZ.rsam_plot_month.bp_2.00-5.00.png
\mv ./workdir/my_rsam/rsam_plot.svg ./output/WIZ.rsam_plot_month.bp_2.00-5.00.svg

#WIZ.10-HHZ.NZ
#last week
python ./rsam_plot.py WIZ.10-HHZ.NZ ./workdir $weekdate $date ./workdir/my_rsam 1500 bp 2 5
\mv ./workdir/my_rsam/rsam_plot.png ./output/WIZ.rsam_plot_week.bp_2.00-5.00.png
\mv ./workdir/my_rsam/rsam_plot.svg ./output/WIZ.rsam_plot_week.bp_2.00-5.00.svg

#WIZ.10-HHZ.NZ
#last 2 days
python ./rsam_plot.py WIZ.10-HHZ.NZ ./workdir $daydate $date ./workdir/my_rsam 1500 bp 2 5
\mv ./workdir/my_rsam/rsam_plot.png ./output/WIZ.rsam_plot_2days.bp_2.00-5.00.png
\mv ./workdir/my_rsam/rsam_plot.svg ./output/WIZ.rsam_plot_2days.bp_2.00-5.00.svg

#WSRZ.10-HHZ.NZ
#last month
python ./rsam_plot.py WSRZ.10-HHZ.NZ ./workdir $monthdate $date ./workdir/my_rsam 2780 bp 2 5
\mv ./workdir/my_rsam/rsam_plot.png ./output/WSRZ.rsam_plot2_month.bp_2.00-5.00.png
\mv ./workdir/my_rsam/rsam_plot.svg ./output/WSRZ.rsam_plot2_month.bp_2.00-5.00.svg

#WSRZ.10-HHZ.NZ
#last week
python ./rsam_plot.py WSRZ.10-HHZ.NZ ./workdir $weekdate $date ./workdir/my_rsam 2780 bp 2 5
\mv ./workdir/my_rsam/rsam_plot.png ./output/WSRZ.rsam_plot2_week.bp_2.00-5.00.png
\mv ./workdir/my_rsam/rsam_plot.svg ./output/WSRZ.rsam_plot2_week.bp_2.00-5.00.svg

#WSRZ.10-HHZ.NZ
#last 2 days
python ./rsam_plot.py WSRZ.10-HHZ.NZ ./workdir $daydate $date ./workdir/my_rsam 2780 bp 2 5
\mv ./workdir/my_rsam/rsam_plot.png ./output/WSRZ.rsam_plot2_2days.bp_2.00-5.00.png
\mv ./workdir/my_rsam/rsam_plot.svg ./output/WSRZ.rsam_plot2_2days.bp_2.00-5.00.svg