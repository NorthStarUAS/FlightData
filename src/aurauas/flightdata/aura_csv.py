# load aura csv data format

import csv
import numpy as np
import os
import math
import re

from . import imucal

d2r = math.pi / 180.0

# empty class we'll fill in with data members
class Record: pass

def load(flight_dir, recalibrate=None):
    result = {}

    # load imu/gps data files
    event_file = os.path.join(flight_dir, "event-0.csv")
    imu_file = os.path.join(flight_dir, "imu-0.csv")
    imucal_json = os.path.join(flight_dir, "imucal.json")
    gps_file = os.path.join(flight_dir, "gps-0.csv")
    air_file = os.path.join(flight_dir, "air-0.csv")
    filter_file = os.path.join(flight_dir, "filter-0.csv")
    filter_post = os.path.join(flight_dir, "filter-post.csv")
    pilot_file = os.path.join(flight_dir, "pilot-0.csv")
    act_file = os.path.join(flight_dir, "act-0.csv")
    ap_file = os.path.join(flight_dir, "ap-0.csv")
    health_file = os.path.join(flight_dir, "health-0.csv")
    imu_bias_file = os.path.join(flight_dir, "imubias.csv")

    # HEY: in the latest aura code, calibrated magnetometer is logged,
    # not raw magnetometer, so we don't need to correct here.  We
    # could 'back correct' if we wanted original values for some
    # reason (using the calibration matrix saved with each flight
    # log.)
    
    # # vireo_01
    # mag_affine = np.array(
    #     [[ 1.6207467043,  0.0228992488,  0.0398638786,  0.1274248748],
    #      [-0.0169905025,  1.7164397411, -0.0001290047, -0.1140304977],
    #      [ 0.0424979948, -0.0038515935,  1.7193766423, -0.1449816095],
    #      [ 0.          ,  0.          ,  0.          ,  1.          ]]
    # )

    # telemaster apm2_101
    mag_affine = np.array(
        [[ 0.0026424919,  0.0001334248,  0.0000984977, -0.2235908546],
         [-0.000081925 ,  0.0026419229,  0.0000751835, -0.0010757621],
         [ 0.0000219407,  0.0000560341,  0.002541171 ,  0.040221458 ],
         [ 0.          ,  0.          ,  0.          ,  1.          ]]
    )
    
    # skywalker apm2_105
    # mag_affine = np.array(
    #      [[ 0.0025834778, 0.0001434776, 0.0001434961, -0.7900775707 ],
    #       [-0.0001903118, 0.0024796553, 0.0001365238,  0.1881142449 ],
    #       [ 0.0000556437, 0.0001329724, 0.0023791184,  0.1824851582, ],
    #       [ 0.0000000000, 0.0000000000, 0.0000000000,  1.0000000000  ]]
    # )

    #np.set_printoptions(precision=10,suppress=True)
    #print mag_affine

    pilot_mapping = 'Aura3'       # APM2 or Aura3
    result['event'] = []
    with open(event_file, 'r') as fevent:
        reader = csv.DictReader(fevent)
        for row in reader:
            event = Record()
            event.time = float(row['timestamp'])
            event.message = row['message']
            if 'Aura3' in event.message:
                pilot_mapping = 'Aura3'
            if 'APM2' in event.message:
                pilot_mapping = 'APM2'
            result['event'].append( event )

    result['imu'] = []
    with open(imu_file, 'r') as fimu:
        reader = csv.DictReader(fimu)
        for row in reader:
            imu = Record()
            imu.time = float(row['timestamp'])
            imu.p = float(row['p_rad_sec'])
            imu.q = float(row['q_rad_sec'])
            imu.r = float(row['r_rad_sec'])
            imu.ax = float(row['ax_mps_sec'])
            imu.ay = float(row['ay_mps_sec'])
            imu.az = float(row['az_mps_sec'])
            imu.hx = float(row['hx'])
            imu.hy = float(row['hy'])
            imu.hz = float(row['hz'])
            imu.temp = float(row['temp_C'])
            result['imu'].append( imu )

    result['gps'] = []
    last_time = -1.0
    with open(gps_file, 'r') as fgps:
        reader = csv.DictReader(fgps)
        for row in reader:
            # Note: aurauas logs unix time of the gps record, not tow,
            # but for the purposes of the insgns algorithm, it's only
            # important to have a properly incrementing clock, it doesn't
            # really matter what the zero reference point of time is here.
            time = float(row['timestamp'])
            sats = int(row['satellites'])
            if sats >= 5 and time > last_time:
                gps = Record()
                gps.time = time
                gps.unix_sec = float(row['unix_time_sec'])
                gps.lat = float(row['latitude_deg'])
                gps.lon = float(row['longitude_deg'])
                gps.alt = float(row['altitude_m'])
                gps.vn = float(row['vn_ms'])
                gps.ve = float(row['ve_ms'])
                gps.vd = float(row['vd_ms'])
                gps.sats = sats
                result['gps'].append(gps)
            last_time = time

    result['air'] = []
    with open(air_file, 'r') as fair:
        reader = csv.DictReader(fair)
        for row in reader:
            air = Record()
            air.time = float(row['timestamp'])
            air.static_press = float(row['pressure_mbar'])
            air.diff_press = 0.0    # not directly available in aura flight log
            air.temp = float(row['temp_C'])
            air.airspeed = float(row['airspeed_smoothed_kt'])
            air.alt_press = float(row['altitude_smoothed_m'])
            air.alt_true = float(row['altitude_true_m'])
            air.wind_dir = float(row['wind_dir_deg'])
            air.wind_speed = float(row['wind_speed_kt'])
            result['air'].append( air )

    # load filter records if they exist (for comparison purposes)
    result['filter'] = []
    with open(filter_file, 'r') as ffilter:
        reader = csv.DictReader(ffilter)
        for row in reader:
            lat = float(row['latitude_deg'])
            lon = float(row['longitude_deg'])
            if abs(lat) > 0.0001 and abs(lon) > 0.0001:
                nav = Record()
                nav.time = float(row['timestamp'])
                nav.lat = lat*d2r
                nav.lon = lon*d2r
                nav.alt = float(row['altitude_m'])
                nav.vn = float(row['vn_ms'])
                nav.ve = float(row['ve_ms'])
                nav.vd = float(row['vd_ms'])
                nav.phi = float(row['roll_deg'])*d2r
                nav.the = float(row['pitch_deg'])*d2r
                psi = float(row['heading_deg'])
                if psi > 180.0:
                    psi = psi - 360.0
                if psi < -180.0:
                    psi = psi + 360.0
                nav.psi = psi*d2r
                nav.p_bias = float(row['p_bias'])
                nav.q_bias = float(row['q_bias'])
                nav.r_bias = float(row['r_bias'])
                nav.ax_bias = float(row['ax_bias'])
                nav.ay_bias = float(row['ay_bias'])
                nav.az_bias = float(row['az_bias'])
                result['filter'].append(nav)

    # load filter (post process) records if they exist (for comparison
    # purposes)
    if os.path.exists(filter_post):
        result['filter_post'] = []
        with open(filter_post, 'r') as ffilter:
            reader = csv.DictReader(ffilter)
            for row in reader:
                lat = float(row['latitude_deg'])
                lon = float(row['longitude_deg'])
                if abs(lat) > 0.0001 and abs(lon) > 0.0001:
                    nav = Record()
                    nav.time = float(row['timestamp'])
                    nav.lat = lat*d2r
                    nav.lon = lon*d2r
                    nav.alt = float(row['altitude_m'])
                    nav.vn = float(row['vn_ms'])
                    nav.ve = float(row['ve_ms'])
                    nav.vd = float(row['vd_ms'])
                    nav.phi = float(row['roll_deg'])*d2r
                    nav.the = float(row['pitch_deg'])*d2r
                    psi = float(row['heading_deg'])
                    if psi > 180.0:
                        psi = psi - 360.0
                    if psi < -180.0:
                        psi = psi + 360.0
                    nav.psi = psi*d2r
                    nav.p_bias = float(row['p_bias'])
                    nav.q_bias = float(row['q_bias'])
                    nav.r_bias = float(row['r_bias'])
                    nav.ax_bias = float(row['ax_bias'])
                    nav.ay_bias = float(row['ay_bias'])
                    nav.az_bias = float(row['az_bias'])
                    result['filter_post'].append(nav)

    if os.path.exists(pilot_file):
        print('Pilot input mapping:', pilot_mapping)
        result['pilot'] = []
        with open(pilot_file, 'r') as fpilot:
            reader = csv.DictReader(fpilot)
            for row in reader:
                pilot = Record()
                pilot.time = float(row['timestamp'])
                if pilot_mapping == 'Aura3':
                    pilot.auto_manual = float(row['channel[0]'])
                    pilot.throttle_safety = float(row['channel[1]'])
                    pilot.throttle = float(row['channel[2]'])
                    pilot.aileron = float(row['channel[3]'])
                    pilot.elevator = float(row['channel[4]'])
                    pilot.rudder = float(row['channel[5]'])
                    pilot.flaps = float(row['channel[6]'])
                    pilot.aux1 = float(row['channel[7]'])
                    pilot.gear = 0
                elif pilot_mapping == 'APM2':
                    pilot.aileron = float(row['channel[0]'])
                    pilot.elevator = -float(row['channel[1]'])
                    pilot.throttle = float(row['channel[2]'])
                    pilot.rudder = float(row['channel[3]'])
                    pilot.gear = float(row['channel[4]'])
                    pilot.flaps = float(row['channel[5]'])
                    pilot.aux1 = float(row['channel[6]'])
                    pilot.auto_manual = float(row['channel[7]'])
                    pilot.throttle_safety = 0.0
                result['pilot'].append(pilot)

    if os.path.exists(act_file):
        result['act'] = []
        with open(act_file, 'r') as fact:
            reader = csv.DictReader(fact)
            for row in reader:
                act = Record()
                act.time = float(row['timestamp'])
                act.aileron = float(row['aileron_norm'])
                act.elevator = float(row['elevator_norm'])
                act.throttle = float(row['throttle_norm'])
                act.rudder = float(row['rudder_norm'])
                act.gear = float(row['channel5_norm'])
                act.flaps = float(row['flaps_norm'])
                act.aux1 = float(row['channel7_norm'])
                act.auto_manual = float(row['channel8_norm'])
                result['act'].append(act)

    if os.path.exists(ap_file):
        result['ap'] = []
        with open(ap_file, 'r') as fap:
            reader = csv.DictReader(fap)
            for row in reader:
                ap = Record()
                ap.time = float(row['timestamp'])
                ap.master_switch = int(row['master_switch'])
                ap.pilot_pass_through = int(row['pilot_pass_through'])
                ap.hdg = float(row['groundtrack_deg'])
                ap.roll = float(row['roll_deg'])
                ap.alt = float(row['altitude_msl_ft'])
                ap.pitch = float(row['pitch_deg'])
                ap.speed = float(row['airspeed_kt'])
                ap.ground = float(row['altitude_ground_m'])
                result['ap'].append(ap)

    if os.path.exists(health_file):
        result['health'] = []
        with open(health_file, 'r') as fhealth:
            reader = csv.DictReader(fhealth)
            for row in reader:
                health = Record()
                health.time = float(row['timestamp'])
                health.load_avg = float(row['system_load_avg'])
                health.avionics_vcc = float(row['avionics_vcc'])
                health.main_vcc = float(row['main_vcc'])
                health.cell_vcc = float(row['cell_vcc'])
                health.main_amps = float(row['main_amps'])
                health.main_mah = float(row['total_mah'])
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

def save_filter_result(filename, data_store):
    keys = ['timestamp', 'latitude_deg', 'longitude_deg', 'altitude_m',
            'vn_ms', 've_ms', 'vd_ms', 'roll_deg', 'pitch_deg', 'heading_deg',
            'p_bias', 'q_bias', 'r_bias', 'ax_bias', 'ay_bias', 'az_bias',
            'status']
    with open(filename, 'w') as csvfile:
        writer = csv.DictWriter( csvfile, fieldnames=keys )
        writer.writeheader()
        size = len(data_store.time)
        for i in range(size):
            row = dict()
            row['timestamp'] = '%.4f' % data_store.time[i]
            row['latitude_deg'] = '%.10f' % (data_store.lat[i]*180.0/math.pi)
            row['longitude_deg'] = '%.10f' % (data_store.lon[i]*180.0/math.pi)
            row['altitude_m'] = '%.2f' % data_store.alt[i]
            row['vn_ms'] = '%.4f' % data_store.vn[i]
            row['ve_ms'] = '%.4f' % data_store.ve[i]
            row['vd_ms'] = '%.4f' % data_store.vd[i]
            row['roll_deg'] = '%.2f' % (data_store.phi[i]*180.0/math.pi)
            row['pitch_deg'] = '%.2f' % (data_store.the[i]*180.0/math.pi)
            row['heading_deg'] = '%.2f' % (data_store.psi[i]*180.0/math.pi)
            row['p_bias'] = '%.4f' % data_store.p_bias[i]
            row['q_bias'] = '%.4f' % data_store.q_bias[i]
            row['r_bias'] = '%.4f' % data_store.r_bias[i]
            row['ax_bias'] = '%.3f' % data_store.ax_bias[i]
            row['ay_bias'] = '%.3f' % data_store.ay_bias[i]
            row['az_bias'] = '%.3f' % data_store.az_bias[i]
            row['status'] = '%d' % 0
            writer.writerow(row)
