from flask import Flask, send_from_directory, render_template
from SNAPobs import snap_control
from SNAPobs import snap_config
import numpy as np
import requests
import time
import pandas as pd
from ATATools.device_lock import set_device_lock, release_device_lock
#from ATATools.device_lock import release_device_lock

import json
import os
import datetime
import redis

from procutils import gen_antlo_img



# -- EXPERIMENTAL 

'''
REDISHOST = 'redishost'
REDIS = redis.Redis(REDISHOST)
SLEEP_TIME = 0.1
NSEC = 15.0
MAX_NTRIES = int(NSEC / SLEEP_TIME)
DEFAULT_EXPIRE = 10

LOCK_ON = b'1'

class LockError(Exception):
    pass

def set_device_lock(device_hostname,expire=DEFAULT_EXPIRE):
    lockname = device_hostname+"_lock"

    while True:
        set_result = REDIS.set(lockname, LOCK_ON, ex = expire, nx = True)
        if set_result:
            return 1
        else:
            time.sleep(SLEEP_TIME)

    
    lock = REDIS.get(lockname)
    ntries = 0
    if lock == LOCK_ON:
        # make sure we can obtain lock
        while lock == LOCK_ON:
            time.sleep(SLEEP_TIME)
            lock = REDIS.get(lockname)
            #ntries += 1
            #print("Trying to read", lockname)
            #if ntries > MAX_NTRIES:
            #    raise LockError("Lock for device '%s' couldn't be obtained "
            #            "after %i tries" %(device_hostname, ntries))

        # now set lock
        if resp = REDIS.set(lockname, LOCK_ON, ex=expire)
        if resp:
            return 1
        else:
            raise LockError("Could not set lock %s"
                    %lockname)
    else:
        resp = REDIS.set(lockname, LOCK_ON, ex=expire)
        if resp:
            return 1
        else:
            raise LockError("Could not set lock %s (was initially unset)"
                    %lockname)

'''
# --

snap_tab = snap_config.get_ata_snap_tab()
snap_tab = snap_tab[snap_tab['snap_hostname'].str.contains("rfsoc")]
snap_tab['board'] = snap_tab['snap_hostname'].apply(lambda el : el.split("-")[0])
snap_tab['board_defaults'] = snap_tab['board'].apply(lambda el : el + "-ctrl-1")

snap_tab = snap_tab.reset_index()

rfsoc_hostnames = list(snap_tab['snap_hostname'])
rfsoc_boards_defaults = list(snap_tab['board_defaults'].unique())
rfsoc_devices = snap_control.init_snaps(rfsoc_boards_defaults, load_system_information = True)

ANTLO_COMBOS = []

for i in range(40):
    item = snap_tab.iloc[i - 1]
    antlo = item['ANT_name'] + item['LO'].upper()
    ANTLO_COMBOS.append(antlo)

app = Flask(__name__,
        static_url_path='', 
        static_folder='public',
        template_folder='public/templates')

# CONFIG PARAMS
dir_public = 'public'
dir_data = 'data'

adc_fname = "adc.txt"
spec_fname = "spec.txt"


# seconds
DATA_TTL = 120

def get_adc_path(datadir):
    return os.path.join(datadir, adc_fname)

def get_spec_path(datadir):
    return os.path.join(datadir, spec_fname)

def get_rfsoc_data_path(rfsoc):
    return os.path.join(dir_public, dir_data, rfsoc)

def read_rfsoc_board(n):
    device_name = rfsoc_hostnames[n]
    lock_name = device_name.split("-")[0]

    print(lock_name)

    #the last digit of the board
    board_num = int(lock_name.replace("rfsoc", ""))
    print("using tcp connection to", board_num)
    pipeline_id = int(device_name.split("-")[-1]) - 1
    
    set_device_lock(lock_name)
    rfsoc_device = rfsoc_devices[board_num - 1]#snap_control.init_snaps([device_name], load_system_information = True)[0]
    
    rfsoc_device.pipeline_id = pipeline_id
    rfsoc_device.spec_set_pipeline_id()

    x_adc, y_adc = rfsoc_device.adc_get_samples()
    xx, yy = rfsoc_device.spec_read(normalize = True)
   
    release_device_lock(lock_name)
    #snap_control.disconnect_snaps([device_name])

    return x_adc, y_adc, 10 * np.log10(xx), 10 * np.log10(yy)

def write_rfsoc_data(x_adc, y_adc, xx, yy, path):
    t = datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
    adc_data = np.array([x_adc, y_adc])
    spec_data = np.array([xx, yy])
    
    adc_path = get_adc_path(path)
    spec_path = get_spec_path(path)

    np.savetxt(adc_path, adc_data, fmt = '%.3f')
    np.savetxt(spec_path, spec_data, fmt = '%.3f')

def read_rfsoc_data(path):
    adc_path = os.path.join(path, adc_fname)
    spec_path = os.path.join(path, spec_fname)

    adc_data = np.loadtxt(adc_path)
    spec_data = np.loadtxt(adc_path)

    return adc_data[0], adc_data[1], spec_data[0], spec_data[1]

def proc_rfsoc_data(n):
    rfsoc_hostname = rfsoc_hostnames[n]
    datadir = get_rfsoc_data_path(rfsoc_hostname)
    
    if os.path.exists(datadir):
        modify_time = os.path.getmtime(get_adc_path(datadir))
        print(modify_time, time.time())
        if time.time() - modify_time > 180:
            x_adc, y_adc, xx, yy = read_rfsoc_board(n)
            write_rfsoc_data(x_adc, y_adc, xx, yy, datadir)
            gen_antlo_img(x_adc, y_adc, xx, yy, n)
        else:
            x_adc, y_adc, xx, yy = read_rfsoc_data(datadir)
    else:
        os.mkdir(datadir)
        x_adc, y_adc, xx, yy = read_rfsoc_board(n)
        write_rfsoc_data(x_adc, y_adc, xx, yy, datadir)
        gen_antlo_img(x_adc, y_adc, xx, yy, n)

    xx = np.array(xx)
    yy = np.array(yy)
    x_adc = np.array(x_adc)
    y_adc = np.array(y_adc)

    print(rfsoc_hostname, x_adc.shape, y_adc.shape, xx.shape, yy.shape)

    data_dict = {
            'x_adc' : x_adc.tolist(),
            'y_adc' : y_adc.tolist(),
            'x_spec' : xx.tolist(),
            'y_spec' : yy.tolist()
            }

    return json.dumps(data_dict)

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/<int:pagenum>')
def page(pagenum):
    return render_template('main.html')

@app.route('/antlo/<int:n>')
def antlo(n):
    item = snap_tab.iloc[n]
    antlo = item['ANT_name'] + item['LO'].upper()
    return antlo

@app.route('/totalantennae')
def total():
    return str(len(rfsoc_hostnames))

@app.route('/public/<path:path>')
def send_report(path):
    return send_from_directory('reports', path)

@app.route('/procreq/<string:n>')
def handle_procreq(n):
    ind = int(n)
    data = proc_rfsoc_data(ind)
    #print(data)
    return "DONE"

app.run(host = '0.0.0.0', port = 8081, debug = True)
