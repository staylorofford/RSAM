#!/usr/bin/env python
# rsam_plot.py
# plot rsam data for one channel and filter type

import matplotlib
matplotlib.use('Agg')
from matplotlib.patches import Rectangle
import matplotlib.pyplot as plt
import datetime as dt
import math
from matplotlib.dates import date2num
from matplotlib.dates import num2date
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
from obspy.core import read, Trace, Stream
import sys
import os
import numpy as np
import scipy as sp
import pytz

# start here
if (len(sys.argv) < 8) | (len(sys.argv) > 10):
    sys.exit(
        "syntax rsam_plot.py site(DRZ.10-EHZ.CH) rsam_dir date1(yyyymmdd) date2(yyyymmdd) plot_dir basetriglev filter(lp,hp,bp,none) [f1 f2]")
else:
    site = sys.argv[1]
    rsam_dir = sys.argv[2]
    date1 = sys.argv[3]
    date2 = sys.argv[4]
    plot_dir = sys.argv[5]
    basetrig = sys.argv[6]
    plot_file = os.path.join(plot_dir, 'rsam_plot')
if len(sys.argv) == 8:  # filter = none
    filtype = sys.argv[7]
elif len(sys.argv) == 9:  # filter = lp or hp, one frequency given
    filtype = sys.argv[7]
    f = float(sys.argv[8])
elif len(sys.argv) == 10:  # filter = bp, two frequencies given
    filtype = sys.argv[7]
    f1 = float(sys.argv[8])
    f2 = float(sys.argv[9])

# site dir like DRZ.CH
site_dir = str.split(site, '.')[0] + '.' + str.split(site, '.')[2]

# format dates as datetime variables
d1 = dt.datetime.strptime(date1, '%Y%m%d')
yd1 = date2num(d1)
d2 = dt.datetime.strptime(date2, '%Y%m%d')
yd2 = date2num(d2)
yd2 = yd2 + 1  # so date range is inclusive
dates = num2date(np.arange(yd1, yd2, 1))

st = Stream()  # create empty stream
for date in dates:
    # get rsam file name
    yd = date.strftime("%Y.%j")
    if filtype == 'none':
        rsamfile = os.path.join(rsam_dir, site_dir, yd + '.' + site + '.rsam')
    elif (filtype == 'lp') | (filtype == 'hp'):
        strf = '%.2f' % f  # string version with 2 decimal places
        rsamfile = os.path.join(
            rsam_dir, site_dir, yd + '.' + site + '.' + filtype + '_' + strf + '.rsam')
    elif filtype == 'bp':
        strf1 = '%.2f' % f1  # string version with 2 decimal places
        strf2 = '%.2f' % f2  # string version with 2 decimal places
        rsamfile = os.path.join(
            rsam_dir, site_dir, yd + '.' + site + '.' + filtype + '_' + strf1 + '-' + strf2 + '.rsam')

    # process rsamfile
    if os.path.isfile(rsamfile):
        st += read(rsamfile)

# merge to single stream
st.merge(fill_value='interpolate')
tr = st[0]

# parse VAL data
val_changes, val_level_at_change = [], []
with open('/home/samto/PROCESSING/WIR/calendar_VAB.csv', 'r') as openfile:
    rc = 0
    for row in openfile:
        if rc == 0:
            rc += 1
            continue
        cols = row.split(',')
        val_changes.append(dt.datetime.strptime(cols[1] + '-' + cols[0],
                                                      '%Y-%b-%d'))
        val_level_at_change.append(cols[2][:-1])

# plot
start = date2num(tr.stats.starttime.datetime)  # as decimal years
end = date2num(tr.stats.endtime.datetime)


# build plot ticks
plot_range = (tr.stats.endtime.datetime - tr.stats.starttime.datetime).total_seconds() / 86400
tick_range = math.ceil(plot_range)
second_offset = 86400 - (tr.stats.starttime.datetime.hour * 3600 +
                         tr.stats.starttime.datetime.minute * 60 +
                         tr.stats.starttime.datetime.second +
                         tr.stats.starttime.datetime.microsecond / 1000000)
xticks = []
xtick_labels = []
for n in range(tick_range):
    xticks.append((tr.stats.starttime.datetime + dt.timedelta(seconds=second_offset) + dt.timedelta(days=n)).astimezone(pytz.timezone('Pacific/Auckland')).date())
    if n % 2 == 0:
        xtick_labels.append(str(xticks[-1]))
    else:
        xtick_labels.append('')

# add end time of data to val change calendar for plotting clarity
val_changes.append(tr.stats.endtime.datetime)
val_level_at_change.append(val_level_at_change[-1])

# time values
#t = np.arange(start, end, tr.stats.delta/86400)
t = sp.linspace(start, end, tr.stats.npts)

# plot
#date and time
now = dt.datetime.now()

#base trigger level string for title
if basetrig == '0':
  basetrig = 'null'

if filtype == 'none':
    title = 'RSAM: ' + site + ', date: ' + date1 + '-' + date2 + \
        ' UT, filter: ' + filtype + ', plotted at: ' + \
            now.strftime("%Y-%m-%d %H:%M") + ', BTL = ' + basetrig
elif (filtype == 'lp') | (filtype == 'hp'):
    title = 'RSAM: ' + site + ', date: ' + date1 + '-' + date2 + ' UT, filter: ' + \
        filtype + ' ' + strf + ' Hz' + ', plotted at: ' + \
            now.strftime("%Y-%m-%d %H:%M") + ', BTL = ' + basetrig
elif filtype == 'bp':
    title = 'RSAM: ' + site + ', date: ' + date1 + '-' + date2 + ' UT, filter: ' + filtype + \
        ' ' + strf1 + ' - ' + strf2 + ' Hz' + \
            ', plotted at: ' + now.strftime("%Y-%m-%d %H:%M") + ', BTL = ' + basetrig
fig = plt.figure(figsize=(15, 5))
plt.axes([0.1, 0.2, 0.85, 0.7])

maxy = 1.1 * tr.data.max()
plt.ylim(bottom=0, top=maxy)

#base trigger level on plot, if in scale
if basetrig != 'null':
  bt = float(basetrig)
  half = bt / 2
  plt.axhline(y=bt, linestyle='--', color = 'red', label='RSAM alert value')
  #colour areas based on relation to BTL
  plt.axhspan(0, half, alpha=0.1, color='green', label='Green RSAM zone') #low rectangle
  plt.axhspan(half, bt, alpha=0.1, color='orange', label='Orange RSAM zone') #moderate rectangle
  plt.axhspan(bt, 100000, alpha=0.1, color='red', label='Red RSAM zone') #high rectangle

plt.plot_date(t, tr.data, linewidth=1, linestyle='-', marker='None', color='black', label='RSAM')

# Plot VAL calendar
plt.vlines(val_changes, 0, 999999, linestyles='dashed', color='black', label='VAL change')
for n in range(len(val_changes) - 1):
    if int(val_level_at_change[n - 1]) < 3 and int(val_level_at_change[n]) == 4:  # Catch when an eruption occurs
        plt.annotate(s='VAL ' + val_level_at_change[n],
                     xy=(val_changes[n],
                         maxy - maxy/11),
                     xytext=(val_changes[n] + dt.timedelta(hours=12),
                             maxy - 2 * maxy/10),
                     bbox={'boxstyle': 'square',
                           'fc': '1',
                           'alpha': 0.8},
                     arrowprops={'facecolor': 'black',
                                 'arrowstyle': '->',
                                 'relpos': (0, 0.5)})
    else:
        plt.annotate(s='VAL ' + val_level_at_change[n],
                     xy=(val_changes[n],
                         maxy - maxy/11),
                     xytext=(val_changes[n] + dt.timedelta(seconds=(val_changes[n + 1] - val_changes[n]).total_seconds() / 2),
                             maxy - maxy/10),
                     bbox={'boxstyle': 'square',
                           'fc': '1',
                           'alpha': 0.8},
                     arrowprops={'facecolor': 'black',
                                 'arrowstyle': '->',
                                 'relpos': (0, 0.5)})

# Add eruption box

eruption_dt = dt.datetime.strptime('2019-12-09T01:11:47Z',
                                   '%Y-%m-%dT%H:%M:%SZ')
rect = Rectangle(xy=(eruption_dt - dt.timedelta(hours=6), 0),
                 width=(dt.timedelta(hours=12)),
                 height=maxy + maxy/20,
                 fill=True,
                 color='red',
                 alpha=0.2)
plt.gca().add_patch(rect)
plt.text(s='Eruption',
         x=eruption_dt,
         y=maxy,
         horizontalalignment='center',
         bbox={'boxstyle': 'square',
               'fc': '1',
               'alpha': 0.8},
         fontdict={'fontsize': 12,
                   'weight': 'bold',
                   'color': 'red'})

# plt.title(title)
plt.title('RSAM at ' + site + ' between frequencies ' + strf1 + '-' + strf2 + ' Hz',
          y=1.03,
          fontdict={'fontsize': 14})
plt.yticks(plt.gca().get_yticks(),
           fontsize=12)
plt.ylabel('ground velocity (nm/s)',
           fontsize=14,
           labelpad=10)
plt.xticks(ticks=xticks,
           labels=xtick_labels,
           rotation=30,
           ha='right',
           fontsize=12)
plt.xlabel('time',
           fontsize=14,
           labelpad=5)
plt.xlim(t[0], t[-1])

plt.legend(loc='upper left')

plt.savefig(plot_file + '.png', dpi=600, fmt='png')
plt.savefig(plot_file + '.svg', dpi=600, fmt='svg')
# plt.show()
