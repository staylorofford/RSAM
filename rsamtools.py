#!/usr/bin/env python

"""
Sam Taylor-Offord's amalgamation of Steve Sherburn's RSAM codes.
"""

import argparse
import datetime
import math
import matplotlib
matplotlib.use('Agg')
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
import urllib


# Parse arguments from command line

parser = argparse.ArgumentParser()
parser.add_argument('--streams', type=str, help='Streams(s) to calculate and/or plot RSAM data for. Format is a comma-separated list of NETWORK.SITE.LOC.CHANNEL strings, e.g. NZ.WIZ.10.HHZ,NZ.WSRZ.10.HHZ')
parser.add_argument('--date', type=str, help='Date to calculate RSAM on and/or to produce plots relative to. Format is YYYYMMDD in UTC.')
parser.add_argument('--response', action='store_true', help='Whether to remove instrument response before RSAM calculation.')
parser.add_argument('--filter-ranges', type=int, help='Frequency range to filter the data to, set either bound to None to apply no filtering on that bound. Give a comma-separated list of frequency bounds to produce multiple RSAM timeseries, e.g. [0,5],[5,10]')
args = parser.parse_args()

# Set up timing

date = datetime.datetime.strptime(args.date, '%Y%m%d')
start = UTCDateTime(date)
end = start + 86400

# Run through each stream

streams = args.sites.split(',')
for stream in streams:

    if stream.split('.')[0] == 'NZ':  # If the network is New Zealand
        try:  # First try the near real time FDSN service for waveforms
            client = Client(base_url='service-nrt.geonet.org.nz')
            stream = client.get_waveforms(stream.split('.')[0],
                                          stream.split('.')[1],
                                          stream.split('.')[2],
                                          stream.split('.')[3],
                                          start,
                                          end,
                                          attach_response=True)
        except:  # If this fails, try the archive FDSN service
            try:
                client = Client(base_url='service.geonet.org.nz')
                stream = client.get_waveforms(stream.split('.')[0],
                                              stream.split('.')[1],
                                              stream.split('.')[2],
                                              stream.split('.')[3],
                                              start,
                                              end,
                                              attach_response=True)
            except:  # If this fails, the data does not exist
                sys.stderr.write('No data found for ' + stream + '\n')
                sys.exit(0)
    else:
        raise Exception('This code only has functionality for data from the NZ network.')

    # Remove instrument response and, if the stream has multiple traces, ensure there are no gaps in the data

    if args.response:
        stream.remove_sensitivity()
    stream.merge(fill_value='interpolate')

    # Get metadata from stream

    station = stream[0].stats.station
    network = stream[0].stats.network
    location = stream[0].stats.location
    channel = stream[0].stats.channel
    starttime = stream[0].stats.starttime
    endtime = stream[0].stats.endtime

    # Generate RSAM file

    frequency_ranges = args.filter_ranges.split('[,]')
    for frequency_range in frequency_ranges:

        data = np.zeros(145)  # Initialise data array

        # Build RSAM output file name

        frequency_bounds = frequency_range.split(',')
        if not frequency_bounds[0] and not frequency_bounds[1]:
            file_name = date.strftime("%Y.%j") + '.' + stream + '.rsam'
        elif frequency_bounds[0] and not frequency_bounds[1]:
            filter_type = 'lowpass'
            lower_bound = '%.2f' % float(frequency_bounds[0])  # String of lower frequency bound to 2 decimal places
            file_name = date.strftime("%Y.%j") + '.' + stream + '.low_pass_' + lower_bound + '.rsam'
        elif frequency_bounds[1] and not frequency_bounds[0]:
            filter_type = 'highpass'
            upper_bound = '%.2f' % float(frequency_bounds[0])  # String of upper frequency bound to 2 decimal places
            file_name = date.strftime("%Y.%j") + '.' + stream + '.high_pass_' + upper_bound + '.rsam'
        elif frequency_bounds[0] and frequency_bounds[1]:
            filter_type = 'bandpass'
            lower_bound = '%.2f' % float(frequency_bounds[0])  # String of lower frequency bound to 2 decimal places
            upper_bound = '%.2f' % float(frequency_bounds[0])  # String of upper frequency bound to 2 decimal places
            file_name = date.strftime("%Y.%j") + '.' + stream + '.band_pass_' + lower_bound + '-' + upper_bound + '.rsam'
        rsam_data_path = './rsam_files/' + stream
        rsam_file_path = rsam_data_path + '/' + file_name

        # Make RSAM data folder if required

        if not os.path.exists(rsam_data_path):
            os.makedirs(rsam_data_path)

        # Perform RSAM calculation

        t = starttime
        tr = stream[0].data
        index = 0

        # Loop through data in 600sec (10 min) blocks until loop goes through all data

        while t < endtime:

            tr_10m = stream[0].slice(t, t + 600)
            duration = tr_10m.stats.npts * tr_10m.stats.delta

            if duration >= 500:
                if duration < 600:
                    tr_10m = tr.slice(endtime - 600, endtime)

                # Detrend and filter data

                tr_10m.detrend(type='constant')

                if filter_type == 'lowpass':
                    tr_10m.filter('lowpass',
                                  freq=lower_bound,
                                  corners=4,
                                  zerophase=False)
                elif filter_type == 'highpass':
                    tr_10m.filter('highpass',
                                  freq=upper_bound,
                                  corners=4,
                                  zerophase=False)
                elif filter_type == 'bandpass':
                    tr_10m.filter('bandpass',
                                  freqmin=lower_bound,
                                  freqmax=upper_bound,
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
        stream = Stream([Trace(data=data,
                               header=stats)])
        stream.write(rsam_file_path,
                     format='MSEED',
                     reclen=256)
