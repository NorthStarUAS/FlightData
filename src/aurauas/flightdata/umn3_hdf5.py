# load umn3 .h5 file data format

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
    
    last_gps_lon = -9999.0
    last_gps_lat = -9999.0
    
    size = len(data['Fmu']['Time_us'])

    timestamp = data['Fmu']['Time_us'][()].astype(float) * 1e-6

    result['imu'] = []
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
        aircraft = 'Mjolner'
        if aircraft == 'Mjolner':
            affine = np.array(
                [[ 0.018620589,   0.0003888403, -0.0003962612, -0.229103659 ],
                 [-0.0014668783,  0.0179526977,  0.0008107074, -1.0884978428],
                 [-0.000477532,   0.0004510884,  0.016958479,   0.3941687691],
                 [ 0.,            0.,            0.,            1.          ]]
)
            raw = np.hstack((mag[i], 1.0))
            cal = np.dot(affine, raw)
            imu_pt.hx = cal[0]
            imu_pt.hy = cal[1]
            imu_pt.hz = cal[2]
        else:
            imu_pt.hx = mag[i][0]
            imu_pt.hy = mag[i][1]
            imu_pt.hz = mag[i][2]
        imu_pt.temp = temp[i][0]
        result['imu'].append(imu_pt)

    result['gps'] = []
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
            
    result['air'] = []
    airspeed = data['Airdata']['vIas_mps'][()] * mps2kt
    altitude = data['Airdata']['alt_m'][()]
    for i in range( size ):
        air_pt = Record()
        air_pt.time = timestamp[i][0]
        air_pt.airspeed = airspeed[i][0]
        air_pt.altitude = altitude[i][0]
        air_pt.alt_true = altitude[i][0]
        result['air'].append(air_pt)
        
    result['filter'] = []
    lla = data['NavFilter']['LLA'][()]
    vel = data['NavFilter']['NEDVelocity_ms'][()]
    euler = data['NavFilter']['Euler_rad'][()]
    gb = data['NavFilter']['GyroBias_rads'][()]
    ab = data['NavFilter']['AccelBias_mss'][()]
    for i in range( size ):
        nav = Record()
        nav.time = timestamp[i][0]
        nav.lat = lla[i][0]
        nav.lon = lla[i][1]
        nav.alt = lla[i][2]
        nav.vn = vel[i][0]
        nav.ve = vel[i][1]
        nav.vd = vel[i][2]
        nav.phi = euler[i][0]
        nav.the = euler[i][1]
        nav.psi = euler[i][2]
        nav.p_bias = gb[i][0]
        nav.q_bias = gb[i][1]
        nav.r_bias = gb[i][2]
        nav.ax_bias = ab[i][0]
        nav.ay_bias = ab[i][1]
        nav.az_bias = ab[i][2]
        if abs(nav.lat) > 0.0001 and abs(nav.lon) > 0.0001:
            result['filter'].append(nav)

    result['pilot'] = []
    inceptors = data['SbusRx_0']['Inceptors'][()]
    auto = data['SbusRx_0']['AutoEnabled'][()]
    aux = data['SbusRx_0']['AuxInputs'][()]
    for i in range( size ):
        pilot = Record()
        pilot.time = timestamp[i][0]
        pilot.aileron = inceptors[i][0]
        pilot.elevator = inceptors[i][1]
        pilot.throttle = inceptors[i][4]
        pilot.rudder = inceptors[i][2]
        pilot.flaps = inceptors[i][3]
        pilot.gear = 0.0
        pilot.aux1 = 0.0
        pilot.auto_manual = aux[i][0]
        result['pilot'].append(pilot)
        
    result['act'] = []
    cmds = data['Cntrl']['cmdCntrl'][()]
    for i in range( size ):
        act = Record()
        act.time = timestamp[i][0]
        act.aileron = cmds[i][0]
        act.elevator = cmds[i][1]
        act.rudder = cmds[i][2]
        act.throttle = cmds[i][3]
        if act.throttle > 1.1:
            act.throttle = 0
        act.flaps = 0.0
        act.gear = 0.0
        act.aux1 = 0.0
        result['act'].append(act)
                
    result['ap'] = []
    for i in range( size ):
        ap = Record()
        ap.time = timestamp[i][0]
        ap.master_switch = int(aux[i][0] > 0)
        ap.pilot_pass_through = int(0)
        ap.hdg = 0.0
        ap.roll = inceptors[i][0] * 60.0
        ap.alt = 0.0
        ap.pitch = inceptors[i][1] * 60.0
        ap.speed = 23.0 * mps2kt
        ap.ground = 0.0
        result['ap'].append(ap)

    result['health'] = []
    vcc = data['Fmu']['InputVoltage_V']
    indxTest = data['Excite']['indxTest'][()]
    exciteMode = data['Excite']['exciteMode'][()]
    for i in range( size ):
        health = Record()
        health.time = timestamp[i][0]
        health.main_vcc = vcc[i][0]
        health.test_index = indxTest[i][0]
        health.excite_mode = exciteMode[i][0]
        result['health'].append(health)
        
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
