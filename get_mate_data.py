#!/opt/local/bin/python

import telnetlib
import csv
import datetime
import h5py

state_decoder = {
    0: 'Silent',
    1: 'Float',
    2: 'Bulk',
    3: 'Absorb',
    4: 'Equalize'
}

tn = telnetlib.Telnet("12.203.85.9",10002)
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

time_string = '{0:%Y-%m-%d\t%H:%M:%S}'.format(datetime.datetime.now())

pv_volts = int(mate_array[4])
pv_amps = int(mate_array[3])
bat_volts = int(mate_array[10])/10.
bat_amps = int(mate_array[2])
kwh = int(mate_array[5])
state = int(mate_array[9])

translated = '%s:\tSolar:\t%d,\t%d;\tBattery\t%f,\t%d;\tKWH:\t%d\tState:\t%s\n' % \
             (time_string, pv_volts, pv_amps,
              bat_volts, bat_amps, kwh, state_decoder.get(state))

print(translated)

with open('mate_data.tsv', 'a') as file:
    file.write(translated)

'''
with h5py.File('mate_data.h5, 'w') as f:
            if first:
                coord = f.create_dataset('coord', maxshape=(2, None, 3), data=[tracks.hit_pos.T, tracks.means.T],
                                         chunks=True)
                uncert = f.create_dataset('sigma', maxshape=(None,), data=tracks.sigmas, chunks=True)
                arr.append(tracks.sigmas.shape[0])
                f.create_dataset('r_lens', data=tracks.lens_rad)
            else:
                coord.resize(coord.shape[1] + tracks.means.shape[1], axis=1)
                coord[:, -tracks.means.shape[1]:, :] = [tracks.hit_pos.T, tracks.means.T]
                uncert.resize(uncert.shape[0] + tracks.sigmas.shape[0], axis=0)
                uncert[-tracks.sigmas.shape[0]:] = tracks.sigmas
                arr.append(uncert.shape[0])
        first = False
'''