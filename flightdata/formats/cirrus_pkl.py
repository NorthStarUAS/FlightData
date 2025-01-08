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
        "airdata": [],
        "nav": [],
        "inceptors": [],
        "effectors": [],
        "fcs": [],
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
                "timestamp": time_s[i],
                "millis": time_s[i] * 1000.0,
                "p_rps": gyro[0][i],
                "q_rps": gyro[1][i],
                "r_rps": gyro[2][i],
                "ax_mps2": accel[0][i],
                "ay_mps2": accel[1][i],
                "az_mps2": accel[2][i],
                "hx": 0.0,
                "hy": 0.0,
                "hz": 0.0,
                "temp_C": 0.0,
            }
            result["imu"].append( imu )

        lla = data["rGps_D_ddm"]
        vel = data["vGps_L_mps"]
        for i in range(records):
            gps = {
                "timestamp": time_s[i],
                "millis": time_s[i] * 1000.0,
                "unix_usec": time_s[i] * 1000000.0,
                "latitude_deg": lla[0][i],
                "longitude_deg": lla[1][i],
                "altitude_m": lla[2][i],  # MSL
                "vn_mps": vel[0][i],
                "ve_mps": vel[1][i],
                "vd_mps": vel[2][i],
                "num_sats": 8
            }
            result["gps"].append(gps)

        static_mbar = data["pStatic_Pa"] / 100.0
        diff_pa = data["pDiff_Pa"]
        vcas_kt = data["vCas_mps"] * mps2kt
        alt_m = data["altBaro_m"]
        alpha_deg = data["alpha_rad"] * r2d
        beta_deg = data["beta_rad"] * r2d
        for i in range(records):
            airdata = {
                "timestamp": time_s[i],
                "millis": time_s[i] * 1000.0,
                "bar_press_pa": static_mbar[i] * 100.0,
                "diff_press_pa": diff_pa[i],
                "airspeed_mps": vcas_kt[i] * kt2mps,
                "altitude_m": alt_m[i],
                "alpha_deg": alpha_deg[i],
                "beta_deg": beta_deg[i],
            }
            result["airdata"].append( airdata )

        euler = data["sB_rad"]
        psix = np.cos(euler[2])
        psiy = np.sin(euler[2])
        for i in range(records):
            nav = {
                "timestamp": time_s[i],
                "millis": time_s[i] * 1000.0,
                "latitude_deg": lla[0][i],
                "longitude_deg": lla[1][i],
                "altitude_m": lla[2][i],  # MSL
                "vn_mps": vel[0][i],
                "ve_mps": vel[1][i],
                "vd_mps": vel[2][i],
                "phi_deg": euler[0][i] * r2d,
                "theta_deg": euler[1][i] * r2d,
                "psi_deg": euler[2][i] * r2d,
                "psix": psix[i],
                "psiy": psiy[i],
            }
            result["nav"].append(nav)

        power = data["engPwr_nd"]
        ail = data["dAilL_rad"] * r2d / 12.5
        ele = data["dElev_rad"] * r2d / 25
        rud = data["dRud_rad"] * r2d / 20
        flaps = data["dFlap_nd"]
        for i in range(records):
            inceptors = {
                "timestamp": time_s[i],
                "millis": time_s[i] * 1000.0,
                "power": power[i],
                "roll": ail[i],
                "pitch": ele[i],  # technically +15,-25 but this makes it symmetric about zero
                "yaw": -rud[i],
                "flaps": flaps[i],
                "master_switch": 0,
                "motor_enable": 1,
                "aux1": 0,
                "aux2": 0,
            }
            result["inceptors"].append(inceptors)

        for i in range(records):
            effectors = {
                "timestamp": time_s[i],
                "millis": time_s[i] * 1000,
                # "channel": [ power[i], ail[i], ele[i], -rud[i], flaps[i], 0, 0 ]
                "power": power[i],
                "aileron": ail[i],
                "elevator": ele[i],
                "rudder": -rud[i],
                "flaps": flaps[i]
            }
            result["effectors"].append(effectors)

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

    # Ack, throwing CHris under the bus here, his interpolation is bunk, (but he
    # only had to add that to work around flaws in the data that I was unable to
    # fix.)  Let's try to find those bad sections and just delete them.  This
    # leaves gaps, but I think that's preferable to wildly wrong data.

    # find/filter not-useful interpolated sections
    from scipy.ndimage import gaussian_filter1d
    from matplotlib import pyplot as plt
    accel = data["aB_B_mps2"]
    ax = accel[0]
    ay = accel[1]
    az = accel[2]
    total_accel = np.sqrt( ax*ax + ay*ay + az*az )

    # cutoff_freq = 0.05
    # b, a = signal.butter(4, cutoff_freq, analog=False)
    # print(b,a)
    # filt = signal.filtfilt(b, a, total_accel)
    filt = gaussian_filter1d(total_accel, 2)
    print("total_accel shape:", total_accel.shape)
    print("filt shape:", filt.shape)
    print("filt:", filt)
    diff = total_accel-filt
    # diff = diff[np.abs(diff)<0.2]
    # plt.figure()
    # plt.plot(total_accel, label="total_accels")
    print("finding segments...")
    segments = []
    thresh = 0.2
    start = 0
    while start < len(diff):
        end = start
        while end < len(diff) and abs(diff[end]) < thresh:
            end += 1
        if end - start > 25:
            # 0.5 sec
            print("adding segment:", [start-5, end+5])
            segments.append([start-5, end+5])
            # plt.axvspan(start-5, end+5, alpha=0.5, color='red')
        start = end + 1
    # plt.legend()
    # plt.show()

    # now delete those segments!
    for segment in reversed(segments):
        del result["imu"][segment[0]:segment[1]]
        del result["gps"][segment[0]:segment[1]]
        del result["airdata"][segment[0]:segment[1]]
        del result["nav"][segment[0]:segment[1]]
        del result["inceptors"][segment[0]:segment[1]]
        del result["effectors"][segment[0]:segment[1]]

    return result
