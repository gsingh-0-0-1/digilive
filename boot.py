import os
import subprocess
import sys
import time

N_ANTENNAE = 40#int(sys.argv[1])

DIR = os.environ["DIGILIVE_INFO_DIR"]
if DIR[-1] != '/':
    DIR = DIR + "/"

f = open("errorlog.txt", "w")
webserver_proc = subprocess.Popen(["env","TZ='America/Los_Angeles'", "node", DIR + "dataserver.js", "40"], stdout = subprocess.DEVNULL, stderr = f, cwd = DIR)
with open(DIR + "webid.txt", "w") as f:
    f.write(str(webserver_proc.pid))

time.sleep(1)

f = open("errorlog.txt", "w")
pull_proc = subprocess.Popen(["python3", DIR + "pull.py"], stdout = subprocess.DEVNULL, stderr = f, cwd = DIR)
with open(DIR + "pullid.txt", "w") as f:
    f.write(str(pull_proc.pid))

time.sleep(1)

f = open("errorlog.txt", "w")
processors_proc = subprocess.Popen(["python3", DIR + "startprocs.py", str(N_ANTENNAE)], stdout = subprocess.DEVNULL, stderr = f, cwd = DIR)

