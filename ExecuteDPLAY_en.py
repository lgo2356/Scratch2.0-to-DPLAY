import subprocess
import os


def execute_scratch():
    subprocess.call("utills\\dplay_en.sb2", shell=True)
    os.system('taskkill /im DPLAY_en.exe')
    os.system('taskkill /im s2a_fm.exe')


def execute_s2a_fm():
    subprocess.call('utills\\s2a_fm.exe', shell=True)
