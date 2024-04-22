# load cirrus pkl data format

from math import pi
import numpy as np
import pickle

d2r = pi / 180.0
r2d = 180.0 / pi
kt2mps = 0.5144444444444444444
mps2kt = 1.0 / kt2mps

def load(pkl_file):
    result = {
        "imu": [],
        "gps": [],
        "air": [],
        "filter": [],
        "pilot": [],
        "act": [],
        "ap": [],
        # "health": [],
    }

    with open(pkl_file, "rb") as f:
        data = pickle.load(f)

        time_s = data["time_s"]
        records = len(time_s)

        gyro = data["wB_B_rps"]
        accel = data["aB_B_mps2"]
        for i in range(records):
            imu = {
                "time": time_s[i],
                "p": gyro[0][i],
                "q": gyro[1][i],
                "r": gyro[2][i],
                "ax": accel[0][i],
                "ay": accel[1][i],
                "az": accel[2][i],
                "hx": 0.0,
                "hy": 0.0,
                "hz": 0.0,
                "temp": 0.0,
            }
            result["imu"].append( imu )

        lla = data["rGps_D_ddm"]
        vel = data["vGps_L_mps"]
        for i in range(records):
            gps = {
                "time": time_s[i],
                "unix_sec": time_s[i],
                "lat": lla[0][i],
                "lon": lla[1][i],
                "alt": lla[2][i],  # MSL
                "vn": vel[0][i],
                "ve": vel[1][i],
                "vd": vel[2][i],
                "sats": 8
            }
            result["gps"].append(gps)

        static_mbar = data["pStatic_Pa"] / 100.0
        diff_pa = data["pDiff_Pa"]
        vcas_kt = data["vCas_mps"] * mps2kt
        alt_m = data["altBaro_m"]
        alpha_deg = data["alpha_rad"] * r2d
        beta_deg = data["beta_rad"] * r2d
        for i in range(records):
            air = {
                "time": time_s[i],
                "static_press": static_mbar[i],
                "diff_press": diff_pa[i],
                "airspeed": vcas_kt[i],
                "alt_press": alt_m[i],
                "alpha": alpha_deg[i],
                "beta": beta_deg[i],
            }
            result["air"].append( air )

        lat_rad = lla[0] * d2r
        lon_rad = lla[1] * d2r
        euler = data["sB_rad"]
        psix = np.cos(euler[2])
        psiy = np.sin(euler[2])
        for i in range(records):
            nav = {
                "time": time_s[i],
                "lat": lat_rad[i],
                "lon": lon_rad[i],
                "alt": lla[2][i],
                "vn": vel[0][i],
                "ve": vel[1][i],
                "vd": vel[2][i],
                "phi": euler[0][i],
                "the": euler[1][i],
                "psi": euler[2][i],
                "psix": psix[i],
                "psiy": psiy[i],
            }
            result["filter"].append(nav)

        power = data["engPwr_nd"]
        ail = data["dAilL_rad"] * r2d / 12.5
        ele = data["dElev_rad"] * r2d / 25
        rud = data["dRud_rad"] * r2d / 20
        flaps = data["dFlap_nd"]
        for i in range(records):
            pilot = {
                "time": time_s[i],
                "throttle": power[i],
                "aileron": ail[i],
                "elevator": ele[i],  # technically +15,-25 but this makes it symmetric about zero
                "rudder": -rud[i],
                "flaps": flaps[i],
                "auto_manual": 0,
                "aux1": 0,
            }
            result["pilot"].append(pilot)

        for i in range(records):
            act = {
                "time": time_s[i],
                "throttle": power[i],
                "aileron": ail[i],
                "elevator": ele[i],  # technically +15,-25 but this makes it symmetric about zero
                "rudder": -rud[i],
                "flaps": flaps[i],
                "auto_manual": 0,
                "aux1": 0,
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
