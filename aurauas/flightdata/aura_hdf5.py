import csv
import h5py
import os
import math
import re

from . import imucal

d2r = math.pi / 180.0

# empty class we'll fill in with data members
# class Record: pass (deprecated)

def load(h5_filename, recalibrate=None):
    filepath = h5_filename
    flight_dir = os.path.dirname(filepath)

    # open the hdf5 file
    data = h5py.File(filepath)

    result = {}

    # load imu/gps data files
    imucal_json = os.path.join(flight_dir, "imucal.json")
    health_file = os.path.join(flight_dir, "health-0.csv")
    imu_bias_file = os.path.join(flight_dir, "imubias.csv")

    timestamp = data['/events/timestamp'][()].astype(float)
    message = data['/events/message'][()]
    result['event'] = []
    pilot_mapping = 'Aura3'       # APM2 or Aura3
    for i in range(len(timestamp)):
        event = {
            'time': timestamp[i][0],
            'message': message[i][0]
        }
        if 'Aura3' in event['message']:
            pilot_mapping = 'Aura3'
        elif 'APM2' in event['message']:
            pilot_mapping = 'APM2'
        result['event'].append(event)
        
    timestamp = data['/sensors/imu/timestamp'][()].astype(float)
    gx = data['/sensors/imu/p_rad_sec'][()].astype(float)
    gy = data['/sensors/imu/q_rad_sec'][()].astype(float)
    gz = data['/sensors/imu/r_rad_sec'][()].astype(float)
    ax = data['/sensors/imu/ax_mps_sec'][()].astype(float)
    ay = data['/sensors/imu/ay_mps_sec'][()].astype(float)
    az = data['/sensors/imu/az_mps_sec'][()].astype(float)
    hx = data['/sensors/imu/hx'][()].astype(float)
    hy = data['/sensors/imu/hy'][()].astype(float)
    hz = data['/sensors/imu/hz'][()].astype(float)
    temp = data['/sensors/imu/temp_C'][()].astype(float)
    result['imu'] = []
    for i in range(len(timestamp)):
        imu = {
            'time': timestamp[i][0],
            'p': gx[i][0],
            'q': gy[i][0],
            'r': gz[i][0],
            'ax': ax[i][0],
            'ay': ay[i][0],
            'az': az[i][0],
            'hx': hx[i][0],
            'hy': hy[i][0],
            'hz': hz[i][0],
            'temp': temp[i][0]
        }
        result['imu'].append(imu)

    timestamp = data['/sensors/gps/timestamp'][()].astype(float)
    unix_sec = data['/sensors/gps/unix_time_sec'][()]
    lat_deg = data['/sensors/gps/latitude_deg'][()]
    lon_deg = data['/sensors/gps/longitude_deg'][()]
    alt = data['/sensors/gps/altitude_m'][()].astype(float)
    vn = data['/sensors/gps/vn_ms'][()].astype(float)
    ve = data['/sensors/gps/ve_ms'][()].astype(float)
    vd = data['/sensors/gps/vd_ms'][()].astype(float)
    sats = data['/sensors/gps/satellites'][()]
    result['gps'] = []
    for i in range(len(timestamp)):
        if sats[i][0] > 5:
            gps = {
                'time': timestamp[i][0],
                'unix_sec': unix_sec[i][0],
                'lat': lat_deg[i][0],
                'lon': lon_deg[i][0],
                'alt': alt[i][0],
                'vn': vn[i][0],
                've': ve[i][0],
                'vd': vd[i][0],
                'sats': sats[i][0]
            }
            result['gps'].append(gps)

    timestamp = data['/sensors/air/timestamp'][()].astype(float)
    static_press = data['/sensors/air/pressure_mbar'][()].astype(float)
    temp = data['/sensors/air/temp_C'][()].astype(float)
    airspeed = data['/sensors/air/airspeed_smoothed_kt'][()].astype(float)
    alt_press = data['/sensors/air/altitude_smoothed_m'][()].astype(float)
    alt_true = data['/sensors/air/altitude_true_m'][()].astype(float)
    wind_dir = data['/sensors/air/wind_dir_deg'][()].astype(float)
    wind_speed = data['/sensors/air/wind_speed_kt'][()].astype(float)
    result['air'] = []
    for i in range(len(timestamp)):
        air = {
            'time': timestamp[i][0],
            'static_press': static_press[i][0],
            'diff_press': 0.0, # not directly available in aura flight log
            'temp': temp[i][0],
            'airspeed': airspeed[i][0],
            'alt_press': alt_press[i][0],
            'alt_true': alt_true[i][0],
            'wind_dir': wind_dir[i][0],
            'wind_speed': wind_speed[i][0]
        }
        result['air'].append( air )

    timestamp = data['/navigation/filter/timestamp'][()].astype(float)
    lat = data['/navigation/filter/latitude_deg'][()]*d2r
    lon = data['/navigation/filter/longitude_deg'][()]*d2r
    alt = data['/navigation/filter/altitude_m'][()].astype(float)
    vn = data['/navigation/filter/vn_ms'][()].astype(float)
    ve = data['/navigation/filter/ve_ms'][()].astype(float)
    vd = data['/navigation/filter/vd_ms'][()].astype(float)
    roll = data['/navigation/filter/roll_deg'][()].astype(float)
    pitch = data['/navigation/filter/pitch_deg'][()].astype(float)
    yaw = data['/navigation/filter/heading_deg'][()].astype(float)
    gbx = data['/navigation/filter/p_bias'][()].astype(float)
    gby = data['/navigation/filter/q_bias'][()].astype(float)
    gbz = data['/navigation/filter/r_bias'][()].astype(float)
    abx = data['/navigation/filter/ax_bias'][()].astype(float)
    aby = data['/navigation/filter/ay_bias'][()].astype(float)
    abz = data['/navigation/filter/az_bias'][()].astype(float)
    result['filter'] = []
    for i in range(len(timestamp)):
        psi = yaw[i][0]*d2r
        if psi > math.pi:
            psi -= 2*math.pi
        if psi < -math.pi:
            psi += 2*math.pi
        psix = math.cos(psi)
        psiy = math.sin(psi)
        if abs(lat[i][0]) > 0.0001 and abs(lon[i][0]) > 0.0001:
            filter = {
                'time': timestamp[i][0],
                'lat': lat[i][0],
                'lon': lon[i][0],
                'alt': alt[i][0],
                'vn': vn[i][0],
                've': ve[i][0],
                'vd': vd[i][0],
                'phi': roll[i][0]*d2r,
                'the': pitch[i][0]*d2r,
                'psi': psi,
                'psix': psix,
                'psiy': psiy,
                'p_bias': gbx[i][0],
                'q_bias': gby[i][0],
                'r_bias': gbz[i][0],
                'ax_bias': abx[i][0],
                'ay_bias': aby[i][0],
                'az_bias': abz[i][0]
            }
            result['filter'].append(filter)

    # load filter (post process) records if they exist (for comparison
    # purposes)
    # if os.path.exists(filter_post):
    #     result['filter_post'] = []
    #     with open(filter_post, 'r') as ffilter:
    #         reader = csv.DictReader(ffilter)
    #         for row in reader:
    #             lat = float(row['latitude_deg'])
    #             lon = float(row['longitude_deg'])
    #             psi_deg = float(row['heading_deg'])
    #             psi = psi_deg*d2r
    #             if psi > math.pi:
    #                 psi -= 2*math.pi
    #             if psi < -math.pi:
    #                 psi += 2*math.pi
    #             psix = math.cos(psi)
    #             psiy = math.sin(psi)
    #             if abs(lat) > 0.0001 and abs(lon) > 0.0001:
    #                 nav = {
    #                     'time': float(row['timestamp']),
    #                     'lat': lat*d2r,
    #                     'lon': lon*d2r,
    #                     'alt': float(row['altitude_m']),
    #                     'vn': float(row['vn_ms']),
    #                     've': float(row['ve_ms']),
    #                     'vd': float(row['vd_ms']),
    #                     'phi': float(row['roll_deg'])*d2r,
    #                     'the': float(row['pitch_deg'])*d2r,
    #                     'psi': psi,
    #                     'psix': psix,
    #                     'psiy': psiy,
    #                     'p_bias': float(row['p_bias']),
    #                     'q_bias': float(row['q_bias']),
    #                     'r_bias': float(row['r_bias']),
    #                     'ax_bias': float(row['ax_bias']),
    #                     'ay_bias': float(row['ay_bias']),
    #                     'az_bias': float(row['az_bias'])
    #                 }
    #                 result['filter_post'].append(nav)

    print('Pilot input mapping:', pilot_mapping)
    timestamp = data['/sensors/pilot/timestamp'][()].astype(float)
    ch0 = data['/sensors/pilot/channel[0]'][()].astype(float)
    ch1 = data['/sensors/pilot/channel[1]'][()].astype(float)
    ch2 = data['/sensors/pilot/channel[2]'][()].astype(float)
    ch3 = data['/sensors/pilot/channel[3]'][()].astype(float)
    ch4 = data['/sensors/pilot/channel[4]'][()].astype(float)
    ch5 = data['/sensors/pilot/channel[5]'][()].astype(float)
    ch6 = data['/sensors/pilot/channel[6]'][()].astype(float)
    ch7 = data['/sensors/pilot/channel[7]'][()].astype(float)
    result['pilot'] = []
    for i in range(len(timestamp)):
        if pilot_mapping == 'Aura3':
            pilot = {
                'time': timestamp[i][0],
                'auto_manual': ch0[i][0],
                'throttle_safety': ch1[i][0],
                'throttle': ch2[i][0],
                'aileron': ch3[i][0],
                'elevator': ch4[i][0],
                'rudder': ch5[i][0],
                'flaps': ch6[i][0],
                'aux1': ch7[i][0],
                'gear': 0
            }
        elif pilot_mapping == 'APM2':
            pilot = {
                'time': timestamp[i][0],
                'aileron': ch0[i][0],
                'elevator': -ch1[i][0],
                'throttle': ch2[i][0],
                'rudder': ch3[i][0],
                'gear': ch4[i][0],
                'flaps': ch5[i][0],
                'aux1': ch6[i][0],
                'auto_manual': ch7[i][0],
                'throttle_safety': 0.0
            }
        else:
            pilot = {}
        result['pilot'].append(pilot)

    timestamp = data['/actuators/act/timestamp'][()].astype(float)
    ail = data['/actuators/act/aileron_norm'][()].astype(float)
    elev = data['/actuators/act/elevator_norm'][()].astype(float)
    thr = data['/actuators/act/throttle_norm'][()].astype(float)
    rud = data['/actuators/act/rudder_norm'][()].astype(float)
    gear = data['/actuators/act/channel5_norm'][()].astype(float)
    flaps = data['/actuators/act/flaps_norm'][()].astype(float)
    aux1 = data['/actuators/act/channel7_norm'][()].astype(float)
    auto_manual = data['/actuators/act/channel8_norm'][()].astype(float)
    result['act'] = []
    for i in range(len(timestamp)):
        act = {
            'time': timestamp[i][0],
            'aileron': ail[i][0],
            'elevator': elev[i][0],
            'throttle': thr[i][0],
            'rudder': rud[i][0],
            'gear': gear[i][0],
            'flaps': flaps[i][0],
            'aux1': aux1[i][0],
            'auto_manual': auto_manual[i][0]
        }
        result['act'].append(act)


    timestamp = data['/autopilot/timestamp'][()].astype(float)
    master = data['/autopilot/master_switch'][()]
    pass_through = data['/autopilot/pilot_pass_through'][()]
    hdg = data['/autopilot/groundtrack_deg'][()].astype(float)
    roll = data['/autopilot/roll_deg'][()].astype(float)
    alt = data['/autopilot/altitude_msl_ft'][()].astype(float)
    pitch = data['/autopilot/pitch_deg'][()].astype(float)
    speed = data['/autopilot/airspeed_kt'][()].astype(float)
    ground = data['/autopilot/altitude_ground_m'][()].astype(float)
    result['ap'] = []
    for i in range(len(timestamp)):
        hdgx = math.cos(hdg[i][0]*d2r)
        hdgy = math.sin(hdg[i][0]*d2r)
        ap = {
            'time': timestamp[i][0],
            'master_switch': master[i][0],
            'pilot_pass_through': pass_through[i][0],
            'hdg': hdg[i][0],
            'hdgx': hdgx,
            'hdgy': hdgy,
            'roll': roll[i][0],
            'alt': alt[i][0],
            'pitch': pitch[i][0],
            'speed': speed[i][0],
            'ground': ground[i][0]
        }
        result['ap'].append(ap)

    if os.path.exists(health_file):
        result['health'] = []
        with open(health_file, 'r') as fhealth:
            reader = csv.DictReader(fhealth)
            for row in reader:
                health = {
                    'time': float(row['timestamp']),
                    'load_avg': float(row['system_load_avg'])
                }
                if 'avionics_vcc' in row:
                    health['avionics_vcc'] = float(row['avionics_vcc'])
                elif 'board_vcc' in row:
                    health['avionics_vcc'] = float(row['board_vcc'])
                if 'main_vcc' in row:
                    health['main_vcc'] = float(row['main_vcc'])
                elif 'extern_volts' in row:
                    health['main_vcc'] = float(row['extern_volts'])
                if 'cell_vcc' in row:
                    health['cell_vcc'] = float(row['cell_vcc'])
                elif 'extern_cell_volts' in row:
                    health['cell_vcc'] = float(row['extern_cell_volts'])
                if 'main_amps' in row:
                    health['main_amps'] = float(row['main_amps'])
                elif 'extern_amps' in row:
                    health['main_amps'] = float(row['extern_amps'])
                if 'total_mah' in row:
                    health['main_mah'] = float(row['total_mah'])
                elif 'extern_current_mah' in row:
                    health['main_mah'] = float(row['extern_current_mah'])
                result['health'].append(health)

    cal = imucal.Calibration()
    if os.path.exists(imucal_json):
        cal.load(imucal_json)
        print('back correcting imu data (to get original raw values)')
        cal.back_correct(result['imu'], result['filter'])

    if recalibrate:
        print('recalibrating imu data using alternate calibration file:', recalibrate)
        rcal = imucal.Calibration()
        rcal.load(recalibrate)
        result['imu'] = rcal.correct(result['imu'])

    return result

def save_filter_result(filename, nav):
    keys = ['timestamp', 'latitude_deg', 'longitude_deg', 'altitude_m',
            'vn_ms', 've_ms', 'vd_ms', 'roll_deg', 'pitch_deg', 'heading_deg',
            'p_bias', 'q_bias', 'r_bias', 'ax_bias', 'ay_bias', 'az_bias',
            'status']
    with open(filename, 'w') as csvfile:
        writer = csv.DictWriter( csvfile, fieldnames=keys )
        writer.writeheader()
        for navpt in nav:
            row = dict()
            row['timestamp'] = '%.4f' % navpt['time']
            row['latitude_deg'] = '%.10f' % (navpt['lat']*180.0/math.pi)
            row['longitude_deg'] = '%.10f' % (navpt['lon']*180.0/math.pi)
            row['altitude_m'] = '%.2f' % navpt['alt']
            row['vn_ms'] = '%.4f' % navpt['vn']
            row['ve_ms'] = '%.4f' % navpt['ve']
            row['vd_ms'] = '%.4f' % navpt['vd']
            row['roll_deg'] = '%.2f' % (navpt['phi']*180.0/math.pi)
            row['pitch_deg'] = '%.2f' % (navpt['the']*180.0/math.pi)
            row['heading_deg'] = '%.2f' % (navpt['psi']*180.0/math.pi)
            row['p_bias'] = '%.4f' % navpt['gbx']
            row['q_bias'] = '%.4f' % navpt['gby']
            row['r_bias'] = '%.4f' % navpt['gbz']
            row['ax_bias'] = '%.3f' % navpt['abx']
            row['ay_bias'] = '%.3f' % navpt['aby']
            row['az_bias'] = '%.3f' % navpt['abz']
            row['status'] = '%d' % 0
            writer.writerow(row)
