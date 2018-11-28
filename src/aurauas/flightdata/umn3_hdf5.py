# load umn3 .h5 file data format

import h5py                     # dnf install python3-h5py
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
    
    last_gps_lon = -9999.0
    last_gps_lat = -9999.0
    
    size = len(data['/Sensors/Fmu/Time_us'])

    timestamp = data['/Sensors/Fmu/Time_us'][()].astype(float) * 1e-6

    result['imu'] = []
    gx = data['/Sensors/Fmu/Mpu9250/GyroX_rads'][()].astype(float)
    gy = data['/Sensors/Fmu/Mpu9250/GyroY_rads'][()].astype(float)
    gz = data['/Sensors/Fmu/Mpu9250/GyroZ_rads'][()].astype(float)
    ax = data['/Sensors/Fmu/Mpu9250/AccelX_mss'][()].astype(float)
    ay = data['/Sensors/Fmu/Mpu9250/AccelY_mss'][()].astype(float)
    az = data['/Sensors/Fmu/Mpu9250/AccelZ_mss'][()].astype(float)
    hx = data['/Sensors/Fmu/Mpu9250/MagX_uT'][()].astype(float)
    hy = data['/Sensors/Fmu/Mpu9250/MagY_uT'][()].astype(float)
    hz = data['/Sensors/Fmu/Mpu9250/MagZ_uT'][()].astype(float)
    temp = data['/Sensors/Fmu/Mpu9250/Temperature_C'][()].astype(float)
    for i in range( size ):
        imu_pt = Record()
        imu_pt.time = timestamp[i][0]
        imu_pt.p = gx[i][0]
        imu_pt.q = gy[i][0]
        imu_pt.r = gz[i][0]
        imu_pt.ax = ax[i][0]
        imu_pt.ay = ay[i][0]
        imu_pt.az = az[i][0]
        aircraft = 'Mjolner'
        if aircraft == 'Mjolner':
            affine = np.array(
                [[ 0.018620589,   0.0003888403, -0.0003962612, -0.229103659 ],
                 [-0.0014668783,  0.0179526977,  0.0008107074, -1.0884978428],
                 [-0.000477532,   0.0004510884,  0.016958479,   0.3941687691],
                 [ 0.,            0.,            0.,            1.          ]]
)
            mag = np.array([hx[i][0], hy[i][0], hz[i][0], 1.0])
            #raw = np.hstack((mag, 1.0))
            cal = np.dot(affine, mag)
            imu_pt.hx = cal[0]
            imu_pt.hy = cal[1]
            imu_pt.hz = cal[2]
        else:
            imu_pt.hx = hx[i][0]
            imu_pt.hy = hy[i][0]
            imu_pt.hz = hz[i][0]
        imu_pt.temp = temp[i][0]
        result['imu'].append(imu_pt)

    result['gps'] = []
    lat_rad = data['/Sensors/uBlox/Latitude_rad'][()]
    lon_rad = data['/Sensors/uBlox/Longitude_rad'][()]
    alt = data['/Sensors/uBlox/Altitude_m'][()]
    vn = data['/Sensors/uBlox/NorthVelocity_ms'][()]
    ve = data['/Sensors/uBlox/EastVelocity_ms'][()]
    vd = data['/Sensors/uBlox/DownVelocity_ms'][()]
    sats = data['/Sensors/uBlox/NumberSatellites'][()]
    for i in range( size ):
        lat = lat_rad[i][0] * r2d
        lon = lon_rad[i][0] * r2d
        #print lon,lat,alt
        if abs(lat - last_gps_lat) > 0.0000000001 or abs(lon - last_gps_lon) > 0.0000000000001:
            last_gps_lat = lat
            last_gps_lon = lon
            gps_pt = Record()
            gps_pt.time = timestamp[i][0]
            gps_pt.unix_sec = timestamp[i][0] # hack incrementing time stamp here
            gps_pt.lat = lat
            gps_pt.lon = lon
            gps_pt.alt = alt[i][0]
            gps_pt.vn = vn[i][0]
            gps_pt.ve = ve[i][0]
            gps_pt.vd = vd[i][0]
            gps_pt.sats = int(sats[i][0])
            result['gps'].append(gps_pt)
            
    result['air'] = []
    airspeed = data['/Sensor-Processing/vIAS_ms'][()] * mps2kt
    altitude = data['/Sensor-Processing/Altitude_m'][()]
    for i in range( size ):
        air_pt = Record()
        air_pt.time = timestamp[i][0]
        air_pt.airspeed = airspeed[i][0]
        air_pt.altitude = altitude[i][0]
        air_pt.alt_true = altitude[i][0]
        result['air'].append(air_pt)
        
    result['filter'] = []
    lat = data['/Sensor-Processing/Baseline/INS/Latitude_rad'][()]
    lon = data['/Sensor-Processing/Baseline/INS/Longitude_rad'][()]
    alt = data['/Sensor-Processing/Baseline/INS/Altitude_m'][()]
    vn = data['/Sensor-Processing/Baseline/INS/NorthVelocity_ms'][()]
    ve = data['/Sensor-Processing/Baseline/INS/EastVelocity_ms'][()]
    vd = data['/Sensor-Processing/Baseline/INS/DownVelocity_ms'][()]
    roll = data['/Sensor-Processing/Baseline/INS/Roll_rad'][()]
    pitch = data['/Sensor-Processing/Baseline/INS/Pitch_rad'][()]
    yaw = data['/Sensor-Processing/Baseline/INS/Heading_rad'][()]
    gbx = data['/Sensor-Processing/Baseline/INS/GyroXBias_rads'][()]
    gby = data['/Sensor-Processing/Baseline/INS/GyroYBias_rads'][()]
    gbz = data['/Sensor-Processing/Baseline/INS/GyroZBias_rads'][()]
    abx = data['/Sensor-Processing/Baseline/INS/AccelXBias_mss'][()]
    aby = data['/Sensor-Processing/Baseline/INS/AccelYBias_mss'][()]
    abz = data['/Sensor-Processing/Baseline/INS/AccelZBias_mss'][()]
    for i in range( size ):
        nav = Record()
        nav.time = timestamp[i][0]
        nav.lat = lat[i][0]
        nav.lon = lon[i][0]
        nav.alt = alt[i][0]
        nav.vn = vn[i][0]
        nav.ve = ve[i][0]
        nav.vd = vd[i][0]
        nav.phi = roll[i][0]
        nav.the = pitch[i][0]
        nav.psi = yaw[i][0]
        nav.p_bias = gbx[i][0]
        nav.q_bias = gby[i][0]
        nav.r_bias = gbz[i][0]
        nav.ax_bias = abx[i][0]
        nav.ay_bias = aby[i][0]
        nav.az_bias = abz[i][0]
        if abs(nav.lat) > 0.0001 and abs(nav.lon) > 0.0001:
            result['filter'].append(nav)

    result['pilot'] = []
    roll = data['/Control/cmdRoll_rads'][()]
    pitch = data['/Control/cmdPitch_rads'][()]
    yaw = data['/Control/cmdYaw_rads'][()]
    motor = data['/Control/cmdMotor_nd'][()]
    flaps = data['/Control/cmdFlap_nd'][()]
    auto = data['/Mission/socEngage'][()]
    for i in range( size ):
        pilot = Record()
        pilot.time = timestamp[i][0]
        pilot.aileron = roll[i][0]
        pilot.elevator = pitch[i][0]
        pilot.throttle = motor[i][0]
        pilot.rudder = yaw[i][0]
        pilot.flaps = flaps[i][0]
        pilot.gear = 0.0
        pilot.aux1 = 0.0
        pilot.auto_manual = auto[i][0]
        result['pilot'].append(pilot)
        
    result['act'] = []
    for i in range( size ):
        act = Record()
        act.time = timestamp[i][0]
        act.aileron = roll[i][0]
        act.elevator = pitch[i][0]
        act.rudder = yaw[i][0]
        act.throttle = motor[i][0]
        act.flaps = flaps[i][0]
        act.gear = 0.0
        act.aux1 = 0.0
        result['act'].append(act)
                
    result['ap'] = []
    roll = data['/Control/refPhi_rad'][()]
    pitch = data['/Control/refTheta_rad'][()]
    vel = data['/Control/refV_ms'][()]
    for i in range( size ):
        ap = Record()
        ap.time = timestamp[i][0]
        ap.master_switch = int(auto[i][0] > 0)
        ap.pilot_pass_through = int(0)
        ap.hdg = 0.0
        ap.roll = roll[i][0] * r2d
        ap.alt = 0.0
        ap.pitch = pitch[i][0] * r2d
        ap.speed = vel[i][0] * mps2kt
        ap.ground = 0.0
        result['ap'].append(ap)

    result['health'] = []
    vcc = data['/Sensors/Fmu/Voltage/Input_V']
    indxTest = data['/Mission/testID'][()]
    exciteMode = data['/Mission/testSel'][()]
    for i in range( size ):
        health = Record()
        health.time = timestamp[i][0]
        health.main_vcc = vcc[i][0]
        health.test_index = indxTest[i][0]
        health.excite_mode = exciteMode[i][0]
        result['health'].append(health)
        
    dir = os.path.dirname(h5_filename)
    print('dir:', dir)
    
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
