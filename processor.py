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
ADC_MAX_DEV = IDEAL_ADC_STD * 0.5

while True:

    req = requests.get("http://0.0.0.0:9000/spectrum/" + str(THIS_ANTENNA))
    data = req.text.split(":")
    SPECTRA = [[float(el) for el in data[0].split("_")], [float(el) for el in data[1].split("_")]]

    SPECTRA = np.array(SPECTRA)

    req = requests.get("http://0.0.0.0:9000/adcsnapshot/" + str(THIS_ANTENNA))
    data = req.text.split("|")[1].split(":")
    ADC_SAMPLES = [[float(el) for el in data[0].split("_")], [float(el) for el in data[1].split("_")]]

    adc_std = [np.std(ADC_SAMPLES[0]), np.std(ADC_SAMPLES[1])]


    ax[0].plot(SPECTRA[0], color = 'blue', label = 'X-pol')
    ax[0].plot(SPECTRA[1], color = 'red', label = 'Y-pol')
    ax[0].set_title("Simulated Ant-Tun " + str(THIS_ANTENNA))
    #ax[0].set_xlabel("Channel")
    #ax[0].set_ylabel("Power (dB)")
    ax[0].grid()
    ax[0].legend(loc = 'upper right')


    ax[1].set_title("ADC Values")#, X = " + str(round(adc_std[0], 2)) + ", Y = " + str(round(adc_std[1], 2)))
    #ax[1].set_ylabel("Counts")
    ax[1].hist(ADC_SAMPLES[0], 50, color = 'blue', rwidth = 0.5)#, label = "X = " + str(round(adc_std[0], 2)))
    ax[1].hist(ADC_SAMPLES[1], 50, color = 'red', rwidth = 0.5)#, label = "Y = " + str(round(adc_std[1], 2)))
    ax[1].set_xlim([-HALFRANGE, HALFRANGE])
    #cur_ylim = ax[1].get_ylim()
    #ax[1].set_ylim([cur_ylim[0], int(cur_ylim[1] * 1.4)])
    ax[1].grid()
    #ax[1].legend(loc = 'upper right')

    imgdir = "public/images/"

    imgname = "anttun" + str(THIS_ANTENNA) + ".png"
    tempimgname = "t_anttun" + str(THIS_ANTENNA) + ".png"

    plt.savefig(imgdir + tempimgname, bbox_inches = "tight", dpi = 250.0)

    #img = cv2.imread(imgdir + tempimgname)

    img = PIL.Image.open(imgdir + tempimgname)

    shape = list(np.array(img).shape)
    shape[0] = int(shape[0] / 4)

    textrect = np.ones(shape, dtype = np.array(img).dtype) * 255
    newimg = np.concatenate((np.array(img), textrect), axis = 0)
    img = PIL.Image.fromarray(newimg, mode = "RGBA")
    #img.save(imgdir + imgname)
    #time.sleep(5)

    #cv2.putText(img, "X:" + str(round(adc_std[0])) + " Y:" + str(round(adc_std[1])),
	#	(int(img.shape[1] * 0.3), int(img.shape[0] * 0.95)),
	#	cv2.FONT_HERSHEY_SIMPLEX,
	#	7,
	#	(0, 0, 0),
	#	15,
	#	2
	#	)


    shape = list(np.array(img).shape)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(CONFIG_FONT, 230)
    draw.text( (int(shape[1] * 0.48), int(shape[0] * 0.8)), "σX:" + str(round(adc_std[0])) + "   σY:" + str(round(adc_std[1])), font = font, fill = (0, 0, 0) )

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

    colorrect[ystart : yend, xstart : xend0, 0] = R_VAL_0
    colorrect[ystart : yend, xstart : xend0, 1] = G_VAL_0
    colorrect[ystart : yend, xstart : xend0, 2] = B_VAL_0

    colorrect[ystart : yend, xend0 : xend1, 0] = R_VAL_1
    colorrect[ystart : yend, xend0 : xend1, 1] = G_VAL_1
    colorrect[ystart : yend, xend0 : xend1, 2] = B_VAL_1

    newimg = np.concatenate((np.array(img), colorrect), axis = 1)
    img = PIL.Image.fromarray(newimg, mode = "RGBA")
    #img.save(imgdir + imgname)
    #time.sleep(5)

    #cv2.imwrite(imgdir + imgname, np.array(img))
    img.save(imgdir + imgname)

    np.savetxt("public/data/std_anttun_" + str(THIS_ANTENNA) + ".txt", np.array(adc_std), fmt = "%f")
    f = open("public/colordata/anttun_" + str(THIS_ANTENNA) + ".txt", "w")
    f.write(str(R_VAL_0) + "," + str(G_VAL_0) + "," + str(B_VAL_0))
    f.write("," + str(R_VAL_1) + "," + str(G_VAL_1) + "," + str(B_VAL_1))
    f.close()

    ax[0].cla()
    ax[1].cla()

    time.sleep(10)
