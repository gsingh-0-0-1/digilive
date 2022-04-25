import subprocess
import os

DIR = os.environ["DIGILIVE_INFO_DIR"] 

subprocess.Popen(["python3", DIR + "killprocs.py"])

with open(DIR + "pullid.txt", "r") as f:
    d = f.read()
    print(d)
    subprocess.Popen(["kill", d])

with open(DIR + "webid.txt", "r") as f:
    d = f.read()
    print(d)
    subprocess.Popen(["kill", d])

