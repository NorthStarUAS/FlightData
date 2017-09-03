import os

import aura_csv
import aura_txt
import px4_sdlog2
import px4_ulog
import sentera
import sentera2
import umn1_mat
import umn3_mat

def load(path, recal_file=None):
    flight_data = {}

    (root, ext) = os.path.splitext(path)
    aura_txt_path = os.path.join('imu-0.txt')
    aura_csv_path = os.path.join('imu-0.csv')
    ulog_path = path + '_sensor_combined_0.csv'
    sentera_path = os.path.join(path, 'imu.csv')
    
    # determine the data log format and call the corresponding loader code
    
    if os.path.isdir(aura_csv_path):
        # aura csv format
        print 'Discovered aura csv format.'
        flight_data = aura_csv.load(path, recal_file)
    elif os.path.isdir(aura_txt_path):
        # aura txt format
        print 'Discovered aura text format.'
        flight_data = aura_txt.load(path, recal_file)
    elif ext == '.mat':
        # umn1, umn3
        print 'Discovered umn1/umn3 format.'
        print 'Notice: assuming umn1 .mat format'
        flight_data = umn1_mat.load(path)
        #flight_data = umn3_mat.load(path)
    elif os.path.exists(ulog_path):
        # px4_ulog
        print 'Discovered px4 ulog (csv family of files) format.'
        flight_data = px4_ulog.load(path)
    elif ext == '.csv':
        # px4 sdlog2
        print 'Discovered px4 ulog (single csv file) format.'
        flight_data = px4_sdlog2.load(path)
    elif os.path.exists(sentera_path):
        # sentera1 or sentera2
        print 'Discovered sentera format.'
        print 'Notice: assuming original sentera camera format'
        flight_data = sentera.load(path)
        # imu_data, gps_data, air_data, filter_data = sentera2.load(path)
    else:
        print "Unable to determine data log format (or path not valid):", path

    return flight_data
