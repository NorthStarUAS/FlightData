# load umn .mat file data format

# MAT_FILENAME = 'thor_flight75_WaypointTracker_150squareWaypointNew_2012_10_10.mat'

FLAG_UNBIASED_IMU = False             # Choose if accel/gyro should be bias-free.

import h5py
import math
import os, sys
join = os.path.join
import numpy as np

mps2kt = 1.94384
r2d = 180.0 / math.pi

# empty class we'll fill in with data members
class Record(): pass

def load(h5_filename):
    # Name of .mat file that exists in the directory defined above and
    # has the flight_data and flight_info structures
    filepath = h5_filename

    # Load Flight Data: ## IMPORTANT to have the .mat file in the
    # flight_data and flight_info structures for this function ##
    data = h5py.File(filepath)
    #for keys in data:
    #    print keys
        
    # create data structures for ekf processing
    result = {}
    result['imu'] = []
    result['gps'] = []
    result['air'] = []
    result['filter'] = []
    result['act'] = []
    
    last_gps_lon = -9999.0
    last_gps_lat = -9999.0
    
    size = len(data['Fmu']['Time_us'])

    timestamp = data['Fmu']['Time_us'][()].astype(float) * 1e-6

    gyro = data['Mpu9250']['Gyro_rads'][()].astype(float)
    accel = data['Mpu9250']['Accel_mss'][()].astype(float)
    mag = data['Mpu9250']['Mag_uT'][()].astype(float)
    temp = data['Mpu9250']['Temp_C'][()].astype(float)
    for i in range( size ):
        imu_pt = Record()
        imu_pt.time = timestamp[i][0]
        imu_pt.p = gyro[i][0]
        imu_pt.q = gyro[i][1]
        imu_pt.r = gyro[i][2]
        imu_pt.ax = accel[i][0]
        imu_pt.ay = accel[i][1]
        imu_pt.az = accel[i][2]
        imu_pt.hx = mag[i][0]
        imu_pt.hy = mag[i][1]
        imu_pt.hz = mag[i][2]
        imu_pt.temp = temp[i][0]
        result['imu'].append(imu_pt)

    lla = data['Gps_0']['LLA'][()]
    vel = data['Gps_0']['NEDVelocity_ms'][()]
    sats = data['Gps_0']['NumberSatellites'][()]
    for i in range( size ):
        lat = lla[i][0] * r2d
        lon = lla[i][1] * r2d
        #print lon,lat,alt
        if abs(lat - last_gps_lat) > 0.0000000001 or abs(lon - last_gps_lon) > 0.0000000000001:
            last_gps_lat = lat
            last_gps_lon = lon
            gps_pt = Record()
            gps_pt.time = timestamp[i][0]
            gps_pt.unix_sec = timestamp[i][0] # hack incrementing time stamp here
            gps_pt.lat = lat
            gps_pt.lon = lon
            gps_pt.alt = lla[i][2]
            gps_pt.vn = vel[i][0]
            gps_pt.ve = vel[i][1]
            gps_pt.vd = vel[i][2]
            gps_pt.sats = int(sats[i][0])
            result['gps'].append(gps_pt)
            
    airspeed = data['Airdata']['vIas_mps'][()] * mps2kt
    altitude = data['Airdata']['alt_m'][()]
    for i in range( size ):
        air_pt = Record()
        air_pt.time = timestamp[i][0]
        air_pt.airspeed = airspeed[i][0]
        air_pt.altitude = altitude[i][0]
        result['air'].append(air_pt)
        
    # nav = NAVdata()
    # nav.time = float(t[k])
    # nav.lat = float(flight_data.navlat[k])
    # nav.lon = float(flight_data.navlon[k])
    # nav.alt = float(flight_data.navalt[k])
    # nav.vn = float(flight_data.navvn[k])
    # nav.ve = float(flight_data.navve[k])
    # nav.vd = float(flight_data.navvd[k])
    # nav.phi = float(flight_data.phi[k])
    # nav.the = float(flight_data.theta[k])
    # nav.psi = float(flight_data.psi[k])
    # result['filter'].append(nav)

    inceptors = data['SbusRx_0']['Inceptors'][()]
    for i in range( size ):
        act = Record()
        act.time = timestamp[i][0]
        act.aileron = inceptors[i][0]
        act.elevator = inceptors[i][1]
        act.throttle = inceptors[i][4]
        act.rudder = inceptors[i][2]
        result['act'].append(act)
        
    dir = os.path.dirname(h5_filename)
    print 'dir:', dir
    
    filename = os.path.join(dir, 'imu-0.txt')
    f = open(filename, 'w')
    for imupt in result['imu']:
        line = [ '%.5f' % imupt.time, '%.4f' % imupt.p, '%.4f' % imupt.q, '%.4f' % imupt.r, '%.4f' % imupt.ax, '%.4f' % imupt.ay, '%.4f' % imupt.az, '%.4f' % imupt.hx, '%.4f' % imupt.hy, '%.4f' % imupt.hz, '%.4f' % imupt.temp, '0' ]
        f.write(','.join(line) + '\n')

    filename = os.path.join(dir, 'gps-0.txt')
    f = open(filename, 'w')
    for gpspt in result['gps']:
        line = [ '%.5f' % gpspt.time, '%.10f' % gpspt.lat, '%.10f' % gpspt.lon, '%.4f' % gpspt.alt, '%.4f' % gpspt.vn, '%.4f' % gpspt.ve, '%.4f' % gpspt.vd, '%.4f' % gpspt.time, '8', '0' ]
        f.write(','.join(line) + '\n')

    if 'filter' in result:
        filename = os.path.join(dir, 'filter-0.txt')
        f = open(filename, 'w')
        for filtpt in result['filter']:
            line = [ '%.5f' % filtpt.time, '%.10f' % filtpt.lat, '%.10f' % filtpt.lon, '%.4f' % filtpt.alt, '%.4f' % filtpt.vn, '%.4f' % filtpt.ve, '%.4f' % filtpt.vd, '%.4f' % (filtpt.phi*r2d), '%.4f' % (filtpt.the*r2d), '%.4f' % (filtpt.psi*r2d), '0' ]
            f.write(','.join(line) + '\n')

    return result
