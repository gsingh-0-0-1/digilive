import subprocess
import os

f = open(os.environ["DIGILIVE_INFO_DIR"] + "pids.txt", "r")
d = f.read()
f.close()
for pid in d.split("\n"):
	subprocess.Popen(["kill", str(pid)])

