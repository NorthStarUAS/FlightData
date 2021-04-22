# load a ardupilot log file

import csv
from copy import copy
import math
import numpy as np
import re

d2r = math.pi / 180.0
r2d = 180.0/ math.pi
mps2kt = 1.94384
m2ft = 1.0 / 0.3048

select_imu = "IMU2"
select_mag = "MAG2"

# convert value (string) to float, check for "" and return 0.0
def my_float(value):
    if value != "":
        return float(value)
    else:
        return 0.0
    
def load(csv_file):
    result = {}
    result["imu"] = []
    result["gps"] = []
    result["air"] = []
    result["filter"] = []
    result["pilot"] = []
    #result["act"] = []
    #result["ap"] = []

    imu = {}
    nav = {}
    air = {}
    
    last_gps_time = -1.0
    with open(csv_file, "r") as f:
        reader = csv.reader(f)
        for row in reader:
            #print(row)
            if row[0] == select_imu:
                imu["time"] = float(row[1]) / 1000000.0
                imu["p"] = float(row[2])
                imu["q"] = float(row[3])
                imu["r"] = float(row[4])
                imu["ax"] = float(row[5])
                imu["ay"] = float(row[6])
                imu["az"] = float(row[7])
                imu["temp"] = float(row[10])
            if row[0] == select_mag:
                imu["hx"] = float(row[2])
                imu["hy"] = float(row[3])
                imu["hz"] = float(row[4])
                # hf = np.array( [hx, hy, hz] )
                # norm = np.linalg.norm(hf)
                # hf /= norm
                # imu["hx"] = hf[0]
                # imu["hy"] = hf[1]
                # imu["hz"] = hf[2]
                #print imu["hx, imu["hy, imu["hz
                result["imu"].append( copy(imu) )
            if row[0] == "GPS":
                gps = {}
                gps["time"] = float(row[1]) / 1000000.0
                gps["unix_sec"] = gps["time"]
                gps["lat"] = float(row[7])
                gps["lon"] = float(row[8])
                gps["alt"] = float(row[9])
                speed_mps = float(row[10])
                course_deg = float(row[11])
                angle_rad = (90 - course_deg) * d2r
                gps["vn"] = math.sin(angle_rad) * speed_mps
                gps["ve"] = math.cos(angle_rad) * speed_mps
                gps["vd"] = float(row[12])
                gps["sats"] = int(row[5])
                if gps["sats"] >= 5 and gps["unix_sec"] > last_gps_time:
                    result["gps"].append(gps)
                last_gps_time = gps["unix_sec"]

            if row[0] == "ARSP":
                air["airspeed"] = float(row[2]) * mps2kt
                air["diff_press"] = float(row[3])
            if row[0] == "BARO":
                air["time"] = float(row[1]) / 1000000.0
                air["static_press"] = float(row[3])
                air["temp"] = float(row[4])
                air["alt_press"] = float(row[2])
                air["alt_true"] = 0.0
                result["air"].append( copy(air) )

            if row[0] == "NKF1":
                nav["vn"] = float(row[5])
                nav["ve"] = float(row[6])
                nav["vd"] = float(row[7])
                nav["p_bias"] = float(row[12])*d2r
                nav["q_bias"] = float(row[13])*d2r
                nav["r_bias"] = float(row[14])*d2r
            if row[0] == "NKF2":
                nav["az_bias"] = float(row[3])
            if row[0] == "AHR2":
                nav["time"] = float(row[1]) / 1000000.0
                nav["lat"] = float(row[6])*d2r
                nav["lon"] = float(row[7])*d2r
                nav["alt"] = float(row[5])
                nav["phi"] = float(row[2])*d2r
                nav["the"] = float(row[3])*d2r
                psi = float(row[4])
                if psi > 180.0:
                    psi = psi - 360.0
                if psi < -180.0:
                    psi = psi + 360.0
                nav["psi"] = psi*d2r
                nav["ax_bias"] = 0
                nav["ay_bias"] = 0
                result["filter"].append(copy(nav))

            if row[0] == "AETR":
                pilot = {
                    "time": float(row[1]) / 1000000.0,
                    "auto_manual": 0,
                    "throttle_safety": 0,
                    "aileron": float(row[2]) / 100.0,
                    "elevator": float(row[3]) / 100.0,
                    "throttle": float(row[4]) / 100.0,
                    "rudder": float(row[5]) / 100.0,
                    "flaps": 0,
                    "aux1": 0,
                    "geare": 0
                }
                result["pilot"].append(pilot)
                
            if row[0] == "AUTO":
                ap = Record()
                ap.time = imu.time
                ap.hdg = my_float(row["ATSP_YawSP"]) * r2d
                ap.roll = my_float(row["ATSP_RollSP"]) * r2d
                ap.alt = my_float(row["GPSP_Alt"]) * m2ft
                ap.pitch = my_float(row["ATSP_PitchSP"]) * r2d
                ap.speed = my_float(row["TECS_AsSP"]) * mps2kt
                result["ap"].append(ap)
                
            if row[0] == "EFF":
                act = Record()
                ch0 = (float(row["OUT0_Out0"]) - 1500) / 500
                ch1 = (float(row["OUT0_Out1"]) - 1500) / 500 
                ch2 = (float(row["OUT0_Out2"]) - 1000) / 1000
                ch3 = (float(row["OUT0_Out3"]) - 1500) / 500
                #print ch0, ch1, ch2, ch3
                act.time = imu.time
                act.aileron = (ch0 - ch1)
                act.elevator = -(ch0 + ch1)
                act.throttle = ch2
                act.rudder = ch3
                act.gear = 0.0
                act.flaps = 0.0
                act.aux1 = 0.0
                act.auto_manual = 0.0
                result["act"].append(act)

    return result
