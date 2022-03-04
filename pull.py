from SNAPobs import snap_control
import numpy as np
import requests

rfsoc_hostnames = ['rfsoc1-ctrl-1']
rfsocs = snap_control.init_snaps(rfsoc_hostnames, load_system_information=True)

# get spectrum for first RFSoC pipeline:
xx,yy = rfsocs[0].spec_read(normalize = True)


# get ADC values for first RFSoC pipeline
x_adc, y_adc = rfsocs[0].adc_get_samples()
x_adc = np.array(x_adc)
y_adc = np.array(y_adc)

#print(np.amax(xx), np.amin(xx))

SPEC_PREC = 15
#print(x_adc.shape, y_adc.shape, xx.shape, yy.shape)
fullspec = '_'.join([str(round(el, SPEC_PREC)) for el in xx]) + ":" + "_".join([str(round(el, SPEC_PREC)) for el in yy])
#print(fullspec[:100], xx[:3])
req = requests.get("https://10.10.1.31:9000/updatespec/1?data=" + fullspec[:100])
req.send()

