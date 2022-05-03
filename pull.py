from SNAPobs import snap_control
from SNAPobs import snap_config
import numpy as np
import requests
import time
import pandas as pd
from ATATools.device_lock import set_device_lock, release_device_lock

snap_tab = snap_config.get_ata_snap_tab()

rfsoc_hostnames = [el for el in list(snap_tab['snap_hostname']) if 'frb' not in el]
#rfsoc_hostnames = rfsoc_hostnames[:1]
rfsocs = snap_control.init_snaps(rfsoc_hostnames, load_system_information=True)

while True:
    print("----------")
    maxs = []
    mins = []

    for ind in range(len(rfsoc_hostnames)):
        # get spectrum for first RFSoC pipeline:

        # get ADC values for first RFSoC pipeline
        snap_name = rfsoc_hostnames[ind]

        if snap_name.lower().startswith('rfsoc'):
            # e.g. snap_name "rfsoc2-ctrl-3"
            # so lock_name = "rfsoc2"
            lock_name = snap_name[:6]
        else:
            lock_name = snap_name

        set_device_lock(lock_name)
        x_adc, y_adc = rfsocs[ind].adc_get_samples()
        xx,yy = rfsocs[ind].spec_read(normalize = True)
        release_device_lock(lock_name)
        x_adc = np.array(x_adc)
        y_adc = np.array(y_adc)



        #print(np.amax(xx), np.amin(xx))

        SPEC_PREC = 15
        #print(x_adc.shape, y_adc.shape, xx.shape, yy.shape)
        fullspec = '_'.join([str(round(el, SPEC_PREC)) for el in xx]) + ":" + "_".join([str(round(el, SPEC_PREC)) for el in yy])
        fulladc = '_'.join([str(round(el, SPEC_PREC)) for el in x_adc]) + ":" + '_'.join([str(round(el, SPEC_PREC)) for el in y_adc])
        specdata = {'fullspec' : fullspec}
        adcdata = {'fulladc' : fulladc}
        specmax = 10 * np.log10(max(np.amax(xx), np.amax(yy)))
        specmin = 10 * np.log10(min(np.amin(xx), np.amin(yy)))
        maxs.append(specmax)
        mins.append(specmin)
        try:
            requests.post("http://10.10.1.31:9000/updatespec/" + str(ind + 1), data = specdata, timeout = 2.50)
            requests.post("http://10.10.1.31:9000/updateadc/" + str(ind + 1), data = adcdata, timeout = 2.50)
            print("Pulled " + str(ind) + ": " + rfsoc_hostnames[ind])
        except Exception as e:
            pass
    requests.get("http://10.10.1.31:9000/setminmax/" + str(min(mins)) + "/" + str(max(maxs)), timeout = 2.50)
    time.sleep(10)
