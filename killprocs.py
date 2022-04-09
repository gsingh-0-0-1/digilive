import subprocess

f = open("/home/sonata/gsingh_tests/digilive/pids.txt", "r")
d = f.read()
f.close()
for pid in d.split("\n"):
	subprocess.Popen(["kill", str(pid)])

