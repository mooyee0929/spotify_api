import subprocess
import time

for i in range(2018,2020):
    for j in range(0,4):
        cmd = 'python .\data.py -y '+str(i)+' -t '+str(j)
        output = subprocess.getoutput(cmd)
        print(output)