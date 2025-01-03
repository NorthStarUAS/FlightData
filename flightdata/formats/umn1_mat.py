# load umn .mat file data format

# MAT_FILENAME = "thor_flight75_WaypointTracker_150squareWaypointNew_2012_10_10.mat"\

FLAG_UNBIASED_IMU = False             # Choose if accel/gyro should be bias-free.

import math
import os, sys
join = os.path.join
import numpy as np
from scipy import io as sio

mps2kt = 1.94384

class dict2struct(): pass

def load(mat_filename):
    # Name of .mat file that exists in the directory defined above and
    # has the flight_data and flight_info structures
    filepath = mat_filename

    # Load Flight Data: ## IMPORTANT to have the .mat file in the
    # flight_data and flight_info structures for this function ##
    data = sio.loadmat(filepath, struct_as_record=False, squeeze_me=True)
    print("Loaded Data Summary")
    print("* File: %s" % filepath.split(os.path.sep)[-1])
    try:
        flight_data, flight_info = data["flight_data"], data["flight_info"]
        print("* Date: %s" % flight_info.date)
        print("* Aircraft: %s" % flight_info.aircraft)
    except KeyError:
        print("KeyError")
        # Convert from Python dictionary to struct-like before
        flight_data = dict2struct()
        for k in data:
            exec("flight_data.%s = data['%s']" % (k, k))
    del(data)

    # Add both names for pitch: the and theta
    try:
        flight_data.theta = flight_data.the
    except AttributeError:
        pass

    # Fill in time data
    t = flight_data.time
    print("t:", t)

    # Magnetometer data - not used hence don't trust
    hm  = np.vstack((flight_data.hx, -flight_data.hy, -flight_data.hz)).T

    # Geri mag calibration
    mag_affine = np.array(
        [[ 4.3374191736,  0.9527668819,  0.2106929615,  0.0649324241],
         [-3.7617930866,  6.2839014058, -3.5707398622,  2.1616165305],
         [-0.8688354599,  0.2205650877,  4.7466115481, -2.7041600008],
         [ 0.          ,  0.          ,  0.          ,  1.          ]]
    )

    # Populate IMU Data
    imu = np.vstack((t, flight_data.p, flight_data.q, flight_data.r,
                     flight_data.ax, flight_data.ay, flight_data.az,
                     hm[:,0], hm[:,1], hm[:,2])).T

    # Note that accelerometer and gyro measurements logged by UAV
    # after 11/17/2011 flight (seemingly, see
    # http://trac.umnaem.webfactional.com/wiki/FlightReports/2011_11_17)
    # have the nav-estimated bias removed before datalogging. So to work with raw
    # imu-data, we add back the on-board estimated biases.
    if not FLAG_UNBIASED_IMU:
        try:
            imu[:, 1:4] += np.vstack((flight_data.p_bias,
                                      flight_data.q_bias,
                                      flight_data.r_bias)).T

            imu[:, 4:7] += np.vstack((flight_data.ax_bias,
                                      flight_data.ay_bias,
                                      flight_data.az_bias)).T
        except AttributeError:
            print("Note: On board estimated bias not found.")

    # Air Data
    ias = flight_data.ias # indicated airspeed (m/s)
    h = flight_data.h

    # Populate GPS sensor data
    try:
        vn = flight_data.gps_vn
    except:
        vn = flight_data.vn
    try:
        ve = flight_data.gps_ve
    except:
        ve = flight_data.ve
    try:
        vd = flight_data.gps_vd
    except:
        vd = flight_data.vd
    lat = flight_data.lat
    lon = flight_data.lon
    alt = flight_data.alt

    # kstart set to when the navigation filter used onboard the aircraft
    # was initialized and this is accomplished by detecting when navlat is
    # no longer 0.0. This choice of kstart will ensure the filter being
    # tested is using the same initialization time step as the onboard
    # filter allowing for apples to apples comparisons.
    kstart = (abs(flight_data.navlat) > 0.0).tolist().index(True)
    k = kstart
    print("Initialized at Time: %.2f s (k=%i)" % (t[k], k))

    # Set previous value of GPS altitude to 0.0. This will be used to
    # trigger GPS newData flag which is commonly used in our
    # navigation filters for deciding if the GPS data has been
    # updated. However, in python we have no log of newData
    # (typically). So a comparison of current GPS altitude to the
    # previous epoch's GPS altitude is used to determine if GPS has
    # been updated.
    last_gps_alt = -9999.9

    # create data structures for ekf processing
    result = {}
    result["imu"] = []
    result["gps"] = []
    result["airdata"] = []
    result["nav"] = []

    k = kstart
    while k < len(t):
        p, q, r = imu[k, 1:4]
        ax, ay, az = imu[k, 4:7]
        hx, hy, hz = imu[k, 7:10]

        s = [hx, hy, hz, 1.0]
        #hf = np.dot(mag_affine, s)
        hf = s

        imu_pt = {
            "timestamp": float(t[k]),
            "p_rps": float(p),
            "q_rps": float(q),
            "r_rps": float(r),
            "ax_mps2": float(ax),
            "ay_mps2": float(ay),
            "az_mps2": float(az),
            #"hx": hx,
            #"hy": hy,
            #"hz": hz,
            "hx": float(hf[0]),
            "hy": float(hf[1]),
            "hz": float(hf[2]),
            "temp_C": 15.0
        }
        result["imu"].append(imu_pt)

        if abs(alt[k] - last_gps_alt) > 0.0001:
            last_gps_alt = alt[k]
            gps_pt = {
                "timestamp": float(t[k]),
                #"status": int(status),
                "unix_sec": float(t[k]),
                "lat_deg": float(lat[k]),
                "lon_deg": float(lon[k]),
                "alt_m": float(alt[k]),
                "vn_mps": float(vn[k]),
                "ve_mps": float(ve[k]),
                "vd_mps": float(vd[k]),
                "sats": 8     # force a reasonable value (not logged)
            }
            result["gps"].append(gps_pt)

        air_pt = {
            "timestamp": float(t[k]),
            "airspeed": float(flight_data.ias[k]*mps2kt),
            "altitude": float(flight_data.h[k]),
            "alt_true": float(flight_data.navalt[k])
        }
        result["airdata"].append(air_pt)

        nav = {
            "timestamp": float(t[k]),
            "lat_rad": float(flight_data.navlat[k]),
            "lon_rad": float(flight_data.navlon[k]),
            "alt_m": float(flight_data.navalt[k]),
            "vn_mps": float(flight_data.navvn[k]),
            "ve_mps": float(flight_data.navve[k]),
            "vd_mps": float(flight_data.navvd[k]),
            "phi_rad": float(flight_data.phi[k]),
            "the_rad": float(flight_data.theta[k]),
            "psi_rad": float(flight_data.psi[k]),
            "p_bias": float(flight_data.p_bias[k]),
            "q_bias": float(flight_data.q_bias[k]),
            "r_bias": float(flight_data.r_bias[k]),
            "ax_bias": float(flight_data.ax_bias[k]),
            "ay_bias": float(flight_data.ay_bias[k]),
            "az_bias": float(flight_data.az_bias[k])
        }
        result["nav"].append(nav)

        k += 1

    dir = os.path.dirname(mat_filename)
    print("dir:", dir)

    filename = os.path.join(dir, "imu-0.txt")
    f = open(filename, "w")
    for imupt in result["imu"]:
        line = [ "%.5f" % imupt["timestamp"], "%.4f" % imupt["p_rps"], "%.4f" % imupt["q_rps"], "%.4f" % imupt["r_rps"], "%.4f" % imupt["ax_mps2"], "%.4f" % imupt["ay_mps2"], "%.4f" % imupt["az_mps2"], "%.4f" % imupt["hx"], "%.4f" % imupt["hy"], "%.4f" % imupt["hz"], "%.4f" % imupt["temp_C"], "0" ]
        f.write(",".join(line) + "\n")

    filename = os.path.join(dir, "gps-0.txt")
    f = open(filename, "w")
    for gpspt in result["gps"]:
        line = [ "%.5f" % gpspt["timestamp"], "%.10f" % gpspt["lat_deg"], "%.10f" % gpspt["lon_deg"], "%.4f" % gpspt["alt_m"], "%.4f" % gpspt["vn_mps"], "%.4f" % gpspt["ve_mps"], "%.4f" % gpspt["vd_mps"], "%.4f" % gpspt["timestamp"], "8", "0" ]
        f.write(",".join(line) + "\n")

    filename = os.path.join(dir, "nav-0.txt")
    f = open(filename, "w")
    r2d = 180.0 / math.pi
    for filtpt in result["nav"]:
        line = [ "%.5f" % filtpt["timestamp"], "%.10f" % filtpt["lat_rad"], "%.10f" % filtpt["lon_rad"], "%.4f" % filtpt["alt_m"], "%.4f" % filtpt["vn_mps"], "%.4f" % filtpt["ve_mps"], "%.4f" % filtpt["vd_mps"], "%.4f" % (filtpt["phi_rad"]*r2d), "%.4f" % (filtpt["the_rad"]*r2d), "%.4f" % (filtpt["psi_rad"]*r2d), "0" ]
        f.write(",".join(line) + "\n")

    return result
