#!/usr/bin/python

import telnetlib
import csv
import datetime
import h5py
from dateutil import tz
import time

# See: https://stackoverflow.com/questions/2801882/generating-a-png-with-matplotlib-when-display-is-undefined
import matplotlib
#matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

state_decoder = {
    0: 'Silent',
    1: 'Float',
    2: 'Bulk',
    3: 'Absorb',
    4: 'Equalize'
}


# Append data to an hdf5 table.  Will create the table if necessary.
# There must be a better way to do this!!
def append_data_to_table(h5file, table_name, data, data_type):
    if not table_name in h5file:
        h5file.create_dataset(table_name, data=[data], dtype=data_type, maxshape=(None,))
    else:
        table = h5file[table_name]
        cur_size = len(table)
        # print('cur_size: %i, shape: %s' % (cur_size, str(np.shape(pvv_table))))
        table.resize(cur_size + 1, axis=0)
        table[cur_size] = data

def plot(h5file, times, slice_to_plot=None):
    figure, ax = plt.subplots()
    figure.set_size_inches(12, 6)
    if (slice_to_plot == None):
        slice_to_plot = slice(0,len(times))
    times_to_plot = times[slice_to_plot]
    ax.plot(times_to_plot, h5file['batt_volts'][slice_to_plot], label="Batt volts")
    plt.legend(loc=2)
    plt.grid()
    ax.fmt_xdata = mdates.DateFormatter('%Y-%m-%d')  # Why aint this working??
    figure.autofmt_xdate()

    plt.twinx()
    ''' This was cleaner until we needed to slice the data
    plt.plot(times_to_plot, 'batt_amps', data=h5file, label="Batt amps", color='red')
    plt.plot(times_to_plot, 'kwh', data=h5file, label="KWH", color='orange')
    plt.plot(times_to_plot, 'state', data=h5file, label="State", color='green')
    '''
    plt.plot(times_to_plot, h5file['batt_amps'][slice_to_plot], label="Batt amps", color='red')
    plt.plot(times_to_plot, h5file['kwh'][slice_to_plot], label="KWH", color='orange')
    plt.plot(times_to_plot, h5file['state'][slice_to_plot], label="State", color='green')
    plt.legend(loc=1)
    plt.show()
    return plt


if __name__=='__main__':

    tn = telnetlib.Telnet("12.97.65.162",10002)
    blank = tn.read_until("\n")
    mate_output = tn.read_until("\n")   # Read one line of old data that may be stuck in the Lantronix
    print('Throwaway line: %s' % mate_output)
    mate_output = tn.read_until("\n")
    while len(mate_output) != 49:
        print('Bad mate data: %d: %s' % (len(mate_output), mate_output))
        mate_output = tn.read_until("\n")
    tn.close()
    print(mate_output)

    mate_reader = csv.reader([mate_output])
    mate_list_of_lists = list(mate_reader)
    mate_array = mate_list_of_lists[0]

    # Auto-detect zones:
    from_zone = tz.tzutc()
    to_zone = tz.gettz('US/Pacific') # Daylight saving?

    utc = datetime.datetime.utcnow()

    # Tell the datetime object that it's in UTC time zone since
    # datetime objects are 'naive' by default
    utc = utc.replace(tzinfo=from_zone)

    # Convert time zone
    local = utc.astimezone(to_zone)
    time_string = '{0:%Y-%m-%d\t%H:%M:%S\t%Z}'.format(local)

    pv_volts = int(mate_array[4])
    pv_amps = int(mate_array[3])
    bat_volts = int(mate_array[10])/10.
    bat_amps = int(mate_array[2])
    kwh = int(mate_array[5])/10.
    state = int(mate_array[9])

    translated = '%s\tSolar:\t%d\t%d\tBattery:\t%s\t%d\tKWH:\t%s\tState:\t%s\n' % \
                 (time_string, pv_volts, pv_amps,
                  format(bat_volts, '.1f'), bat_amps, format(kwh, '.1f'), state_decoder.get(state))

    print(translated)

    # Note: the script must be run from the directory where this file is located
    with open('mate_data.tsv', 'a') as file:
        file.write(translated)

    with h5py.File('mate_data.h5', 'a') as _h5f:     # Mode 'a' is the default

        append_data_to_table(_h5f, 'timestamp', time.time(), 'float')   # Python 3 has much better support for timestamps -
                                                                       # this is currently not converted to anything...
        append_data_to_table(_h5f, 'pv_volts', pv_volts, 'int16')
        append_data_to_table(_h5f, 'pv_amps', pv_amps, 'int16')
        append_data_to_table(_h5f, 'batt_volts', bat_volts, 'float')
        append_data_to_table(_h5f, 'batt_amps', bat_amps, 'int16')
        append_data_to_table(_h5f, 'kwh', kwh, 'float')
        append_data_to_table(_h5f, 'state', state, 'int16')

        # TODO
        #   Display the proper time scale
        #   Scale the drawing right

        # For 2-axis plots see: https://matplotlib.org/2.0.1/examples/api/two_scales.html
        # To move legend outside of plot area (partially): https://stackoverflow.com/questions/4700614/how-to-put-the-legend-out-of-matplotlib-plot

        _times = []
        for time in _h5f['timestamp']:
            _times.append(datetime.datetime.fromtimestamp(time))

        the_plot = plot(_h5f, _times, slice_to_plot=slice(-(12 * 24 * 14),0-1))    # Will -1 give the last data point??  Don't think so
        the_plot.savefig('mate.png', bbox_inches='tight')        # Use PDF for vectorized
        the_plot.savefig('mate.pdf', bbox_inches='tight')        # Use PDF for vectorized
