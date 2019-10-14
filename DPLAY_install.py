import os
import subprocess


subprocess.call('installers\\CP210x_Windows_Drivers\\CP210xVCPInstaller_x64', shell=True)
subprocess.call('installers\\AdobeAIRInstaller.exe', shell=True)
os.system('installers\\Scratch-458.0.1.exe')
