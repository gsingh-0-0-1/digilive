const express = require('express')
var fs = require('fs');
const {URLSearchParams} = require('url')

const app = express()
const port = 9000

app.use(express.static('public'));

var SAMPLE_ADC_SNAPSHOTS = [];
var ADC_SAMPLES = 16384

var SAMPLE_SPECTRA = [];
var SPECTRA_CHANS = 4096

var ANTENNAE = 40


//utility functions
function randomnormal(mean, std){
	var u = 0, v = 0;
	while(u === 0) u = Math.random(); //Converting [0,1) to (0,1)
	while(v === 0) v = Math.random();
	var out = Math.sqrt( -2.0 * Math.log( u ) ) * Math.cos( 2.0 * Math.PI * v )
	out = std*out + mean
	return out;
}

function randomuniform(center = 0.5, scale = 1){
	let val = Math.random() - 0.5
	val = val * scale + center
	return val;
}

function bandpass_simulated({chanidx, centerchan = (SPECTRA_CHANS + 1) / 2, height = 40, min = 60, noiseamp = 1}){
	let x = chanidx - centerchan
	let baseval = height * Math.pow(Math.E, -Math.pow(x / (centerchan * 0.75), 6)) + min
	baseval = baseval + randomuniform(0, noiseamp)
	return baseval
}

//generation functions
function reGenerateADCSnapshot(){
	SAMPLE_ADC_SNAPSHOTS = []
	for (var j = 0; j < ANTENNAE; j++){
		var arr = []
		SAMPLE_ADC_SNAPSHOTS.push(arr)
		var subarr1 = []
		var subarr2 = []
		SAMPLE_ADC_SNAPSHOTS[j].push(subarr1)
		SAMPLE_ADC_SNAPSHOTS[j].push(subarr2)
		var std = (randomuniform(16, 12))
		for (var i = 0; i < ADC_SAMPLES; i++){
			for (var pol = 0; pol < 2; pol++){
				SAMPLE_ADC_SNAPSHOTS[j][pol].push(randomnormal(0, std))
			}
		}
	}
}

function reGenerateSpectra(){
	SAMPLE_SPECTRA = []
	for (var j = 0; j < ANTENNAE; j++){
		var arr = []
		SAMPLE_SPECTRA.push(arr)
		var subarr1 = []
		var subarr2 = []
		SAMPLE_SPECTRA[j].push(subarr1)
		SAMPLE_SPECTRA[j].push(subarr2)
		for (var i = 0; i < SPECTRA_CHANS; i++){
			for (var pol = 0; pol < 2; pol++){
				if (pol == 0){
					SAMPLE_SPECTRA[j][pol].push(bandpass_simulated({chanidx : i + 1, noiseamp : 1.3}))
				}
				if (pol == 1){
					SAMPLE_SPECTRA[j][pol].push(bandpass_simulated({chanidx : i + 1, noiseamp : 1.3, height: 35, min: 62.5}))
				}

				//randomly add some spikes
				if (randomuniform() > 0.999){
					let randpol = Math.round(randomuniform())
					SAMPLE_SPECTRA[j][randpol][SAMPLE_SPECTRA[j][randpol].length - 1] += randomuniform(30, 15)
				}
			}
		}
	}
}

app.get('/adcsnapshot/:id', (req, res) => {
	var id = req.params.id * 1
	var s = SAMPLE_ADC_SNAPSHOTS[id][0].join("_")
	s = s + ":"
	s = s + SAMPLE_ADC_SNAPSHOTS[id][1].join("_")
	res.send(s)
})

app.get('/spectrum/:id', (req, res) => {
	var id = req.params.id * 1
	var s = SAMPLE_SPECTRA[id][0].join("_")
	s = s + ":"
	s = s + SAMPLE_SPECTRA[id][1].join("_")
	res.send(s)
})


app.get("/", (req, res) => {
	res.sendFile("public/templates/main.html", {root: __dirname})
})

reGenerateADCSnapshot()
reGenerateSpectra()

setInterval(reGenerateADCSnapshot, 5000)
setInterval(reGenerateSpectra, 5000)

app.listen(port, '0.0.0.0')