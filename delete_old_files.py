import os
import time
import subprocess

now = time.time()

folders = ['/home/user/scripts/cx_monitor/har', '/home/user/scripts/cx_monitor/log']

for folder in folders:
    files = [os.path.join(folder, filename) for filename in os.listdir(folder)]

    for file in files:
        if (now - os.stat(file).st_mtime) > 604800:
            command = "rm {0}".format(file)
            subprocess.call(command, shell=True)