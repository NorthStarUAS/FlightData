# build linear interpolaters for the 'standard' flight data fields.

import math
import numpy as np
from scipy import interpolate # strait up linear interpolation, nothing fancy

# helpful constants
d2r = math.pi / 180.0

class FlightInterpolate():
    def __init__(self):
        # interpolators
        self.imu_time = None
        self.imu_p = None
        self.imu_q = None
        self.imu_r = None
        self.imu_ax = None
        self.imu_ay = None
        self.imu_az = None
        self.imu_hx = None
        self.imu_hy = None
        self.imu_hz = None
        self.imu_temp = None

        self.gps_lat = None
        self.gps_lon = None
        self.gps_alt = None
        self.gps_unixtime = None

        self.filter_lat = None
        self.filter_lon = None
        self.filter_alt = None
        self.filter_vn = None
        self.filter_ve = None
        self.filter_vd = None
        self.filter_phi = None
        self.filter_the = None
        self.filter_psix = None
        self.filter_psiy = None

        self.air_speed = None
        self.air_true_alt = None
        self.air_alpha = None
        self.air_beta = None
        self.air_wind_dir = None
        self.air_wind_speed = None

        self.pilot_ail = None
        self.pilot_ele = None
        self.pilot_thr = None
        self.pilot_rud = None
        self.pilot_auto = None

        self.act_ail = None
        self.act_ele = None
        self.act_thr = None
        self.act_rud = None

        self.ap_hdgx = None
        self.ap_hdgy = None
        self.ap_roll = None
        self.ap_alt = None
        self.ap_pitch = None
        self.ap_speed = None

        self.power_main = None
        self.excite_mode = None
        self.test_index = None

    # build the interpolators
    def build(self, flight_data):
        if 'imu' in flight_data:
            table = []
            for imu in flight_data['imu']:
                table.append([imu.time,
                              imu.p, imu.q, imu.r,
                              imu.ax, imu.ay, imu.az,
                              imu.hx, imu.hy, imu.hz,
                              imu.temp])
            array = np.array(table)
            x = array[:,0]
            self.imu_time = x
            self.imu_p = interpolate.interp1d(x, array[:,1], bounds_error=False,
                                         fill_value=0.0)
            self.imu_q = interpolate.interp1d(x, array[:,2], bounds_error=False,
                                         fill_value=0.0)
            self.imu_r = interpolate.interp1d(x, array[:,3], bounds_error=False,
                                         fill_value=0.0)
            self.imu_ax = interpolate.interp1d(x, array[:,4],
                                               bounds_error=False,
                                               fill_value=0.0)
            self.imu_ay = interpolate.interp1d(x, array[:,5],
                                               bounds_error=False,
                                               fill_value=0.0)
            self.imu_az = interpolate.interp1d(x, array[:,6],
                                               bounds_error=False,
                                               fill_value=0.0)
            self.imu_hx = interpolate.interp1d(x, array[:,7],
                                               bounds_error=False,
                                               fill_value=0.0)
            self.imu_hy = interpolate.interp1d(x, array[:,8],
                                               bounds_error=False,
                                               fill_value=0.0)
            self.imu_hz = interpolate.interp1d(x, array[:,9],
                                               bounds_error=False,
                                               fill_value=0.0)
            self.imu_temp = interpolate.interp1d(x, array[:,10],
                                               bounds_error=False,
                                               fill_value=0.0)
        if 'gps' in flight_data and len(flight_data['gps']):
            table = []
            for gps in flight_data['gps']:
                table.append([gps.time,
                              gps.lat, gps.lon, gps.alt,
                              gps.vn, gps.ve, gps.vd,
                              gps.unix_sec, gps.sats])
            array = np.array(table)
            x = array[:,0]
            self.gps_lat = interpolate.interp1d(x, array[:,1],
                                                bounds_error=False,
                                                fill_value=0.0)
            self.gps_lon = interpolate.interp1d(x, array[:,2],
                                                bounds_error=False,
                                                fill_value=0.0)
            self.gps_alt = interpolate.interp1d(x, array[:,3],
                                                bounds_error=False,
                                           fill_value=0.0)
            self.gps_unixtime = interpolate.interp1d(x, array[:,7],
                                                     bounds_error=False,
                                                     fill_value=0.0)
        if 'filter_post' in flight_data:
            filter_src = flight_data['filter_post']
            print('Interpolator is using post-process filter data')
        elif 'filter' in flight_data:
            filter_src = flight_data['filter']
            print('Interpolator using on-board filter data')
        else:
            filter_src = None
        if filter_src:
            table = []
            for filter in filter_src:
                psix = math.cos(filter.psi)
                psiy = math.sin(filter.psi)
                table.append([filter.time,
                              filter.lat, filter.lon, filter.alt,
                              filter.vn, filter.ve, filter.vd,
                              filter.phi, filter.the, psix, psiy])
            array = np.array(table)
            x = array[:,0]
            self.filter_lat = interpolate.interp1d(x, array[:,1],
                                                   bounds_error=False,
                                                   fill_value=0.0)
            self.filter_lon = interpolate.interp1d(x, array[:,2],
                                                   bounds_error=False,
                                                   fill_value=0.0)
            self.filter_alt = interpolate.interp1d(x, array[:,3],
                                                   bounds_error=False,
                                                   fill_value=0.0)
            self.filter_vn = interpolate.interp1d(x, array[:,4],
                                                  bounds_error=False,
                                                  fill_value=0.0)
            self.filter_ve = interpolate.interp1d(x, array[:,5],
                                                  bounds_error=False,
                                                  fill_value=0.0)
            self.filter_vd = interpolate.interp1d(x, array[:,6],
                                                  bounds_error=False,
                                                  fill_value=0.0)
            self.filter_phi = interpolate.interp1d(x, array[:,7],
                                                   bounds_error=False,
                                                   fill_value=0.0)
            self.filter_the = interpolate.interp1d(x, array[:,8],
                                                   bounds_error=False,
                                                   fill_value=0.0)
            self.filter_psix = interpolate.interp1d(x, array[:,9],
                                                    bounds_error=False,
                                                    fill_value=0.0)
            self.filter_psiy = interpolate.interp1d(x, array[:,10],
                                                    bounds_error=False,
                                                    fill_value=0.0)
        if 'air' in flight_data:
            table = []
            has_wind = False
            has_alphabeta = False
            for air in flight_data['air']:
                record = [air.time, air.airspeed, air.alt_true]
                if hasattr(air, 'wind_dir') and hasattr(air, 'wind_speed'):
                    record.append( air.wind_dir )
                    record.append( air.wind_speed )
                    has_wind = True
                if hasattr(air, 'alpha_deg') and hasattr(air, 'beta_deg'):
                    record.append( air.alpha_deg )
                    record.append( air.beta_deg )
                    has_alphabeta = True
                table.append(record)
            array = np.array(table)
            x = array[:,0]
            self.air_speed = interpolate.interp1d(x, array[:,1],
                                                  bounds_error=False,
                                                  fill_value=0.0)
            self.air_true_alt = interpolate.interp1d(x, array[:,2],
                                                     bounds_error=False,
                                                     fill_value=0.0)
            if has_wind:
                self.air_wind_dir = interpolate.interp1d(x, array[:,3],
                                                         bounds_error=False,
                                                         fill_value=0.0)
                self.air_wind_speed = interpolate.interp1d(x, array[:,4],
                                                           bounds_error=False,
                                                           fill_value=0.0)
            if has_alphabeta:
                if has_wind:
                    base = 5
                else:
                    base = 3
                print("air data has alpha/beta data")
                self.air_alpha = interpolate.interp1d(x, array[:,base],
                                                      bounds_error=False,
                                                      fill_value=0.0)
                self.air_beta = interpolate.interp1d(x, array[:,(base+1)],
                                                     bounds_error=False,
                                                     fill_value=0.0)
        if 'pilot' in flight_data:
            table = []
            for pilot in flight_data['pilot']:
                table.append([pilot.time,
                              pilot.aileron,
                              pilot.elevator,
                              pilot.throttle,
                              pilot.rudder,
                              pilot.gear,
                              pilot.flaps,
                              pilot.aux1,
                              pilot.auto_manual])
            array = np.array(table)
            x = array[:,0]
            self.pilot_ail = interpolate.interp1d(x, array[:,1],
                                                  bounds_error=False,
                                                  fill_value=0.0)
            self.pilot_ele = interpolate.interp1d(x, array[:,2],
                                                  bounds_error=False,
                                                  fill_value=0.0)
            self.pilot_thr = interpolate.interp1d(x, array[:,3],
                                                  bounds_error=False,
                                                  fill_value=0.0)
            self.pilot_rud = interpolate.interp1d(x, array[:,4],
                                                  bounds_error=False,
                                                  fill_value=0.0)
            self.pilot_auto = interpolate.interp1d(x, array[:,8],
                                                   bounds_error=False,
                                                   fill_value=0.0)
        if 'act' in flight_data:
            table = []
            for act in flight_data['act']:
                table.append([act.time,
                              act.aileron,
                              act.elevator,
                              act.throttle,
                              act.rudder,
                              act.gear,
                              act.flaps,
                              act.aux1])
            array = np.array(table)
            x = array[:,0]
            self.act_ail = interpolate.interp1d(x, array[:,1],
                                                bounds_error=False,
                                                fill_value=0.0)
            self.act_ele = interpolate.interp1d(x, array[:,2],
                                                bounds_error=False,
                                                fill_value=0.0)
            self.act_thr = interpolate.interp1d(x, array[:,3],
                                                bounds_error=False,
                                                fill_value=0.0)
            self.act_rud = interpolate.interp1d(x, array[:,4],
                                                bounds_error=False,
                                                fill_value=0.0)
        if 'ap' in flight_data and len(flight_data['ap']):
            table = []
            for ap in flight_data['ap']:
                hdgx = math.cos(ap.hdg*d2r)
                hdgy = math.sin(ap.hdg*d2r)
                table.append([ap.time,
                              hdgx, hdgy,
                              ap.roll,
                              ap.alt,
                              ap.pitch,
                              ap.speed])
            array = np.array(table)
            x = array[:,0]
            self.ap_hdgx = interpolate.interp1d(x, array[:,1],
                                                bounds_error=False,
                                                fill_value=0.0)
            self.ap_hdgy = interpolate.interp1d(x, array[:,2],
                                                bounds_error=False,
                                                fill_value=0.0)
            self.ap_roll = interpolate.interp1d(x, array[:,3],
                                                bounds_error=False,
                                                fill_value=0.0)
            self.ap_alt = interpolate.interp1d(x, array[:,4],
                                               bounds_error=False,
                                               fill_value=0.0)
            self.ap_pitch = interpolate.interp1d(x, array[:,5],
                                                 bounds_error=False,
                                                 fill_value=0.0)
            self.ap_speed = interpolate.interp1d(x, array[:,6],
                                                 bounds_error=False,
                                                 fill_value=0.0)
            
        if 'health' in flight_data and len(flight_data['health']):
            table = []

            has_test_index = False
            for health in flight_data['health']:
                row = [health.time, health.main_vcc]
                if hasattr(health, 'excite_mode') and hasattr(health, 'test_index'):
                    has_test_index = True
                    row.append(health.excite_mode)
                    row.append(health.test_index)
                table.append(row)
            array = np.array(table)
            x = array[:,0]
            self.power_main = interpolate.interp1d(x, array[:,1],
                                                   bounds_error=False,
                                                   fill_value=0.0)
            if has_test_index:
                self.excite_mode = interpolate.interp1d(x, array[:,2],
                                                        bounds_error=False,
                                                        fill_value=0.0)
                self.test_index = interpolate.interp1d(x, array[:,3],
                                                       bounds_error=False,
                                                       fill_value=0.0)
                
