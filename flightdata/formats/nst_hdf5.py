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
    millis = data["/status/events/millis"][()]
    message = data["/status/events/message"][()]
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
            "lat_deg": lat_raw[i] / 10000000.0,
            "lon_deg": lon_raw[i] / 10000000.0,
            "alt_m": alt[i],
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
    alt_agl = data["/sensors/airdata/altitude_agl_m"][()]
    alt_ground = data["/sensors/airdata/altitude_ground_m"][()]
    alt_true = data["/sensors/airdata/altitude_true_m"][()]
    baro_press = data["/sensors/airdata/baro_press_pa"][()]
    diff_press = data["/sensors/airdata/diff_press_pa"][()]
    flight_timer = data["/sensors/airdata/flight_timer_millis"][()]
    is_airborne = data["/sensors/airdata/is_airborne"][()]
    pitot_scale = data["/sensors/airdata/pitot_scale_factor"][()]
    wind_dir = data["/sensors/airdata/wind_dir_deg"][()]
    wind_speed = data["/sensors/airdata/wind_speed_mps"][()]
    error_count = data["/sensors/airdata/error_count"][()]
    result["airdata"] = []
    for i in range(len(millis)):
        air = {
            "timestamp": millis[i] / 1000.0,
            "temp_C": temp[i],
            "airspeed_mps": airspeed[i],
            "altitude_agl_m": alt_agl[i],
            "altitude_ground_m": alt_ground[i],
            "alt_true": alt_true[i],
            "baro_press_pa": baro_press[i],
            "diff_press_pa": diff_press[i],
            "flight_timer_sec": flight_timer[i] / 1000.0,
            "is_airborne": is_airborne[i],
            "pitot_scale": pitot_scale[i],
            "wind_dir": wind_dir[i],
            "wind_speed": wind_speed[i],
            "error_count": error_count[i]
        }
        result["airdata"].append( air )

    print("  loading nav...")
    timestamp = data["/navigation/filter/timestamp"][()]
    lat = data["/navigation/filter/latitude_deg"][()]*d2r
    lon = data["/navigation/filter/longitude_deg"][()]*d2r
    alt = data["/navigation/filter/altitude_m"][()]
    vn = data["/navigation/filter/vn_ms"][()]
    ve = data["/navigation/filter/ve_ms"][()]
    vd = data["/navigation/filter/vd_ms"][()]
    roll = data["/navigation/filter/roll_deg"][()]
    pitch = data["/navigation/filter/pitch_deg"][()]
    yaw = data["/navigation/filter/heading_deg"][()]
    gbx = data["/navigation/filter/p_bias"][()]
    gby = data["/navigation/filter/q_bias"][()]
    gbz = data["/navigation/filter/r_bias"][()]
    abx = data["/navigation/filter/ax_bias"][()]
    aby = data["/navigation/filter/ay_bias"][()]
    abz = data["/navigation/filter/az_bias"][()]
    if "/navigation/filter/max_pos_cov" in data:
        max_pos_cov = data["/navigation/filter/max_pos_cov"][()]
        max_vel_cov = data["/navigation/filter/max_vel_cov"][()]
        max_att_cov = data["/navigation/filter/max_att_cov"][()]
    result["filter"] = []
    for i in range(len(timestamp)):
        psi = yaw[i]*d2r
        if psi > math.pi:
            psi -= 2*math.pi
        if psi < -math.pi:
            psi += 2*math.pi
        psix = math.cos(psi)
        psiy = math.sin(psi)
        if abs(lat[i]) > 0.0001 and abs(lon[i]) > 0.0001:
            filter = {
                "time": timestamp[i],
                "lat": lat[i],
                "lon": lon[i],
                "alt": alt[i],
                "vn": vn[i],
                "ve": ve[i],
                "vd": vd[i],
                "phi": roll[i]*d2r,
                "the": pitch[i]*d2r,
                "psi": psi,
                "psix": psix,
                "psiy": psiy,
                "p_bias": gbx[i],
                "q_bias": gby[i],
                "r_bias": gbz[i],
                "ax_bias": abx[i],
                "ay_bias": aby[i],
                "az_bias": abz[i]
            }
            if "/navigation/filter/max_pos_cov" in data:
                filter["max_pos_cov"] = max_pos_cov[i]
                filter["max_vel_cov"] = max_vel_cov[i]
                filter["max_att_cov"] = max_att_cov[i]
            result["filter"].append(filter)

    # load filter (post process) records if they exist (for comparison
    # purposes)
    # if os.path.exists(filter_post):
    #     result["filter_post"] = []
    #     with open(filter_post, "r") as ffilter:
    #         reader = csv.DictReader(ffilter)
    #         for row in reader:
    #             lat = float(row["latitude_deg"])
    #             lon = float(row["longitude_deg"])
    #             psi_deg = float(row["heading_deg"])
    #             psi = psi_deg*d2r
    #             if psi > math.pi:
    #                 psi -= 2*math.pi
    #             if psi < -math.pi:
    #                 psi += 2*math.pi
    #             psix = math.cos(psi)
    #             psiy = math.sin(psi)
    #             if abs(lat) > 0.0001 and abs(lon) > 0.0001:
    #                 nav = {
    #                     "time": float(row["timestamp"]),
    #                     "lat": lat*d2r,
    #                     "lon": lon*d2r,
    #                     "alt": float(row["altitude_m"]),
    #                     "vn": float(row["vn_ms"]),
    #                     "ve": float(row["ve_ms"]),
    #                     "vd": float(row["vd_ms"]),
    #                     "phi": float(row["roll_deg"])*d2r,
    #                     "the": float(row["pitch_deg"])*d2r,
    #                     "psi": psi,
    #                     "psix": psix,
    #                     "psiy": psiy,
    #                     "p_bias": float(row["p_bias"]),
    #                     "q_bias": float(row["q_bias"]),
    #                     "r_bias": float(row["r_bias"]),
    #                     "ax_bias": float(row["ax_bias"]),
    #                     "ay_bias": float(row["ay_bias"]),
    #                     "az_bias": float(row["az_bias"])
    #                 }
    #                 result["filter_post"].append(nav)

    timestamp = data["/sensors/pilot/timestamp"][()]
    ch0 = data["/sensors/pilot/channel[0]"][()]
    ch1 = data["/sensors/pilot/channel[1]"][()]
    ch2 = data["/sensors/pilot/channel[2]"][()]
    ch3 = data["/sensors/pilot/channel[3]"][()]
    ch4 = data["/sensors/pilot/channel[4]"][()]
    ch5 = data["/sensors/pilot/channel[5]"][()]
    ch6 = data["/sensors/pilot/channel[6]"][()]
    ch7 = data["/sensors/pilot/channel[7]"][()]
    result["pilot"] = []
    for i in range(len(timestamp)):
        pilot = {
            "time": timestamp[i],
            "auto_manual": ch0[i],
            "throttle_safety": ch1[i],
            "throttle": ch2[i],
            "aileron": ch3[i],
            "elevator": ch4[i],
            "rudder": ch5[i],
            "flaps": ch6[i],
            "aux1": ch7[i],
            "gear": 0
        }
        result["pilot"].append(pilot)

    timestamp = data["/actuators/act/timestamp"][()]
    ail = data["/actuators/act/aileron_norm"][()]
    elev = data["/actuators/act/elevator_norm"][()]
    thr = data["/actuators/act/throttle_norm"][()]
    rud = data["/actuators/act/rudder_norm"][()]
    gear = data["/actuators/act/channel5_norm"][()]
    flaps = data["/actuators/act/flaps_norm"][()]
    aux1 = data["/actuators/act/channel7_norm"][()]
    auto_manual = data["/actuators/act/channel8_norm"][()]
    result["act"] = []
    for i in range(len(timestamp)):
        act = {
            "time": timestamp[i],
            "aileron": ail[i],
            "elevator": elev[i],
            "throttle": thr[i],
            "rudder": rud[i],
            "gear": gear[i],
            "flaps": flaps[i],
            "aux1": aux1[i],
            "auto_manual": auto_manual[i]
        }
        result["act"].append(act)


    timestamp = data["/autopilot/timestamp"][()]
    master = data["/autopilot/master_switch"][()]
    pass_through = data["/autopilot/pilot_pass_through"][()]
    hdg = data["/autopilot/groundtrack_deg"][()]
    roll = data["/autopilot/roll_deg"][()]
    alt = data["/autopilot/altitude_msl_ft"][()]
    pitch = data["/autopilot/pitch_deg"][()]
    speed = data["/autopilot/airspeed_kt"][()]
    ground = data["/autopilot/altitude_ground_m"][()]
    tecs_tot = data["/autopilot/tecs_target_tot"][()]
    if "/autopilot/current_task" in data:
        current_task = data["/autopilot/current_task"][()]
    else:
        current_task = None
    if "/autopilot/task_attribute" in data:
        task_attrib = data["/autopilot/task_attribute"][()]
    else:
        task_attrib = None
    route_size = data["/autopilot/route_size"][()]
    target_waypoint_idx = data["/autopilot/target_waypoint_idx"][()]
    wpt_index = data["/autopilot/wpt_index"][()]
    wpt_latitude_deg = data["/autopilot/wpt_latitude_deg"][()]
    wpt_longitude_deg = data["/autopilot/wpt_longitude_deg"][()]
    result["ap"] = []
    for i in range(len(timestamp)):
        hdgx = math.cos(hdg[i]*d2r)
        hdgy = math.sin(hdg[i]*d2r)
        if not current_task is None:
            cur_task = current_task[i]
        else:
            cur_task = 0
        if not task_attrib is None:
            attrib = task_attrib[i]
        else:
            attrib = 0
        ap = {
            "time": timestamp[i],
            "master_switch": master[i],
            "pilot_pass_through": pass_through[i],
            "hdg": hdg[i],
            "hdgx": hdgx,
            "hdgy": hdgy,
            "roll": roll[i],
            "alt": alt[i],
            "pitch": pitch[i],
            "speed": speed[i],
            "ground": ground[i],
            "tecs_target_tot": tecs_tot[i],
            "current_task": cur_task,
            "task_attrib": attrib,
            "route_size": route_size[i],
            "target_waypoint_idx": target_waypoint_idx[i],
            "wpt_index": wpt_index[i],
            "wpt_latitude_deg": wpt_latitude_deg[i],
            "wpt_longitude_deg": wpt_longitude_deg[i]
        }
        result["ap"].append(ap)

    timestamp = data["/sensors/health/timestamp"][()]
    load_avg = data["/sensors/health/system_load_avg"][()]
    avionics_vcc = data["/sensors/health/avionics_vcc"][()]
    main_vcc = data["/sensors/health/main_vcc"][()]
    cell_vcc = data["/sensors/health/cell_vcc"][()]
    main_amps = data["/sensors/health/main_amps"][()]
    total_mah = data["/sensors/health/total_mah"][()]
    result["health"] = []
    for i in range(len(timestamp)):
        health = {
            "time": timestamp[i],
            "load_avg": load_avg[i],
            "avionics_vcc": avionics_vcc[i],
            "main_vcc": main_vcc[i],
            "cell_vcc": cell_vcc[i],
            "main_amps": main_amps[i],
            "total_mah": total_mah[i]
        }
        result["health"].append(health)

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
