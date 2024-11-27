import csv
import h5py
import os
import math
import re

d2r = math.pi / 180.0

# empty class we'll fill in with data members
# class Record: pass (deprecated)

def load(h5_filename):
    filepath = h5_filename
    flight_dir = os.path.dirname(filepath)

    # open the hdf5 file
    data = h5py.File(filepath, "r")

    result = {}

    print("  loading events...")
    millis = data["/events/millis"][()]
    message = data["/events/message"][()]
    result["event"] = []
    for i in range(len(millis)):
        event = {
            "timestamp": millis[i] / 1000.0,
            "message": str(message[i])
        }
        result["event"].append(event)

    print("  loading imu...")
    millis = data["/sensors/imu/millis"][()]
    gx = data["/sensors/imu/p_rps"][()]
    gy = data["/sensors/imu/q_rps"][()]
    gz = data["/sensors/imu/r_rps"][()]
    ax = data["/sensors/imu/ax_mps2"][()]
    ay = data["/sensors/imu/ay_mps2"][()]
    az = data["/sensors/imu/az_mps2"][()]
    if "/sensors/imu/ax_raw" in data:
        ax_raw = data["/sensors/imu/ax_raw"][()]
        ay_raw = data["/sensors/imu/ay_raw"][()]
        az_raw = data["/sensors/imu/az_raw"][()]
    hx = data["/sensors/imu/hx"][()]
    hy = data["/sensors/imu/hy"][()]
    hz = data["/sensors/imu/hz"][()]
    if "/sensors/imu/hx_raw" in data:
        hx_raw = data["/sensors/imu/hx_raw"][()]
        hy_raw = data["/sensors/imu/hy_raw"][()]
        hz_raw = data["/sensors/imu/hz_raw"][()]
    temp = data["/sensors/imu/temp_C"][()]
    result["imu"] = []
    for i in range(len(millis)):
        imu = {
            "timestamp": millis[i] / 1000.0,
            "p": gx[i],
            "q": gy[i],
            "r": gz[i],
            "ax": ax[i],
            "ay": ay[i],
            "az": az[i],
            "hx": hx[i],
            "hy": hy[i],
            "hz": hz[i],
            "temp": temp[i]
        }
        if "/sensors/imu/ax_raw" in data:
            imu["ax_raw"] = ax_raw[i]
            imu["ay_raw"] = ay_raw[i]
            imu["az_raw"] = az_raw[i]
        if "/sensors/imu/hx_raw" in data:
            imu["hx_raw"] = hx_raw[i]
            imu["hy_raw"] = hy_raw[i]
            imu["hz_raw"] = hz_raw[i]
        result["imu"].append(imu)

    print("  loading gps...")
    millis = data["/sensors/gps/millis"][()]
    unix_usec = data["/sensors/gps/unix_usec"][()]
    lat_raw = data["/sensors/gps/latitude_raw"][()]
    lon_raw = data["/sensors/gps/longitude_raw"][()]
    alt = data["/sensors/gps/altitude_m"][()]
    vn = data["/sensors/gps/vn_mps"][()]
    ve = data["/sensors/gps/ve_mps"][()]
    vd = data["/sensors/gps/vd_mps"][()]
    sats = data["/sensors/gps/num_sats"][()]
    status = data["/sensors/gps/status"][()]
    result["gps"] = []
    for i in range(len(millis)):
        gps = {
            "timestamp": millis[i] / 1000.0,
            "unix_sec": unix_usec[i] / 1000000.0,
            "latitude_deg": lat_raw[i] / 10000000.0,
            "longitude_deg": lon_raw[i] / 10000000.0,
            "altitude_m": alt[i],
            "vn_mps": vn[i],
            "ve_mps": ve[i],
            "vd_mps": vd[i],
            "num_sats": sats[i],
            "status": status[i]
        }
        result["gps"].append(gps)

    print("  loading airdata...")
    millis = data["/sensors/airdata/millis"][()]
    temp = data["/sensors/airdata/air_temp_C"][()]
    airspeed = data["/sensors/airdata/airspeed_mps"][()]
    baro_press = data["/sensors/airdata/baro_press_pa"][()]
    diff_press = data["/sensors/airdata/diff_press_pa"][()]
    error_count = data["/sensors/airdata/error_count"][()]
    result["airdata"] = []
    for i in range(len(millis)):
        air = {
            "timestamp": millis[i] / 1000.0,
            "temp_C": temp[i],
            "airspeed_mps": airspeed[i],
            "baro_press_pa": baro_press[i],
            "diff_press_pa": diff_press[i],
            "error_count": error_count[i]
        }
        result["airdata"].append( air )

    print("  loading environment...")
    millis = data["/filters/env/millis"][()]
    alt_agl = data["/filters/env/altitude_agl_m"][()]
    alt_ground = data["/filters/env/altitude_ground_m"][()]
    alt_true = data["/filters/env/altitude_true_m"][()]
    flight_timer = data["/filters/env/flight_timer_millis"][()]
    is_airborne = data["/filters/env/is_airborne"][()]
    pitot_scale = data["/filters/env/pitot_scale_factor"][()]
    wind_deg = data["/filters/env/wind_deg"][()]
    wind_mps = data["/filters/env/wind_mps"][()]
    result["env"] = []
    for i in range(len(millis)):
        env = {
            "timestamp": millis[i] / 1000.0,
            "altitude_agl_m": alt_agl[i],
            "altitude_ground_m": alt_ground[i],
            "alt_true": alt_true[i],
            "flight_timer_sec": flight_timer[i] / 1000.0,
            "is_airborne": is_airborne[i],
            "pitot_scale": pitot_scale[i],
            "wind_deg": wind_deg[i],
            "wind_mps": wind_mps[i],
        }
        result["env"].append( env )

    print("  loading nav...")
    millis = data["/filters/nav/millis"][()]
    lat_deg = data["/filters/nav/latitude_raw"][()]/10000000.0
    lon_deg = data["/filters/nav/longitude_raw"][()]/10000000.0
    alt_m = data["/filters/nav/altitude_m"][()]
    vn_mps = data["/filters/nav/vn_mps"][()]
    ve_mps = data["/filters/nav/ve_mps"][()]
    vd_mps = data["/filters/nav/vd_mps"][()]
    roll_deg = data["/filters/nav/roll_deg"][()]
    pitch_deg = data["/filters/nav/pitch_deg"][()]
    yaw_deg = data["/filters/nav/yaw_deg"][()]
    result["nav"] = []
    for i in range(len(millis)):
        psi = yaw_deg[i]*d2r
        if psi > math.pi:
            psi -= 2*math.pi
        if psi < -math.pi:
            psi += 2*math.pi
        psix = math.cos(psi)
        psiy = math.sin(psi)
        if abs(lat_deg[i]) > 0.0001 and abs(lon_deg[i]) > 0.0001:
            nav = {
                "timestamp": millis[i] / 1000.0,
                "latitude_deg": lat_deg[i],
                "longitude_deg": lon_deg[i],
                "altitude_m": alt_m[i],
                "vn_mps": vn_mps[i],
                "ve_mps": ve_mps[i],
                "vd_mps": vd_mps[i],
                "phi": roll_deg[i]*d2r,
                "the": pitch_deg[i]*d2r,
                "psi": psi,
                "psix": psix,
                "psiy": psiy,
            }
            result["nav"].append(nav)

    print("  loading nav metrics...")
    millis = data["/filters/nav_metrics/metrics_millis"][()]
    gbx = data["/filters/nav_metrics/p_bias"][()]
    gby = data["/filters/nav_metrics/q_bias"][()]
    gbz = data["/filters/nav_metrics/r_bias"][()]
    abx = data["/filters/nav_metrics/ax_bias"][()]
    aby = data["/filters/nav_metrics/ay_bias"][()]
    abz = data["/filters/nav_metrics/az_bias"][()]
    Pa0 = data["/filters/nav_metrics/Pa0"][()]
    Pa1 = data["/filters/nav_metrics/Pa1"][()]
    Pa2 = data["/filters/nav_metrics/Pa2"][()]
    Pp0 = data["/filters/nav_metrics/Pp0"][()]
    Pp1 = data["/filters/nav_metrics/Pp1"][()]
    Pp2 = data["/filters/nav_metrics/Pp2"][()]
    Pv0 = data["/filters/nav_metrics/Pv0"][()]
    Pv1 = data["/filters/nav_metrics/Pv1"][()]
    Pv2 = data["/filters/nav_metrics/Pv2"][()]
    result["nav_metrics"] = []
    for i in range(len(millis)):
        if abs(lat_deg[i]) > 0.0001 and abs(lon_deg[i]) > 0.0001:
            nav_metrics = {
                "timestamp": millis[i] / 1000.0,
                "p_bias": gbx[i],
                "q_bias": gby[i],
                "r_bias": gbz[i],
                "ax_bias": abx[i],
                "ay_bias": aby[i],
                "az_bias": abz[i],
                "Pa0": Pa0[i],
                "Pa1": Pa1[i],
                "Pa2": Pa2[i],
                "Pp0": Pp0[i],
                "Pp1": Pp1[i],
                "Pp2": Pp2[i],
                "Pv0": Pv0[i],
                "Pv1": Pv1[i],
                "Pv2": Pv2[i],
            }
            result["nav_metrics"].append(nav_metrics)

    print("  loading inceptors...")
    millis = data["/sensors/inceptors/millis"][()]
    master_switch = data["/sensors/inceptors/master_switch"][()]
    motor_enable = data["/sensors/inceptors/motor_enable"][()]
    roll = data["/sensors/inceptors/roll"][()]
    pitch = data["/sensors/inceptors/pitch"][()]
    yaw = data["/sensors/inceptors/yaw"][()]
    power = data["/sensors/inceptors/power"][()]
    flaps = data["/sensors/inceptors/flaps"][()]
    gear = data["/sensors/inceptors/gear"][()]
    aux1 = data["/sensors/inceptors/aux1"][()]
    aux2 = data["/sensors/inceptors/aux2"][()]
    result["inceptors"] = []
    for i in range(len(millis)):
        inceptors = {
            "timestamp": millis[i] / 1000.0,
            "master_switch": master_switch[i],
            "motor_enable": motor_enable[i],
            "roll": roll[i],
            "pitch": pitch[i],
            "yaw": yaw[i],
            "power": power[i],
            "flaps": flaps[i],
            "gear": gear[i],
            "aux1": aux1[i],
            "aux2": aux2[i]
        }
        result["inceptors"].append(inceptors)

    print("  loading effectors...")
    millis = data["/fcs/effectors/millis"][()]
    channel = data["/fcs/effectors/channel"][()]
    result["effectors"] = []
    for i in range(len(millis)):
        effectors = {
            "timestamp": millis[i] / 1000.0,
            "throttle": channel[i][0],
            "aileron": channel[i][1],
            "elevator": channel[i][2],
            "rudder": channel[i][3],
            "flaps": channel[i][4],
            "gear": channel[i][5],
            "aux1": channel[i][6],
            "aux2": channel[i][7]
        }
        result["effectors"].append(effectors)

    print("  loading fcs refs...")
    millis = data["/fcs/refs/millis"][()]
    hdg = data["/fcs/refs/groundtrack_deg"][()]
    roll = data["/fcs/refs/roll_deg"][()]
    pitch = data["/fcs/refs/pitch_deg"][()]
    alt = data["/fcs/refs/altitude_agl_ft"][()]
    speed = data["/fcs/refs/airspeed_kt"][()]
    # tecs_tot = data["/mission/tecs_target_tot"][()]
    # tecs_diff = data["/mission/tecs_target_diff"][()]
    result["refs"] = []
    for i in range(len(millis)):
        hdgx = math.cos(hdg[i]*d2r)
        hdgy = math.sin(hdg[i]*d2r)
        refs = {
            "timestamp": millis[i] / 1000.0,
            "groundtrack_deg": hdg[i],
            "groundtrack_x": hdgx,
            "groundtrack_y": hdgy,
            "roll_deg": roll[i],
            "pitch_deg": pitch[i],
            "altitude_agl_ft": alt[i],
            "airspeed_kt": speed[i],
        }
        result["refs"].append(refs)

    print("  loading mission...")
    millis = data["/mission/millis"][()]
    task_name = data["/mission/task_name"][()]
    task_attrib = data["/mission/task_attribute"][()]
    route_size = data["/mission/route_size"][()]
    target_wpt_idx = data["/mission/target_wpt_idx"][()]
    wpt_index = data["/mission/wpt_index"][()]
    wpt_latitude_deg = data["/mission/wpt_latitude_raw"][()] / 10000000.0
    wpt_longitude_deg = data["/mission/wpt_longitude_raw"][()] / 10000000.0
    result["mission"] = []
    for i in range(len(millis)):
        mission = {
            "timestamp": millis[i] / 1000.0,
            "task_name": task_name,
            "task_attrib": task_attrib,
            "route_size": route_size[i],
            "target_wpt_idx": target_wpt_idx[i],
            "wpt_index": wpt_index[i],
            "wpt_latitude_deg": wpt_latitude_deg[i],
            "wpt_longitude_deg": wpt_longitude_deg[i]
        }
        result["mission"].append(mission)

    print("  loading power...")
    millis = data["/sensors/power/millis"][()]
    avionics_vcc = data["/sensors/power/avionics_vcc"][()]
    main_vcc = data["/sensors/power/main_vcc"][()]
    cell_vcc = data["/sensors/power/cell_vcc"][()]
    pwm_vcc = data["/sensors/power/pwm_vcc"][()]
    result["power"] = []
    for i in range(len(millis)):
        power = {
            "timestamp": millis[i] / 1000.0,
            "avionics_vcc": avionics_vcc[i],
            "main_vcc": main_vcc[i],
            "cell_vcc": cell_vcc[i],
            "pwm_vcc": pwm_vcc[i],
        }
        result["power"].append(power)

    return result

def save_filter_result(filename, nav):
    keys = ["timestamp", "latitude_deg", "longitude_deg", "altitude_m",
            "vn_ms", "ve_ms", "vd_ms", "roll_deg", "pitch_deg", "heading_deg",
            "p_bias", "q_bias", "r_bias", "ax_bias", "ay_bias", "az_bias",
            "status"]
    with open(filename, "w") as csvfile:
        writer = csv.DictWriter( csvfile, fieldnames=keys )
        writer.writeheader()
        for navpt in nav:
            row = dict()
            row["timestamp"] = "%.4f" % navpt["time"]
            row["latitude_deg"] = "%.10f" % (navpt["lat"]*180.0/math.pi)
            row["longitude_deg"] = "%.10f" % (navpt["lon"]*180.0/math.pi)
            row["altitude_m"] = "%.2f" % navpt["alt"]
            row["vn_ms"] = "%.4f" % navpt["vn"]
            row["ve_ms"] = "%.4f" % navpt["ve"]
            row["vd_ms"] = "%.4f" % navpt["vd"]
            row["roll_deg"] = "%.2f" % (navpt["phi"]*180.0/math.pi)
            row["pitch_deg"] = "%.2f" % (navpt["the"]*180.0/math.pi)
            row["heading_deg"] = "%.2f" % (navpt["psi"]*180.0/math.pi)
            row["p_bias"] = "%.4f" % navpt["gbx"]
            row["q_bias"] = "%.4f" % navpt["gby"]
            row["r_bias"] = "%.4f" % navpt["gbz"]
            row["ax_bias"] = "%.3f" % navpt["abx"]
            row["ay_bias"] = "%.3f" % navpt["aby"]
            row["az_bias"] = "%.3f" % navpt["abz"]
            row["status"] = "%d" % 0
            writer.writerow(row)
