# load umn3 .h5 file data format

import csv
import h5py                     # dnf install python3-h5py
import math
import os, sys
join = os.path.join
import numpy as np
import datetime, calendar

mps2kt = 1.94384
r2d = 180.0 / math.pi
d2r = math.pi / 180.0

def load(h5_filename):
    # Name of .mat file that exists in the directory defined above and
    # has the flight_data and flight_info structures
    filepath = h5_filename
    flight_dir = os.path.dirname(filepath)
    
    # Open flight data log file:
    data = h5py.File(filepath, 'r')
        
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
    hxa = data['/Sensors/Fmu/Mpu9250/MagX_uT'][()].astype(float)
    hya = data['/Sensors/Fmu/Mpu9250/MagY_uT'][()].astype(float)
    hza = data['/Sensors/Fmu/Mpu9250/MagZ_uT'][()].astype(float)
    temp = data['/Sensors/Fmu/Mpu9250/Temperature_C'][()].astype(float)

    # temporary fault modeling for a specific project
    if '/Excitation/Fault_GyroBias_2/gyro_faultBias_rps' in data:
        gx2 = data['/Excitation/Fault_GyroBias_2/gyro_faultBias_rps'][()].astype(float)
    else:
        gx2 = None
    if '/Excitation/Fault_GyroBias_10/gyro_faultBias_rps' in data:
        gx10 = data['/Excitation/Fault_GyroBias_10/gyro_faultBias_rps'][()].astype(float)
    else:
        gx10 = None
        
    for i in range( size ):
        aircraft = 'none'
        if aircraft == 'Mjolner':
            affine = np.array(
                [[ 0.018620589,   0.0003888403, -0.0003962612, -0.229103659 ],
                 [-0.0014668783,  0.0179526977,  0.0008107074, -1.0884978428],
                 [-0.000477532,   0.0004510884,  0.016958479,   0.3941687691],
                 [ 0.,            0.,            0.,            1.          ]]
            )
            mag = np.array([hxa[i][0], hya[i][0], hza[i][0], 1.0])
            #raw = np.hstack((mag, 1.0))
            cal = np.dot(affine, mag)
            hx = cal[0]
            hy = cal[1]
            hz = cal[2]
        else:
            hx = hxa[i][0]
            hy = hya[i][0]
            hz = hza[i][0]
        imu_pt = {
            'time': timestamp[i][0],
            'p': gx[i][0],
            'q': gy[i][0],
            'r': gz[i][0],
            'ax': ax[i][0],
            'ay': ay[i][0],
            'az': az[i][0],
            'hx': hx,
            'hy': hy,
            'hz': hz,
            'temp': temp[i][0]
        }
        if not gx2 is None:
            imu_pt['p'] -= gx2[i][0]
        if not gx10 is None:
            imu_pt['p'] -= gx10[i][0]
        if not gx2 is None:
            imu_pt['p'] -= gx2[i][0]
        if not gx10 is None:
            imu_pt['p'] -= gx10[i][0]
        result['imu'].append(imu_pt)

    result['gps'] = []
    lat_rad = data['/Sensors/uBlox/Latitude_rad'][()]
    lon_rad = data['/Sensors/uBlox/Longitude_rad'][()]
    alt = data['/Sensors/uBlox/Altitude_m'][()]
    vn = data['/Sensors/uBlox/NorthVelocity_ms'][()]
    ve = data['/Sensors/uBlox/EastVelocity_ms'][()]
    vd = data['/Sensors/uBlox/DownVelocity_ms'][()]
    sats = data['/Sensors/uBlox/NumberSatellites'][()]
    tow = data['/Sensors/uBlox/TOW'][()]
    year = data['/Sensors/uBlox/Year'][()]
    month = data['/Sensors/uBlox/Month'][()]
    day = data['/Sensors/uBlox/Day'][()]
    hour = data['/Sensors/uBlox/Hour'][()]
    minute = data['/Sensors/uBlox/Minute'][()]
    second = data['/Sensors/uBlox/Second'][()]
    d = datetime.datetime(year[0][0], month[0][0], day[0][0],
                          hour[0][0], minute[0][0], second[0][0])
    unixbase = calendar.timegm(d.timetuple()) - timestamp[0][0]

    last_alt = alt[0][0]
    last_time = timestamp[0][0]
    last_tow = tow[0][0]
    vd_list = []
    vd_est = 0.0
    for i in range( size ):
        if tow[i][0] != last_tow:
            print("NOTICE: over writing gps down velocity with differentiated alt as a test for Huginn flight #02")
            dt = timestamp[i][0] - last_time
            da = alt[i][0] - last_alt
            print("sec: %.2f" % tow[i][0], "t: %.3f" % timestamp[i][0], "dt: %.3f" % dt,
                  "alt: %.2f" % alt[i][0], "da: %.2f" % da)
            if dt > 0.001:
                vd_est = -da / dt
            else:
                vd_est = 0.0
            last_alt = alt[i][0]
            last_time = timestamp[i][0]
            last_tow = tow[i][0]
        vd_list.append(vd_est)
        
    for i in range( size ):
        lat = lat_rad[i][0] * r2d
        lon = lon_rad[i][0] * r2d
        #print lon,lat,alt
        if abs(lat - last_gps_lat) > 0.0000000001 or abs(lon - last_gps_lon) > 0.0000000000001:
            last_gps_lat = lat
            last_gps_lon = lon
            gps_pt = {
                'time': timestamp[i][0],
                'unix_sec': unixbase + timestamp[i][0],
                'lat': lat,
                'lon': lon,
                'alt': alt[i][0],
                'vn': vn[i][0],
                've': ve[i][0],
                'vd': vd_list[i],
                'sats': int(sats[i][0])
            }
            result['gps'].append(gps_pt)
            
    result['air'] = []
    airspeed = data['/Sensor-Processing/vIAS_ms'][()] * mps2kt
    altitude = data['/Sensor-Processing/Altitude_m'][()]
    if '/Sensors/5Hole/Tip/Temperature_C' in data:
        temp = data['/Sensors/5Hole/Tip/Temperature_C'][()]
    for i in range( size ):
        air_pt = {
            'time': timestamp[i][0],
            'airspeed': airspeed[i][0],
            'alt_press': altitude[i][0],
            'alt_true': altitude[i][0]
        }
        if '/Sensors/5Hole/Tip/Temperature_C' in data:
            air_pt['temp'] = temp[i][0]
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
        psi = yaw[i][0]
        if psi > math.pi:
            psi -= 2*math.pi
        if psi < -math.pi:
            psi += 2*math.pi
        nav = {
            'time': timestamp[i][0],
            'lat': lat[i][0],
            'lon': lon[i][0],
            'alt': alt[i][0],
            'vn': vn[i][0],
            've': ve[i][0],
            'vd': vd[i][0],
            'phi': roll[i][0],
            'the': pitch[i][0],
            'psi': psi,
            'p_bias': gbx[i][0],
            'q_bias': gby[i][0],
            'r_bias': gbz[i][0],
            'ax_bias': abx[i][0],
            'ay_bias': aby[i][0],
            'az_bias': abz[i][0]
        }
        if abs(nav['lat']) > 0.0001 and abs(nav['lon']) > 0.0001:
            result['filter'].append(nav)

    if False:
        # load filter (post process) records if they exist (for comparison
        # purposes)
        filter_post = os.path.join(flight_dir, "filter-post.csv")
        if os.path.exists(filter_post):
            print('Also loading:', filter_post, '(because it exists)')
            result['filter_post'] = []
            with open(filter_post, 'r') as ffilter:
                reader = csv.DictReader(ffilter)
                for row in reader:
                    lat = float(row['latitude_deg'])
                    lon = float(row['longitude_deg'])
                    if abs(lat) > 0.0001 and abs(lon) > 0.0001:
                        psi_deg = float(row['heading_deg'])
                        if psi_deg > 180.0:
                            psi_deg = psi_deg - 360.0
                        if psi_deg < -180.0:
                            psi_deg = psi_deg + 360.0
                        nav = {
                            'time': float(row['timestamp']),
                            'lat': lat*d2r,
                            'lon': lon*d2r,
                            'alt': float(row['altitude_m']),
                            'vn': float(row['vn_ms']),
                            've': float(row['ve_ms']),
                            'vd': float(row['vd_ms']),
                            'phi': float(row['roll_deg'])*d2r,
                            'the': float(row['pitch_deg'])*d2r,
                            'psi': psi_deg*d2r,
                            'p_bias': float(row['p_bias']),
                            'q_bias': float(row['q_bias']),
                            'r_bias': float(row['r_bias']),
                            'ax_bias': float(row['ax_bias']),
                            'ay_bias': float(row['ay_bias']),
                            'az_bias': float(row['az_bias'])
                        }
                        result['filter_post'].append(nav)

    result['pilot'] = []
    if '/Control/cmdRoll_rads' in data:
        roll = data['/Control/cmdRoll_rads'][()]
    elif '/Control/cmdRoll_rps' in data:
        roll = data['/Control/cmdRoll_rps'][()]
    if '/Control/cmdPitch_rads' in data:
        pitch = data['/Control/cmdPitch_rads'][()]
    elif '/Control/cmdPitch_rps' in data:
        pitch = data['/Control/cmdPitch_rps'][()]
    if '/Control/cmdYaw_rads' in data:
        yaw = data['/Control/cmdYaw_rads'][()]
    elif '/Control/cmdYaw_rps' in data:
        yaw = data['/Control/cmdYaw_rps'][()]
    motor = data['/Control/cmdMotor_nd'][()]
    flaps = data['/Control/cmdFlap_nd'][()]
    auto = data['/Mission/socEngage'][()]
    for i in range( size ):
        pilot = {
            'time': timestamp[i][0],
            'aileron': roll[i][0],
            'elevator': pitch[i][0],
            'throttle': motor[i][0],
            'rudder': yaw[i][0],
            'flaps': flaps[i][0],
            'gear': 0.0,
            'aux1': 0.0,
            'auto_manual': auto[i][0]
        }
        result['pilot'].append(pilot)
        
    result['act'] = []
    for i in range( size ):
        act = {
            'time': timestamp[i][0],
            'aileron': roll[i][0],
            'elevator': pitch[i][0],
            'rudder': yaw[i][0],
            'throttle': motor[i][0],
            'flaps': flaps[i][0],
            'gear': 0.0,
            'aux1': 0.0
        }
        result['act'].append(act)
                
    result['ap'] = []
    roll = data['/Control/refPhi_rad'][()]
    pitch = data['/Control/refTheta_rad'][()]
    vel = data['/Control/refV_ms'][()]
    for i in range( size ):
        ap = {
            'time': timestamp[i][0],
            'master_switch': int(auto[i][0] > 0),
            'pilot_pass_through': int(0),
            'hdg': 0.0,
            'roll': roll[i][0] * r2d,
            'alt': 0.0,
            'pitch': pitch[i][0] * r2d,
            'speed': vel[i][0] * mps2kt,
            'ground': 0.0
        }
        result['ap'].append(ap)

    result['health'] = []
    vcc = data['/Sensors/Fmu/Voltage/Input_V']
    for i in range( size ):
        health = {
            'time': timestamp[i][0],
            'main_vcc': vcc[i][0]
            #'test_index': indxTest[i][0],
            #'excite_mode': exciteMode[i][0]
        }
        result['health'].append(health)

    result['event'] = []
    socEngage = data['/Mission/socEngage'][()]
    indxTest = data['/Mission/testID'][()]
    exciteMode = data['/Mission/testSel'][()]
    last_soc = 0
    last_id = -1
    last_excite = 0
    for i in range( size ):
        soc = socEngage[i][0]
        test_id = indxTest[i][0]
        excite = exciteMode[i][0]
        if soc != last_soc:
            event = {
                'time': timestamp[i][0]
            }
            if soc:
                event['message'] = "SOC Engaged"
            else:
                event['message'] = "SOC Disengaged"
            result['event'].append(event)
            last_soc = soc
        if test_id != last_id:
            event = {
                'time': timestamp[i][0]
            }
            event['message'] = 'Test ID = %d' % test_id
            result['event'].append(event)
            last_id = test_id
            
    dir = os.path.dirname(h5_filename)
    # print('dir:', dir)
    
    filename = os.path.join(dir, 'imu-0.txt')
    f = open(filename, 'w')
    for imupt in result['imu']:
        line = [ '%.5f' % imupt['time'], '%.4f' % imupt['p'], '%.4f' % imupt['q'], '%.4f' % imupt['r'], '%.4f' % imupt['ax'], '%.4f' % imupt['ay'], '%.4f' % imupt['az'], '%.4f' % imupt['hx'], '%.4f' % imupt['hy'], '%.4f' % imupt['hz'], '%.4f' % imupt['temp'], '0' ]
        f.write(','.join(line) + '\n')

    filename = os.path.join(dir, 'gps-0.txt')
    f = open(filename, 'w')
    for gpspt in result['gps']:
        line = [ '%.5f' % gpspt['time'], '%.10f' % gpspt['lat'], '%.10f' % gpspt['lon'], '%.4f' % gpspt['alt'], '%.4f' % gpspt['vn'], '%.4f' % gpspt['ve'], '%.4f' % gpspt['vd'], '%.4f' % gpspt['time'], '8', '0' ]
        f.write(','.join(line) + '\n')

    if 'filter' in result:
        filename = os.path.join(dir, 'filter-0.txt')
        f = open(filename, 'w')
        for filtpt in result['filter']:
            line = [ '%.5f' % filtpt['time'], '%.10f' % filtpt['lat'], '%.10f' % filtpt['lon'], '%.4f' % filtpt['alt'], '%.4f' % filtpt['vn'], '%.4f' % filtpt['ve'], '%.4f' % filtpt['vd'], '%.4f' % (filtpt['phi']*r2d), '%.4f' % (filtpt['the']*r2d), '%.4f' % (filtpt['psi']*r2d), '0' ]
            f.write(','.join(line) + '\n')

    return result
