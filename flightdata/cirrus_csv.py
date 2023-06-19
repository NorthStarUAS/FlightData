# load cirrus csv data format

import csv
from math import pi, sqrt

g = 9.81
d2r = pi / 180.0
r2d = 180.0 / pi
psf2mbar = 0.47880259

def load(csv_file):
    result = {
        "imu": [],
        "gps": [],
        "air": [],
        "filter": [],
        "pilot": [],
        "act": [],
        "ap": [],
        "health": [],
    }

    last_gps_time = -1.0
    with open(csv_file, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Note: SystemMillis is milliseconds since the start of the UTC day
            # (not unix time, not tow, etc.) but for the purposes of the
            # ins/gnss algorithm, it's only important to have a properly
            # incrementing clock in seconds, it doesn't really matter what the
            # zero reference point of time is here.
            time = float(row["SystemMillis"]) / 1000.0

            imu = {
                "time": time,
                "p": -float(row["gyro_x"]) * d2r,
                "q": float(row["gyro_y"]) * d2r,
                "r": -float(row["gyro_z"]) * d2r,
                "ax": -float(row["Accel_X_millig"]) * g / 1000.0,
                "ay": float(row["Accel_Y_millig"]) * g / 1000.0,
                "az": -float(row["Accel_Z_millig"]) * g / 1000.0,
            }
            result["imu"].append( imu )

            fix = int(row["NavFix"])
            gps_time = int(row["Hour"]) * 3600 + int(row["Min"]) * 60 + int(row["Sec"]) + int(row["Millisec"]) / 1000.0
            if fix == 3 and gps_time > last_gps_time:
                gps = {
                    "time": time,
                    "unix_sec": time,
                    "lat": float(row["Lat_deg"]),
                    "lon": float(row["Lon_deg"]),
                    "alt": float(row["Alt_m"]),  # MSL
                    "vn": float(row["VelN_mps"]),
                    "ve": float(row["VelE_mps"]),
                    "vd": float(row["VelD_mps"]),
                    "sats": int(row["NumSat"])
                }
                result["gps"].append(gps)
                last_gps_time = time

            static_mbar = float(row["AbsPressure"]) * psf2mbar
            diff_mbar = float(row["DelPressure"]) * psf2mbar
            air = {
                "time": time,
                "static_press": static_mbar,
                "diff_press": diff_mbar,
                "airspeed": sqrt((2/1.225)*diff_mbar*100)*1.94384,
                "alt_press": (pow((1013.25/static_mbar), 1/5.257) - 1) * (15+273.15) / 0.0065,
            }
            result["air"].append( air )

            # load filter records if they exist (for comparison purposes)
            # lat = float(row["latitude_deg"])
            # lon = float(row["longitude_deg"])
            # psi_deg = float(row["heading_deg"])
            # psi = psi_deg*d2r
            # if psi > math.pi:
            #     psi -= 2*math.pi
            # if psi < -math.pi:
            #     psi += 2*math.pi
            # psix = math.cos(psi)
            # psiy = math.sin(psi)
            # if abs(lat) > 0.0001 and abs(lon) > 0.0001:
            #     nav = {
            #         "time": float(row["timestamp"]),
            #         "lat": lat*d2r,
            #         "lon": lon*d2r,
            #         "alt": float(row["altitude_m"]),
            #         "vn": float(row["vn_ms"]),
            #         "ve": float(row["ve_ms"]),
            #         "vd": float(row["vd_ms"]),
            #         "phi": float(row["roll_deg"])*d2r,
            #         "the": float(row["pitch_deg"])*d2r,
            #         "psi": psi,
            #         "psix": psix,
            #         "psiy": psiy,
            #         "p_bias": float(row["p_bias"]),
            #         "q_bias": float(row["q_bias"]),
            #         "r_bias": float(row["r_bias"]),
            #         "ax_bias": float(row["ax_bias"]),
            #         "ay_bias": float(row["ay_bias"]),
            #         "az_bias": float(row["az_bias"])
            #     }
            #     result["filter"].append(nav)

            pilot = {
                "time": time,
                #"throttle": float(row["channel[2]"]),
                "aileron": float(row["AileronL"]),
                "elevator": float(row["Elevator"]),
                "rudder": float(row["Rudder"]),
                #"flaps": float(row["Flaps"]),
            }
            result["pilot"].append(pilot)

            act = {
                "time": time,
                #"throttle": float(row["channel[2]"]),
                "aileron": float(row["AileronL"]),
                "elevator": float(row["Elevator"]),
                "rudder": float(row["Rudder"]),
                #"flaps": float(row["Flaps"]),
            }
            result["act"].append(act)

            # hdg = float(row["groundtrack_deg"])
            # hdgx = math.cos(hdg*d2r)
            # hdgy = math.sin(hdg*d2r)
            # ap = {
            #     "time": float(row["timestamp"]),
            #     "master_switch": int(row["master_switch"]),
            #     "pilot_pass_through": int(row["pilot_pass_through"]),
            #     "hdg": hdg,
            #     "hdgx": hdgx,
            #     "hdgy": hdgy,
            #     "roll": float(row["roll_deg"]),
            #     "alt": float(row["altitude_msl_ft"]),
            #     "pitch": float(row["pitch_deg"]),
            #     "speed": float(row["airspeed_kt"]),
            #     "ground": float(row["altitude_ground_m"])
            # }
            # result["ap"].append(ap)

            # health = {
            #     "time": float(row["timestamp"]),
            #     "load_avg": float(row["system_load_avg"])
            # }
            # if "avionics_vcc" in row:
            #     health["avionics_vcc"] = float(row["avionics_vcc"])
            # elif "board_vcc" in row:
            #     health["avionics_vcc"] = float(row["board_vcc"])
            # if "main_vcc" in row:
            #     health["main_vcc"] = float(row["main_vcc"])
            # elif "extern_volts" in row:
            #     health["main_vcc"] = float(row["extern_volts"])
            # if "cell_vcc" in row:
            #     health["cell_vcc"] = float(row["cell_vcc"])
            # elif "extern_cell_volts" in row:
            #     health["cell_vcc"] = float(row["extern_cell_volts"])
            # if "main_amps" in row:
            #     health["main_amps"] = float(row["main_amps"])
            # elif "extern_amps" in row:
            #     health["main_amps"] = float(row["extern_amps"])
            # if "total_mah" in row:
            #     health["main_mah"] = float(row["total_mah"])
            # elif "extern_current_mah" in row:
            #     health["main_mah"] = float(row["extern_current_mah"])
            # result["health"].append(health)

    return result
