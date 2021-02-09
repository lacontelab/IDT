#!/usr/bin/env python

import shutil
import configparser
import os
import glob

init = configparser.ConfigParser()
init.read("config_initialize.txt")
sid = [ x.strip() for x in init.get("INITIALIZE","SubjectID").split(",") ]
session = [ x.strip() for x in init.get("INITIALIZE","Session").split(",")]
sid = str(sid[0])
session = str(session[0])

runs = [1, 2, 3]
dirname = os.path.dirname(os.path.abspath(__file__))
destination = dirname + '/data/{}/'.format(sid)

file = "config_initialize.txt"
try:
	shutil.move("config_initialize.txt", destination)
except OSError:
	if os.path.exists(destination+file):
		print("already moved")
	else:
		print("file does not exist")

for file in glob.glob(r'AdjAmt*csv'):
	try:
		shutil.move(file, destination)
	except OSError:
		if os.path.exists(destination+file):
			print("already moved")
		else:
			print("file does not exist")
