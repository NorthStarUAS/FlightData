import os

import aura_csv
import aura_txt
import px4_sdlog2
import px4_ulog
import sentera
import sentera2
import umn1_mat
import umn3_hdf5

def load(path, recal_file=None):
    flight_data = {}
    flight_format = None

    (root, ext) = os.path.splitext(path)
    aura_csv_path = os.path.join(path, 'imu-0.csv')
    aura_txt_path = os.path.join(path, 'imu-0.txt')
    ulog_path = path + '_sensor_combined_0.csv'
    sentera_path = os.path.join(path, 'imu.csv')
    
    # determine the data log format and call the corresponding loader code
    
    if os.path.exists(aura_csv_path):
        # aura csv format
        print 'Detected aura csv format.'
        flight_data = aura_csv.load(path, recal_file)
        flight_format = 'aura_csv'
    elif os.path.exists(aura_txt_path):
        # aura txt format
        print 'Detected aura text format.'
        flight_data = aura_txt.load(path, recal_file)
        flight_format = 'aura_txt'
    elif ext == '.mat':
        # umn1
        print 'Detected umn1 format.'
        print 'Notice: assuming umn1 .mat format'
        flight_data = umn1_mat.load(path)
        flight_format = 'umn1'
    elif ext == '.h5' or ext == '.hdf5':
        # umn3 (hdf5)
        print 'Detected umn3 (hdf5) format.'
        flight_data = umn3_hdf5.load(path)
        flight_format = 'umn3'
    elif os.path.exists(ulog_path):
        # px4_ulog
        print 'Detected px4 ulog (csv family of files) format.'
        flight_data = px4_ulog.load(path)
        flight_format = 'px4_ulog'
    elif ext == '.csv':
        # px4 sdlog2
        print 'Detected px4 ulog (single csv file) format.'
        flight_data = px4_sdlog2.load(path)
        flight_format = 'px4_sdlog2'
    elif os.path.exists(sentera_path):
        # sentera1 or sentera2
        print 'Detected sentera format.'
        print 'Notice: assuming original sentera camera format'
        flight_data = sentera.load(path)
        # imu_data, gps_data, air_data, filter_data = sentera2.load(path)
        flight_format = 'sentera'
    else:
        print "Unable to determine data log format (or path not valid):", path

    return flight_data, flight_format
