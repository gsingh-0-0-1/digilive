import numpy as np
import matplotlib.pyplot as plt
import requests
import time

N_ANTENNAE = 40

print(time.time())

for i in range(1):
	SPECTRA = []
	ADC_SAMPLES = []

	for i in range(N_ANTENNAE):
		req = requests.get("http://0.0.0.0:9000/spectrum/" + str(i))
		data = req.text.split(":")
		SPECTRA.append([[float(el) for el in data[0].split("_")], [float(el) for el in data[1].split("_")]])

	SPECTRA = np.array(SPECTRA)

	for i in range(N_ANTENNAE):
		req = requests.get("http://0.0.0.0:9000/adcsnapshot/" + str(i))
		data = req.text.split(":")
		ADC_SAMPLES.append([[float(el) for el in data[0].split("_")], [float(el) for el in data[1].split("_")]])

	fig, ax = plt.subplots(1, 2, 
					gridspec_kw={
	                   'width_ratios': [3.5, 1]
	                   },
	                figsize = (17, 5))

	spec1, = ax[0].plot([1], color = 'blue', label = 'X-pol')
	spec2, = ax[0].plot([1], color = 'red', label = 'Y-pol')

	ax[0].set_xlabel("Channel")
	ax[0].set_ylabel("Power (dB)")
	ax[0].legend()


	for i in range(SPECTRA.shape[0]):

		spec1.set_data(np.arange(0, SPECTRA.shape[-1], 1), SPECTRA[i][0])
		spec2.set_data(np.arange(0, SPECTRA.shape[-1], 1), SPECTRA[i][1])
		ax[0].set_title("Simulated Ant-Tun " + str(i))
		ax[0].relim()
		ax[0].autoscale_view(True,True,True) 

		ax[1].set_xlabel("ADC Values")
		ax[1].set_ylabel("Counts")
		ax[1].hist(ADC_SAMPLES[i][0], 50, color = 'blue', rwidth = 0.5)
		ax[1].hist(ADC_SAMPLES[i][1], 50, color = 'red', rwidth = 0.5)

		plt.savefig("ant" + str(i) + ".png")

		ax[1].cla()

	plt.clf()

print(time.time())
