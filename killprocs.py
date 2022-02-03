import subprocess

f = open("pids.txt", "r")
d = f.read()
f.close()
for pid in d.split("\n"):
	subprocess.Popen(["kill", str(pid)])