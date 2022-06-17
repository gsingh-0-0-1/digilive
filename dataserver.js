const express = require('express')
const bodyParser = require('body-parser')
var fs = require('fs');
const {URLSearchParams} = require('url')

const app = express()
const port = 9000

const http = require('http')
const server = http.createServer(app)

const io = require('socket.io')(server)

var DIR = "/home/gsingh/digilive/"

app.use(express.static(DIR + 'public'));

var jsonParser = bodyParser.json()

var urlencodedParser = bodyParser.urlencoded({ extended : false })

var SAMPLE_ADC_SNAPSHOTS = [];
var ADC_SAMPLES = 16384

var ADC_STDS_ARR = []

var SAMPLE_SPECTRA = [];
var SPECTRA_CHANS = 4096

var ANTENNAE = process.argv[2] * 1

var HALFRANGE = Math.pow(2, 13)
var IDEAL_ADC_STD = HALFRANGE / 8
var ADC_STD_VAR = IDEAL_ADC_STD * 0.5


var SPEC_MAX = -50
var SPEC_MIN = -110

var PULLTIME = ''

var ANTLO_COMBOS = []

var PAGES = [1, 2]

FREQ_DATA = [];

process.env.TZ = "America/Los_Angeles"

for (var i = 0; i < ANTENNAE; i++){
    FREQ_DATA.push([])
}

for (var page of PAGES){
    io.of("/" + String(page)).on('connection', (socket) => {
    })
}

//utility functions
function stdDev(array){
	const n = array.length
	const mean = array.reduce((a, b) => a + b) / n
	return Math.sqrt(array.map(x => Math.pow(x - mean, 2)).reduce((a, b) => a + b) / n)
}

function randomnormal(mean, std){
	var u = 0, v = 0;
	while(u === 0) u = Math.random(); //Converting [0,1) to (0,1)
	while(v === 0) v = Math.random();
	var out = Math.sqrt( -2.0 * Math.log( u ) ) * Math.cos( 2.0 * Math.PI * v )
	out = std*out + mean
	return out;
}

function randomuniform(center = 0, scale = 1){
	let val = 2 * (Math.random() - 0.5)
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
    ADC_STDS_ARR = []
	/*SAMPLE_ADC_SNAPSHOTS = []
	for (var j = 0; j < ANTENNAE; j++){
		var arr = []
		SAMPLE_ADC_SNAPSHOTS.push(arr)
		var subarr1 = []
		var subarr2 = []
		SAMPLE_ADC_SNAPSHOTS[j].push(subarr1)
		SAMPLE_ADC_SNAPSHOTS[j].push(subarr2)
		var std = [randomuniform(IDEAL_ADC_STD, ADC_STD_VAR)]
		std.push(std[0] + randomuniform(0, 3))
		for (var i = 0; i < ADC_SAMPLES; i++){
			for (var pol = 0; pol < 2; pol++){
				SAMPLE_ADC_SNAPSHOTS[j][pol].push(randomnormal(0, std[pol]))
			}
		}
	}*/

	//computing instead of storing the previous values so we can simulate actual
	//computation for when we pull real data
	for (var j = 0; j < ANTENNAE; j++){
        if (SAMPLE_ADC_SNAPSHOTS[j] == undefined){
            continue
        }
		let arr = [stdDev(SAMPLE_ADC_SNAPSHOTS[j][0]), stdDev(SAMPLE_ADC_SNAPSHOTS[j][1])]
		ADC_STDS_ARR.push(arr)
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
				if (randomuniform(0.5, 0.5) > 0.999){
					let randpol = Math.round(randomuniform(0.5, 0.5))
					SAMPLE_SPECTRA[j][randpol][SAMPLE_SPECTRA[j][randpol].length - 1] += randomuniform(30, 15)
				}
			}
		}
	}
}

app.get('/adcsnapshot/:id', (req, res) => {
	var id = req.params.id * 1
    if (SAMPLE_ADC_SNAPSHOTS[id - 1] === undefined){
        res.send("No data")
        return
    }
	var s = SAMPLE_ADC_SNAPSHOTS[id - 1][0].join("_")
	s = s + ":"
	s = s + SAMPLE_ADC_SNAPSHOTS[id - 1][1].join("_")

	var adc_stds = ADC_STDS_ARR[id - 1]

    s = String(adc_stds[0]) + "_" + String(adc_stds[1]) + "|" + s

	res.send(s)
})

app.get('/spectrum/:id', (req, res) => {
	var id = req.params.id * 1
    //console.log(SAMPLE_SPECTRA[id - 1])
    if (SAMPLE_SPECTRA[id - 1] === undefined){
        res.send("No data")
        return
    }
	var s = SAMPLE_SPECTRA[id - 1][0].join("_")
	s = s + ":"
	s = s + SAMPLE_SPECTRA[id - 1][1].join("_")

	res.send(SAMPLE_SPECTRA[id - 1][2] + "|" + s)
})

app.get('/adcstd/:id', (req, res) => {
	var id = req.params.id * 1
	res.send(ADC_STDS_ARR[id][0] + "_" + ADC_STDS_ARR[id][1])
})


app.get("/chart/:id", (req, res) => {
	res.sendFile("public/templates/livegraph.html", {root: __dirname})
})

app.get("/totalantennae", (req, res) => {
	res.send(String(ANTENNAE))
})

app.get("/setminmax/:min/:max", (req, res) => {
    var min = req.params.min * 1
    var max = req.params.max * 1
    //if (max > SPEC_MAX){
        SPEC_MAX = max
    //}
    //if (min < SPEC_MIN){
        SPEC_MIN = min
    //}
    res.send("OK")
})

app.get("/setfreqdata/:id/:low/:high/:step", (req, res) => {
    var id = req.params.id * 1
    var high = req.params.low * 1
    var low = req.params.high * 1
    var step = req.params.step * 1
    FREQ_DATA[id - 1] = [low, high, step]
    res.send("OK")
})

app.get("/getfreqdata/:id/", (req, res) => {
    var id = req.params.id * 1
    res.send(String(FREQ_DATA[id - 1][0]) + "_" + String(FREQ_DATA[id - 1][1]) + "_" + String(FREQ_DATA[id - 1][2]))
})

app.get("/getminmax", (req, res) => {
    res.send(String(SPEC_MIN) + "_" + String(SPEC_MAX))
})

app.post("/updateadc/:id", urlencodedParser, (req, res) => {
    var data = req.body.fulladc
    data = data.split(":")
    data[0] = data[0].split("_")
    data[1] = data[1].split("_")
    data[0] = data[0].map(Number)
    data[1] = data[1].map(Number)
    if (SAMPLE_ADC_SNAPSHOTS[req.params.id*1 - 1] == undefined){
        SAMPLE_ADC_SNAPSHOTS.push([])
    }
    SAMPLE_ADC_SNAPSHOTS[req.params.id*1 - 1] = data
    //reGenerateADCSnapshot()
    res.send("ADC_OK") 
})

app.post("/updatespec/:id", urlencodedParser, (req, res) => {
    var data = req.body.fullspec
    data = data.split(":")
    data[0] = data[0].split("_")
    data[1] = data[1].split("_")
    data[0] = data[0].map(Number)
    data[1] = data[1].map(Number)
    var curtime = String(Date()).split("GMT")[0]
    /*if (Math.round(ANTENNAE / 2) == req.params.id * 1){
        PULLTIME = curtime
        for (var page of PAGES){
            io.of("/" + String(page)).emit("pulltime", curtime)
        }
    }*/
    data.push(curtime)
      

    if (SAMPLE_SPECTRA[req.params.id*1 - 1] == undefined){
        SAMPLE_SPECTRA.push([])
    }
    SAMPLE_SPECTRA[req.params.id*1 - 1] = data
    //console.log(data)
    res.send("SPEC_OK")
})

app.get("/updatetime/:time", (req, res) => {
    PULLTIME = req.params.time
    for (var page of PAGES){
        io.of("/" + String(page)).emit("pulltime", PULLTIME)
    }
    res.send("OK")
})

app.get("/antlo_update/:id/:combo", (req, res) => {
    var id = req.params.id *= 1
    id = id - 1
    if (ANTLO_COMBOS[id] === undefined){
        ANTLO_COMBOS.push("")
    }
    ANTLO_COMBOS[id] = req.params.combo
    res.send("OK")
})

app.get("/antlo/:id", (req, res) => {
    res.send(ANTLO_COMBOS[req.params.id * 1 - 1])
})

app.get('/ping', (req, res) => {
    res.send('pong')
})

app.get("/lastpulltime", (req, res) => {
    res.send(PULLTIME)
})

app.get("/:pagenum", (req, res) => {
    res.sendFile("public/templates/main.html", {root: __dirname})
})

app.get("/", (req, res) => {
    res.sendFile("public/templates/landing.html", {root: __dirname})
})
//reGenerateADCSnapshot()
//reGenerateSpectra()

setInterval(reGenerateADCSnapshot, 10000)
//setInterval(reGenerateSpectra, 10000)

server.listen(port, '0.0.0.0')
//app.listen(port, '0.0.0.0')
