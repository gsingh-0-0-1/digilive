import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import requests
import time
import sys
import cv2
import PIL
from PIL import ImageDraw
from PIL import ImageFont
from ATATools import ata_control
from SNAPobs import snap_defaults
from SNAPobs import snap_control
from SNAPobs import snap_config

configfile = open("config.txt", "r")
configdata = configfile.read().split("\n")
configfile.close()

CONFIG_FONT = configdata[0]

matplotlib.use('agg')

matplotlib.rcParams.update({'font.size' : 27})
#matplotlib.rcParams.update({'axes.titlesize' : 30})


THIS_ANTENNA = int(sys.argv[1])

fig, ax = plt.subplots(1, 2, 
				gridspec_kw={
                   'width_ratios': [2, 1]
                   },
                figsize = (17, 4.5))

HALFRANGE = 2 ** 13
IDEAL_ADC_STD = HALFRANGE / 8
ADC_MAX_DEV = 240#IDEAL_ADC_STD * 0.5

NUM_OLD_BOARDS = 12

PORT = '9000'

snap_tab = snap_config.get_ata_snap_tab()
#rfsoc_hostnames = [el for el in list(snap_tab['snap_hostname']) if 'frb' not in el][THIS_ANTENNA]
#rfsocs = snap_control.init_snaps([rfsoc_hostnames], load_system_information=True)

antlo = snap_tab["ANT_name"][THIS_ANTENNA + NUM_OLD_BOARDS - 1] + snap_tab["LO"][THIS_ANTENNA + NUM_OLD_BOARDS - 1].upper()
requests.get("http://10.10.1.31:" + PORT + "/antlo_update/" + str(THIS_ANTENNA) + "/" + antlo)
#exec(open("/home/sonata/utils/rcparams.py", "r").read())

print(antlo)

while True:
    try:
        centerfreq = ata_control.get_sky_freq(lo = snap_tab["LO"][THIS_ANTENNA + NUM_OLD_BOARDS])
        break
    except Exception as e:
        #logging.error(traceback.format_exc())
        print("Encountered "  + str(e) + ", retrying in 30 sec...")
        time.sleep(5)

BW_EFF = 672

BW = snap_defaults.bw
NCHANS = 2048
FOFF = BW / NCHANS

WAIT_TIME = 20

plt.rcParams["font.family"] = "Times New Roman"
#plt.rcParams["font.size"] = 15
while True:

    #xx,yy = rfsocs[0].spec_read(normalize = True)

    #x_adc, y_adc = rfsocs[0].adc_get_samples()
    #x_adc = np.array(x_adc)
    #y_adc = np.array(y_adc)

    skip = False

    try:
        req = requests.get("http://10.10.1.31:" + PORT + "/spectrum/" + str(THIS_ANTENNA))
        req2 = requests.get("http://10.10.1.31:" + PORT + "/adcsnapshot/" + str(THIS_ANTENNA))
    except Exception as e:
        skip = True

    if req.text == "No data" or req2.text == "No data":
        skip = True

    try:
        data_spec = req.text.split("|")[1].split(":")
        data_adc = req2.text.split("|")[1].split(":")
    except IndexError:
        skip = True


    if skip:
        print("Skipping " + str(THIS_ANTENNA) + "...")
        time.sleep(WAIT_TIME)
        continue


    date = req.text.split("|")[0]
    SPECTRA = [[float(el) for el in data_spec[0].split("_")], [float(el) for el in data_spec[1].split("_")]]
    SPECTRA = np.array(SPECTRA)
    SPEC_PREC = 15
    SPEC_MIN, SPEC_MAX = tuple([float(el) for el in requests.get("http://10.10.1.31:" + PORT + "/getminmax").text.split("_")])
    SPEC_MIN -= 3
    SPEC_MAX += 3

    ADC_SAMPLES = [[float(el) for el in data_adc[0].split("_")], [float(el) for el in data_adc[1].split("_")]]
    ADC_SAMPLES = np.array(ADC_SAMPLES)


    adc_std = [np.std(ADC_SAMPLES[0]), np.std(ADC_SAMPLES[1])]

    freqs = np.arange(centerfreq - BW / 2, centerfreq + BW / 2, FOFF)
    requests.get("http://10.10.1.31:" + PORT + "/setfreqdata/" + str(THIS_ANTENNA) + "/" + str(freqs[0]) + "/" + str(freqs[-1]) + "/" + str(FOFF) )

    ax[0].plot(freqs, 10 * np.log10(SPECTRA[0]), color = 'blue')#, label = 'X-pol')
    ax[0].plot(freqs, 10 * np.log10(SPECTRA[1]), color = 'red')#, label = 'Y-pol')
    ax[0].axvline(centerfreq + BW_EFF/2, color = 'black', linestyle='--')
    ax[0].axvline(centerfreq - BW_EFF/2, color = 'black', linestyle='--')
    ax[0].set_ylim(SPEC_MIN, SPEC_MAX)
    ax[0].set_title("ANT-LO " + antlo)# + ", " + date)
    ax[0].set_xlabel(r"$??_\mathrm{X}$:" + str(round(adc_std[0])), fontsize = 80)
    ax[0].xaxis.label.set_color('blue')
    #ax[0].set_xlabel("Channel")
    #ax[0].set_ylabel("Power (dB)")
    ax[0].grid()
    #ax[0].legend(loc = 'upper right')


    ax[1].set_title("ADC Values")#, X = " + str(round(adc_std[0], 2)) + ", Y = " + str(round(adc_std[1], 2)))
    #ax[1].set_ylabel("Counts")
    ax[1].hist(ADC_SAMPLES[0], 50, color = 'blue', rwidth = 0.5)#, label = "X = " + str(round(adc_std[0], 2)))
    ax[1].hist(ADC_SAMPLES[1], 50, color = 'red', rwidth = 0.5)#, label = "Y = " + str(round(adc_std[1], 2)))
    ax[1].set_xlim([-HALFRANGE, HALFRANGE])
    ax[1].set_xlabel(r"$??_\mathrm{Y}$:" + str(round(adc_std[1])), fontsize = 80)
    ax[1].xaxis.label.set_color('red')
    #cur_ylim = ax[1].get_ylim()
    #ax[1].set_ylim([cur_ylim[0], int(cur_ylim[1] * 1.4)])
    ax[1].grid()
    #ax[1].legend(loc = 'upper right')

    imgdir = "public/images/"

    imgname = "anttun" + str(THIS_ANTENNA) + ".png"
    tempimgname = "t_anttun" + str(THIS_ANTENNA) + ".png"

    plt.savefig(imgdir + tempimgname, bbox_inches = "tight", dpi = 75.0)

    img = cv2.imread(imgdir + tempimgname)



    shape = list(np.array(img).shape)
    #draw = ImageDraw.Draw(img)
    #font = ImageFont.truetype(CONFIG_FONT, 230)
    #draw.text( (int(shape[1] * 0.4), int(shape[0] * 0.8)), "??X:" + str(round(adc_std[0])) + "   ??Y:" + str(round(adc_std[1])), font = font, fill = (0, 0, 0) )

    shape[1] = int(shape[1] / 20)
    colorrect = np.ones(shape, dtype = np.array(img).dtype) * 255

    #indices of the rectange we want to color in
    ystart = 0
    yend = shape[0]

    #two different rectangles, one for each polarization
    xstart = int(2.5 * shape[1] / 10)
    xend0 = int(5 * shape[1] / 10)
    xend1 = int(7.5 * shape[1] / 10)

    deviation_0 = abs(adc_std[0] - IDEAL_ADC_STD)
    deviation_1 = abs(adc_std[1] - IDEAL_ADC_STD)

    #we have no use for deviation fractions greater than 1 - we can cap them there
    dev_frac_0 = min(deviation_0 / ADC_MAX_DEV, 1)
    dev_frac_1 = min(deviation_1 / ADC_MAX_DEV, 1)

    #start out at green
    B_VAL_0 = 0
    B_VAL_1 = 0

    G_VAL_0 = 255
    G_VAL_1 = 255

    R_VAL_0 = 0
    R_VAL_1 = 0

    #work our way towards red based on the deviation
    #if the deviation fraction is 0.5, we should saturate the red, which will create a yellow color
    R_VAL_0 += min(1, 2 * dev_frac_0) * 255
    R_VAL_1 += min(1, 2 * dev_frac_1) * 255

    if dev_frac_0 > 0.5:
        G_VAL_0 -= min(1, 2 * (dev_frac_0 - 0.5)) * 255

    if dev_frac_1 > 0.5:
        G_VAL_1 -= min(1, 2 * (dev_frac_1 - 0.5)) * 255


    B_VAL_0 = int(B_VAL_0)
    B_VAL_1 = int(B_VAL_1)
    G_VAL_0 = int(G_VAL_0)
    G_VAL_1 = int(G_VAL_1)
    R_VAL_0 = int(R_VAL_0)
    R_VAL_1 = int(R_VAL_1)

    colorrect[ystart : yend, xstart : xend0, 0] = B_VAL_0
    colorrect[ystart : yend, xstart : xend0, 1] = G_VAL_0
    colorrect[ystart : yend, xstart : xend0, 2] = R_VAL_0

    colorrect[ystart : yend, xend0 : xend1, 0] = B_VAL_1
    colorrect[ystart : yend, xend0 : xend1, 1] = G_VAL_1
    colorrect[ystart : yend, xend0 : xend1, 2] = R_VAL_1

    newimg = np.concatenate((np.array(img), colorrect), axis = 1)
    #img = PIL.Image.fromarray(newimg, mode = "RGBA")
    #img.save(imgdir + imgname)
    #time.sleep(5)

    #cv2.imwrite(imgdir + imgname, cv2.cvtColor(np.array(newimg), cv2.COLOR_BGR2RGB))
    cv2.imwrite(imgdir + imgname, np.array(newimg))
    #img.save(imgdir + imgname)

    if int(THIS_ANTENNA) == 20:
        requests.get("http://10.10.1.31:" + PORT + "/updatetime/" + date)

    np.savetxt("./public/data/std_anttun_" + str(THIS_ANTENNA) + ".txt", np.array(adc_std), fmt = "%f")
    f = open("./public/colordata/anttun_" + str(THIS_ANTENNA) + ".txt", "w")
    f.write(str(R_VAL_0) + "," + str(G_VAL_0) + "," + str(B_VAL_0))
    f.write("," + str(R_VAL_1) + "," + str(G_VAL_1) + "," + str(B_VAL_1))
    f.close()

    ax[0].cla()
    ax[1].cla()

    time.sleep(WAIT_TIME)
