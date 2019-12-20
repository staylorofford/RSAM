#!/usr/bin/env python

"""
Sam Taylor-Offord's amalgamation of Steve Sherburn's RSAM codes.

Can calculate an indefinite range of filtered RSAM timeseries, but can only plot 4 such filtered timeseries at once.
"""

import argparse
import datetime
import math
import matplotlib
matplotlib.use('Agg')
linestyles = ['-', '--', '-.', ':']
from matplotlib.dates import date2num
from matplotlib.dates import num2date
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from obspy.core import read, Trace, Stream, UTCDateTime
from obspy.clients.fdsn import Client
import os
import pytz
import scipy as sp
import sys


# Parse arguments from command line

parser = argparse.ArgumentParser()
parser.add_argument('--streams',
                    type=str,
                    help='Streams(s) to calculate and/or plot RSAM data for. Format is a comma-separated list of '
                         'NETWORK.SITE.LOC.CHANNEL strings, e.g. NZ.WIZ.10.HHZ,NZ.WSRZ.10.HHZ')
parser.add_argument('--date',
                    type=str,
                    help='Date to calculate RSAM on and/or to produce plots relative to. Format is YYYYMMDD in UTC.')
parser.add_argument('--plot-days',
                    type=str,
                    help='Number of days to plot RSAM for prior to the given date.')
parser.add_argument('--calculate-plot-days',
                    action='store_true',
                    help='Whether to extend RSAM calculation to all days in the plotting period.')
parser.add_argument('--response',
                    action='store_true',
                    help='Whether to remove instrument response before RSAM calculation.')
parser.add_argument('--base-trig',
                    type=str,
                    help='Base trigger RSAM level - used for plotting.')
parser.add_argument('--filter-ranges',
                    type=str,
                    help='Frequency range to filter the data to, set either bound to None to apply no filtering on '
                         'that bound. Give a comma-separated list of frequency bounds to produce multiple RSAM '
                         'timeseries, e.g. [0,5],[5,10]')
args = parser.parse_args()

streams = args.streams.split(',')

# Set up number of calculation/plot days

num_plot_days = int(args.plot_days)
if args.calculate_plot_days:
    num_calculation_days = num_plot_days
else:
    num_calculation_days = 1

for n in range(num_calculation_days + 1):

    # Set up timing

    date = datetime.datetime.strptime(args.date, '%Y%m%d')
    start = UTCDateTime(date) - 86400 * n
    end = start + 86400

    for stream in streams:

        if stream.split('.')[0] == 'NZ':  # If the network is New Zealand
            try:  # First try the near real time FDSN service for waveforms
                client = Client('https://service-nrt.geonet.org.nz')
                st = client.get_waveforms(network=stream.split('.')[0],
                                          station=stream.split('.')[1],
                                          location=stream.split('.')[2],
                                          channel=stream.split('.')[3],
                                          starttime=start,
                                          endtime=end,
                                          attach_response=True)
                if st[0].stats.starttime - start > 600:
                    raise Exception('Tried nrt service, start time of data and as requested differ by more than '
                                    '10 minutes. Trying archive service...')
            except:  # If this fails, try the archive FDSN service
                try:
                    client = Client('https://service.geonet.org.nz')
                    st = client.get_waveforms(network=stream.split('.')[0],
                                              station=stream.split('.')[1],
                                              location=stream.split('.')[2],
                                              channel=stream.split('.')[3],
                                              starttime=start,
                                              endtime=end,
                                              attach_response=True)
                except:  # If this fails, the data does not exist
                    sys.stderr.write('No data found for ' + stream + ' on date ' + str(start)[:10] + '\n')
                    sys.exit(0)
        else:
            raise Exception('This code only has functionality for data from the NZ network.')

        # Remove instrument response and ensure there are no gaps in the data

        if args.response:
            st.remove_sensitivity()
        st.merge(fill_value='interpolate')

        # Generate RSAM file

        frequency_ranges = args.filter_ranges.split('],[')
        for frequency_range in frequency_ranges:
            frequency_bounds = frequency_range.replace('[', '').replace(']', '').split(',')

            print('Calculating 10-minute mean RSAM values for ' + stream +
                  ' between dates ' + str(start)[:10] + ' and ' + str(end)[:10] +
                  ' between frequency bounds ' + frequency_bounds[0] + '-' + frequency_bounds[1] + ' Hz')

            # Initialise data array

            data = np.zeros(145)

            # Define RSAM file name

            if not frequency_bounds[0] and not frequency_bounds[1]:
                filter_type = None
                file_name = start.strftime("%Y.%j") + '.' + stream + '.rsam'
            elif frequency_bounds[0] and not frequency_bounds[1]:
                filter_type = 'lowpass'
                lower_bound = '%.2f' % float(frequency_bounds[0])  # String of lower frequency bound to 2 decimal places
                file_name = start.strftime("%Y.%j") + '.' + stream + '.low_pass_' + lower_bound + '.rsam'
            elif frequency_bounds[1] and not frequency_bounds[0]:
                filter_type = 'highpass'
                upper_bound = '%.2f' % float(frequency_bounds[1])  # String of upper frequency bound to 2 decimal places
                file_name = start.strftime("%Y.%j") + '.' + stream + '.high_pass_' + upper_bound + '.rsam'
            elif frequency_bounds[0] and frequency_bounds[1]:
                filter_type = 'bandpass'
                lower_bound = '%.2f' % float(frequency_bounds[0])  # String of lower frequency bound to 2 decimal places
                upper_bound = '%.2f' % float(frequency_bounds[1])  # String of upper frequency bound to 2 decimal places
                file_name = start.strftime("%Y.%j") + '.' + stream + '.band_pass_' + lower_bound + '-' + upper_bound + \
                            '.rsam'
            rsam_data_path = './rsam_files/' + stream
            rsam_file_path = rsam_data_path + '/' + file_name

            # Make RSAM data folder if required

            if not os.path.exists(rsam_data_path):
                os.makedirs(rsam_data_path)

            # Get metadata from stream

            station = st[0].stats.station
            network = st[0].stats.network
            location = st[0].stats.location
            channel = st[0].stats.channel
            starttime = st[0].stats.starttime
            endtime = st[0].stats.endtime

            # Perform RSAM calculation

            t = starttime
            tr = st[0]
            index = 0

            # Loop through data in 600sec (10 min) blocks until loop goes through all data

            while t < endtime:

                tr_10m = tr.slice(t, t + 600)
                duration = tr_10m.stats.npts * tr_10m.stats.delta

                if duration >= 500:
                    if duration < 600:
                        tr_10m = tr.slice(endtime - 600, endtime)

                    # Detrend and filter data

                    tr_10m.detrend(type='constant')

                    if filter_type == 'lowpass':
                        tr_10m.filter('lowpass',
                                      freq=float(lower_bound),
                                      corners=4,
                                      zerophase=False)
                    elif filter_type == 'highpass':
                        tr_10m.filter('highpass',
                                      freq=float(upper_bound),
                                      corners=4,
                                      zerophase=False)
                    elif filter_type == 'bandpass':
                        tr_10m.filter('bandpass',
                                      freqmin=float(lower_bound),
                                      freqmax=float(upper_bound),
                                      corners=4,
                                      zerophase=False)

                    tr_10m.data = np.absolute(tr_10m.data)  # Convert data to absolute values
                    mean = tr_10m.data.mean()  # Take mean of data (RSAM value)

                    if args.response:
                        mean = mean / 1e-9  # Convert data to nanometres so dealing with whole numbers

                    # Assign RSAM value to data array

                    data[index] = mean
                    index += 1

                t += 600

            # Resize data array to remove any unused elements

            data = np.resize(data, index)

            # Write RSAM file in miniSEED format

            delta = 600  # 10 min windows between RSAM values
            stats = {'network': network,
                     'station': station,
                     'location': location,
                     'channel': channel,
                     'npts': len(data),
                     'delta': delta,
                     'mseed': {'dataquality': 'D'},
                     'starttime': starttime}
            out_st = Stream([Trace(data=data,
                             header=stats)])
            out_st.write(rsam_file_path,
                         format='MSEED',
                         reclen=256)

# Generate yearly RSAM files with daily mean RSAM values

for stream in streams:
    frequency_ranges = args.filter_ranges.split('],[')
    for frequency_range in frequency_ranges:
        frequency_bounds = frequency_range.replace('[', '').replace(']', '').split(',')

        print('Calculating daily mean RSAM values for ' + stream + ' between frequency bounds ' +
              frequency_bounds[0] + '-' + frequency_bounds[1] + ' Hz')

        # Define file name of yearly RSAM file

        if not frequency_bounds[0] and not frequency_bounds[1]:
            filter_type = None
            rsam_file_suffix = '.' + stream + '.rsam'
            year_file_name = str(date.year) + '.' + stream + '.rsam'
        elif frequency_bounds[0] and not frequency_bounds[1]:
            filter_type = 'lowpass'
            lower_bound = '%.2f' % float(frequency_bounds[0])  # String of lower frequency bound to 2 decimal places
            rsam_file_suffix = '.' + stream + '.low_pass_' + lower_bound + '.rsam'
            year_file_name = str(date.year) + '.' + stream + '.low_pass_' + lower_bound + '.rsam'
        elif frequency_bounds[1] and not frequency_bounds[0]:
            filter_type = 'highpass'
            upper_bound = '%.2f' % float(frequency_bounds[1])  # String of upper frequency bound to 2 decimal places
            rsam_file_suffix = '.' + stream + '.high_pass_' + upper_bound + '.rsam'
            year_file_name = str(date.year) + '.' + stream + '.high_pass_' + upper_bound + '.rsam'
        elif frequency_bounds[0] and frequency_bounds[1]:
            filter_type = 'bandpass'
            lower_bound = '%.2f' % float(frequency_bounds[0])  # String of lower frequency bound to 2 decimal places
            upper_bound = '%.2f' % float(frequency_bounds[1])  # String of upper frequency bound to 2 decimal places
            rsam_file_suffix = '.' + stream + '.band_pass_' + lower_bound + '-' + upper_bound + '.rsam'
            year_file_name = str(date.year) + '.' + stream + '.band_pass_' + lower_bound + '-' + upper_bound + '.rsam'
        year_rsam_file = './rsam_files/' + stream + '/' + year_file_name

        # Parse all RSAM files for the stream and frequency range and save their daily mean to the data array

        data = []
        starttime = None
        for jday in range(int(date.strftime("%j")) + 1):
            rsam_file_path = './rsam_files/' + stream + '/' + str(date.year) + '.' + str(jday) + rsam_file_suffix

            # If the RSAM file exists calculate the mean value for the day

            if os.path.isfile(rsam_file_path):

                # Read data file

                st = read(rsam_file_path)

                # In case stream has more than one trace, fill gaps

                st.merge(fill_value='interpolate')
                tr = st[0]
                if not starttime:
                    starttime = tr.stats.starttime

                # Save mean value for the day

                data.append(tr.data.mean())

            else:

                # File does not exist, assign a value of -1 as day value

                print("Can't find file %s" % rsam_file_path)
                data.append(-1)

        # If a yearly RSAM file exists already, delete it

        if os.path.isfile(year_rsam_file):
            os.unlink(year_rsam_file)

        # Start a new yearly RSAM file

        station = tr.stats.station
        network = tr.stats.network
        location = tr.stats.location
        channel = tr.stats.channel
        starttime = starttime
        delta = 86400  # One day interval
        npts = len(data)  # Number of days
        stats = {'network': network,
                 'station': station,
                 'location': location,
                 'channel': channel,
                 'npts': npts,
                 'delta': delta,
                 'mseed': {'dataquality': 'D'},
                 'starttime': starttime}
        out_st = Stream([Trace(data=np.array(data),
                               header=stats)])
        out_st.write(year_rsam_file,
                     format='MSEED',
                     reclen=256)

# Make RSAM plot folder if required

if not os.path.exists('./output/'):
    os.makedirs('./output')

# Plot RSAM data

for stream in streams:

    # Set plot dates

    yd1 = date2num(date - datetime.timedelta(days=num_plot_days)) + 1
    yd2 = date2num(date)
    dates = num2date(np.arange(yd1, yd2, 1))

    # Gather data for plotting

    frequency_ranges = args.filter_ranges.split('],[')
    frequency_banded_traces = []
    for frequency_range in frequency_ranges:
        frequency_bounds = frequency_range.replace('[', '').replace(']', '').split(',')

        print('Plotting 10-minute mean RSAM values for ' + stream +
              ' between dates ' + str(date - datetime.timedelta(days=num_plot_days))[:10] + ' and ' + str(date)[:10] +
              ' between frequency bounds ' + frequency_bounds[0] + '-' + frequency_bounds[1] + ' Hz')

        st = Stream()  # Create empty stream to fill with RSAM data over many days
        for d in dates:

            # Get RSAM file name for the date

            yd = d.strftime("%Y.%j")
            if not frequency_bounds[0] and not frequency_bounds[1]:
                filter_type = None
                file_name = d.strftime("%Y.%j") + '.' + stream + '.rsam'
            elif frequency_bounds[0] and not frequency_bounds[1]:
                filter_type = 'lowpass'
                lower_bound = '%.2f' % float(frequency_bounds[0])  # String of lower frequency bound to 2 decimal places
                file_name = d.strftime("%Y.%j") + '.' + stream + '.low_pass_' + lower_bound + '.rsam'
            elif frequency_bounds[1] and not frequency_bounds[0]:
                filter_type = 'highpass'
                upper_bound = '%.2f' % float(frequency_bounds[1])  # String of upper frequency bound to 2 decimal places
                file_name = d.strftime("%Y.%j") + '.' + stream + '.high_pass_' + upper_bound + '.rsam'
            elif frequency_bounds[0] and frequency_bounds[1]:
                filter_type = 'bandpass'
                lower_bound = '%.2f' % float(frequency_bounds[0])  # String of lower frequency bound to 2 decimal places
                upper_bound = '%.2f' % float(frequency_bounds[1])  # String of upper frequency bound to 2 decimal places
                file_name = d.strftime("%Y.%j") + '.' + stream + '.band_pass_' + lower_bound + '-' + upper_bound + \
                            '.rsam'

            # Process RSAM file

            if os.path.isfile('./rsam_files/' + stream + '/' + file_name):
                st += read('./rsam_files/' + stream + '/' + file_name)

        # Merge all RSAM data to a single stream

        st.merge(fill_value='interpolate')
        tr = st[0]

        # Put stream into frequency banded list of streams

        frequency_banded_traces.append(tr)

    # Prepare figure and axis

    fig = plt.figure(figsize=(15,
                              5))
    plt.axes([0.1,
              0.2,
              0.85,
              0.7])

    # Add base trigger level on plot

    if args.base_trig != 'null':
        bt = float(args.base_trig)
        half = bt / 2
        plt.axhline(y=bt,
                    linestyle='--',
                    color='red',
                    label='RSAM alert value')

        # Colour areas based on relation to BTL

        plt.axhspan(0,
                    half,
                    alpha=0.1,
                    color='green',
                    label='Weak RSAM zone')  # Weak rectangle
        plt.axhspan(half,
                    bt,
                    alpha=0.1,
                    color='orange',
                    label='Moderate RSAM zone')  # Moderate rectangle
        plt.axhspan(bt,
                    100000,
                    alpha=0.1,
                    color='red',
                    label='Strong RSAM zone')  # Strong rectangle

    # Plot data

    for n in range(len(frequency_banded_traces)):

        # Prepare start and end time for plotting

        start = date2num(frequency_banded_traces[n].stats.starttime.datetime)
        end = date2num(frequency_banded_traces[n].stats.endtime.datetime)

        # Build plot ticks

        plot_range = (frequency_banded_traces[n].stats.endtime.datetime -
                      frequency_banded_traces[n].stats.starttime.datetime).total_seconds() / 86400
        tick_range = math.ceil(plot_range)
        second_offset = 86400 - (frequency_banded_traces[n].stats.starttime.datetime.hour * 3600 +
                                 frequency_banded_traces[n].stats.starttime.datetime.minute * 60 +
                                 frequency_banded_traces[n].stats.starttime.datetime.second +
                                 frequency_banded_traces[n].stats.starttime.datetime.microsecond / 1000000)
        xticks = []
        xtick_labels = []
        for m in range(tick_range):
            xticks.append((frequency_banded_traces[n].stats.starttime.datetime +
                           datetime.timedelta(seconds=second_offset) +
                           datetime.timedelta(days=m)).astimezone(pytz.timezone('Pacific/Auckland')).date())
            if m % 2 == 0:
                xtick_labels.append(str(xticks[-1]))
            else:
                xtick_labels.append('')

        # Set time values

        t = sp.linspace(start,
                        end,
                        frequency_banded_traces[n].stats.npts)

        plt.plot_date(t,
                      frequency_banded_traces[n].data,
                      linewidth=1,
                      linestyle=linestyles[n],
                      marker='None',
                      color='black',
                      label=frequency_ranges[n].replace('[', '').split(',')[0] + '-' +
                            frequency_ranges[n].replace(']', '').split(',')[1] + ' Hz RSAM')

        # Add plot features

        plt.title('Real-Time Seismic Amplitude (RSAM: a measure of seismic energy) at Whakaari/White Island in the last ' +
                  str(num_plot_days) + ' days',
                  y=1.03,
                  fontdict={'fontsize': 14})
        plt.yticks(plt.gca().get_yticks(),
                   fontsize=12)
        plt.ylabel('ground velocity (nm/s)',
                   fontsize=14,
                   labelpad=10)
        plt.ylim(bottom=0,
                 top=1.1 * frequency_banded_traces[n].data.max())
        plt.xticks(ticks=xticks,
                   labels=xtick_labels,
                   rotation=30,
                   ha='right',
                   fontsize=12)
        plt.xlabel('date (NZT)',
                   fontsize=14,
                   labelpad=5)
        plt.xlim(t[0],
                 t[-1])
        plt.legend(loc='upper left')

    # Save plot to file

    plt.savefig('./output/' + stream.split('.')[1] + '.rsam_plot_' + str(num_plot_days) + '_days.png',
                dpi=400,
                fmt='png')

