import csv
import h5py
import math

d2r = math.pi / 180.0

def subload(data, branch, name):
    path = branch + "/" + name
    print("subload:", path)

    subtree = data[path]
    fields = subtree.keys()
    subdata = {}
    for f in fields:
        subdata[f] = subtree[f][()]
    count = len(subdata[f])  # depend on f still containing the last value of the loop
    result = []
    for i in range(count):
        record = {}
        for f in fields:
            record[f] = subdata[f][i]
        if "millis" in record:
            record["timestamp"] = record["millis"] / 1000.0
        result.append(record)
    print("  %s: %d records." % (name, len(result)))
    return result

def load(h5_filename):
    # open the hdf5 file
    data = h5py.File(h5_filename, "r")

    result = {}

    subdata = subload(data, "", "events")
    result["events"] = subdata

    subdata = subload(data, "/sensors", "imu")
    result["imu"] = subdata

    subdata = subload(data, "/sensors", "gps")
    for i in range(len(subdata)):
        record = subdata[i]
        record["unix_sec"] = record["unix_usec"] / 1000000.0
        record["latitude_deg"] = record["latitude_raw"] / 10000000.0
        record["longitude_deg"] = record["longitude_raw"] / 10000000.0
    result["gps"] = subdata

    subdata = subload(data, "/sensors", "airdata")
    result["airdata"] = subdata

    subdata = subload(data, "/filters", "env")
    for i in range(len(subdata)):
        record = subdata[i]
        record["flight_timer_sec"] = record["flight_timer_millis"] / 1000.0
    result["env"] = subdata

    subdata = subload(data, "/filters", "nav")
    for i in range(len(subdata)):
        record = subdata[i]
        record["latitude_deg"] = record["latitude_raw"] / 10000000.0
        record["longitude_deg"] = record["longitude_raw"] / 10000000.0
        psi = record["yaw_deg"]*d2r
        if psi > math.pi:
            psi -= 2*math.pi
        if psi < -math.pi:
            psi += 2*math.pi
        record["psix"] = math.cos(psi)
        record["psiy"] = math.sin(psi)
    # filter only 'legit' nav solution
    result["nav"] = []
    for i in range(len(subdata)):
        record = subdata[i]
        if record["status"] >= 2:
            result["nav"].append(record)

    subdata = subload(data, "/filters", "nav_metrics")
    for i in range(len(subdata)):
        record = subdata[i]
        record["timestamp"] = record["metrics_millis"] / 1000.0
    result["nav_metrics"] = subdata

    subdata = subload(data, "/sensors", "inceptors")
    result["inceptors"] = subdata

    subdata = subload(data, "/fcs", "outputs")
    result["fcs_outputs"] = subdata

    subdata = subload(data, "/fcs", "effectors")
    for i in range(len(subdata)):
        record = subdata[i]
        record["throttle"] = record["channel"][0]
        record["aileron"] = record["channel"][1]
        record["elevator"] = record["channel"][2]
        record["rudder"] = record["channel"][3]
        record["flaps"] = record["channel"][4]
        record["gear"] = record["channel"][5]
        record["aux1"] = record["channel"][6]
        record["aux2"] = record["channel"][7]
    result["effectors"] = subdata

    subdata = subload(data, "/fcs", "refs")
    for i in range(len(subdata)):
        record = subdata[i]
        psi = record["groundtrack_deg"]*d2r
        if psi > math.pi:
            psi -= 2*math.pi
        if psi < -math.pi:
            psi += 2*math.pi
        record["groundtrack_x"] = math.cos(psi)
        record["groundtrack_y"] = math.sin(psi)
    result["fcs_refs"] = subdata

    subdata = subload(data, "", "mission")
    for i in range(len(subdata)):
        record = subdata[i]
        record["wpt_latitude_deg"] = record["wpt_latitude_raw"] / 10000000.0
        record["wpt_longitude_deg"] = record["wpt_longitude_raw"] / 10000000.0
    result["mission"] = subdata

    subdata = subload(data, "/sensors", "power")
    result["power"] = subdata

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
