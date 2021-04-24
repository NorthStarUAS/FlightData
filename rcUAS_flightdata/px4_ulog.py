# load px4 ulog file

from copy import copy
import math
import numpy as np
from scipy import interpolate

d2r = math.pi / 180.0
r2d = 180.0/ math.pi
mps2kt = 1.94384
m2ft = 1.0 / 0.3048

select_imu = "IMU2"
select_mag = "MAG2"

def px4_norm(q):
    return math.sqrt(q[0]*q[0] + q[1]*q[1] + q[2]*q[2] + q[3]*q[3])

def px4_quat2euler(q):
    #print q
    norm = px4_norm(q)
    if norm > 0.000001:
        # normalize quat
        for i in range(4):
            q[i] /= norm
    # create Euler angles vector from the quaternion
    roll = math.atan2(2.0 * (q[0] * q[1] + q[2] * q[3]),
                      1.0 - 2.0 * (q[1] * q[1] + q[2] * q[2]))
    pitch = math.asin(2.0 * (q[0] * q[2] - q[3] * q[1]))
    yaw = math.atan2(2.0 * (q[0] * q[3] + q[1] * q[2]),
                     1.0 - 2.0 * (q[2] * q[2] + q[3] * q[3]))
    return (roll, pitch, yaw)

def load(ulog_file):
    from pyulog.core import ULog    # pip install pyulog
    
    result = {}
    result["imu"] = []
    result["gps"] = []
    result["air"] = []
    result["filter"] = []
    #result["pilot"] = []
    #result["act"] = []
    #result["ap"] = []

    nav = {}
    air = {}

    messages = ["sensor_accel",
                "sensor_combined",
                "vehicle_air_data",
                "vehicle_attitude",
                "vehicle_global_position",
                "vehicle_gps_position",
                "vehicle_magnetometer"]
    
    ulog = ULog(ulog_file, messages)
    data = ulog.data_list

    for d in data:
        print(d.name, d.multi_id)
        for f in d.field_data:
            print(" ", f.field_name)
        if d.name == "sensor_accel" and d.multi_id == 0:
            imu_temps = []
            for i in range(len(d.data["timestamp"])):
                temp = [
                    d.data["timestamp"][i],
                    d.data["temperature"][i]
                ]
                imu_temps.append(temp)
            imu_temps = np.array(imu_temps)
            temp_interp = interpolate.interp1d(imu_temps[:,0], imu_temps[:,1],
                                             bounds_error=False,
                                             fill_value='extrapolate')
        if d.name == "vehicle_magnetometer" and d.multi_id == 0:
            mags = []
            for i in range(len(d.data["timestamp"])):
                mag = [
                    d.data["timestamp"][i],
                    d.data["magnetometer_ga[0]"][i],
                    d.data["magnetometer_ga[1]"][i],
                    d.data["magnetometer_ga[2]"][i]
                ]
                mags.append(mag)
            mags = np.array(mags)
            hx_interp = interpolate.interp1d(mags[:,0], mags[:,1],
                                             bounds_error=False,
                                             fill_value='extrapolate')
            hy_interp = interpolate.interp1d(mags[:,0], mags[:,2],
                                             bounds_error=False,
                                             fill_value='extrapolate')
            hz_interp = interpolate.interp1d(mags[:,0], mags[:,3],
                                             bounds_error=False,
                                             fill_value='extrapolate')
        if d.name == "sensor_combined" and d.multi_id == 0:
            for i in range(len(d.data["timestamp"])):
                t = d.data["timestamp"][i]
                imu = {
                    "time": t / 1e6,
                    "p": d.data["gyro_rad[0]"][i],
                    "q": d.data["gyro_rad[1]"][i],
                    "r": d.data["gyro_rad[2]"][i],
                    "ax": d.data["accelerometer_m_s2[0]"][i],
                    "ay": d.data["accelerometer_m_s2[1]"][i],
                    "az": d.data["accelerometer_m_s2[2]"][i],
                    "hx": float(hx_interp(t)),
                    "hy": float(hy_interp(t)),
                    "hz": float(hz_interp(t)),
                    "temp": float(temp_interp(t))
                }
                result["imu"].append(imu)
        if d.name == "vehicle_gps_position" and d.multi_id == 0:
            for i in range(len(d.data["timestamp"])):
                gps = {
                    "time": d.data["timestamp"][i] / 1e6,
                    "unix_sec": d.data["time_utc_usec"][i] / 1e6,
                    "lat": d.data["lat"][i] / 1e7,
                    "lon": d.data["lon"][i] / 1e7,
                    "alt": d.data["alt"][i] / 1e3,
                    "vn": d.data["vel_n_m_s"][i],
                    "ve": d.data["vel_e_m_s"][i],
                    "vd": d.data["vel_d_m_s"][i],
                    "sats": d.data["satellites_used"][i]
                }
                print(gps)
                if gps["sats"] >= 5:
                    result["gps"].append(gps)
        if d.name == "vehicle_air_data" and d.multi_id == 0:
            for i in range(len(d.data["timestamp"])):
                air = {
                    "time": d.data["timestamp"][i] / 1e6,
                    "static_press": d.data["baro_pressure_pa"][i],
                    "diff_press": 0.0, 
                    "temp": d.data["baro_temp_celcius"][i],
                    "airspeed": 0,
                    "alt_press": d.data["baro_alt_meter"][i],
                    "alt_true": 0,
                    "tecs_error_total": 0,
                    "tecs_error_diff": 0,
                    "wind_dir": 0,
                    "wind_speed": 0,
                    "pitot_scale": 1
                }
                result["air"].append(air)
        if d.name == "vehicle_global_position" and d.multi_id == 0:
            poses = []
            for i in range(len(d.data["timestamp"])):
                pos = [
                    d.data["timestamp"][i],
                    d.data["lat"][i],
                    d.data["lon"][i],
                    d.data["alt"][i]
                ]
                poses.append(pos)
            poses = np.array(poses)
            lat_interp = interpolate.interp1d(poses[:,0], poses[:,1],
                                              bounds_error=False,
                                              fill_value='extrapolate')
            lon_interp = interpolate.interp1d(poses[:,0], poses[:,2],
                                              bounds_error=False,
                                              fill_value='extrapolate')
            alt_interp = interpolate.interp1d(poses[:,0], poses[:,3],
                                              bounds_error=False,
                                              fill_value='extrapolate')
        if d.name == "vehicle_attitude" and d.multi_id == 0:
            filter = []
            for i in range(len(d.data["timestamp"])):
                q = [ d.data["q[0]"][i],
                      d.data["q[1]"][i],
                      d.data["q[2]"][i],
                      d.data["q[3]"][i] ]
                (roll, pitch, yaw) = px4_quat2euler(q)
                t = d.data["timestamp"][i]
                nav = {
                    "time": t / 1e6,
                    "lat": lat_interp(t)*d2r,
                    "lon": lon_interp(t)*d2r,
                    "alt": alt_interp(t),
                    "vn": 0,
                    "ve": 0,
                    "vd": 0,
                    "phi": roll,
                    "the": pitch,
                    "psi": yaw,
                    "p_bias": 0,
                    "q_bias": 0,
                    "r_bias": 0,
                    "ax_bias": 0,
                    "ay_bias": 0,
                    "az_bias": 0
                }
                result["filter"].append(nav)

    return result
