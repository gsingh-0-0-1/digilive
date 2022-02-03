import subprocess

N_ANTENNAE = 6

f = open("pids.txt", "w")

for i in range(N_ANTENNAE):
	proc = subprocess.Popen(["python3", "processor.py", str(i + 1)])
	f.write(str(proc.pid) + "\n")

f.close()