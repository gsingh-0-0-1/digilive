import subprocess
import sys
import time

N_ANTENNAE = int(sys.argv[1])

f = open("pids.txt", "w")

for i in range(N_ANTENNAE):
	proc = subprocess.Popen(["python3", "/home/sonata/gsingh_tests/digilive/processor.py", str(i + 1)])
	f.write(str(proc.pid) + "\n")
	time.sleep(0.2)

f.close()
