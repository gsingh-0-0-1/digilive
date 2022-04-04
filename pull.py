from SNAPobs import snap_control
from SNAPobs import snap_config
import numpy as np
import requests
import time
import pandas as pd

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
        xx,yy = rfsocs[ind].spec_read(normalize = True)


        # get ADC values for first RFSoC pipeline
        x_adc, y_adc = rfsocs[ind].adc_get_samples()
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
            requests.post("http://10.10.1.31:9000/updatespec/" + str(ind + 1), data = specdata)
            requests.post("http://10.10.1.31:9000/updateadc/" + str(ind + 1), data = adcdata)
            print("Pulled " + str(ind) + ": " + rfsoc_hostnames[ind])
        except Exception as e:
            pass
    requests.get("http://10.10.1.31:9000/setminmax/" + str(min(mins)) + "/" + str(max(maxs)))
    time.sleep(10)
