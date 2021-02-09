#!/usr/bin/env python

import os
import re

sid = input('Subject ID: ')
exp = input('Session (#): ')

with open('config_initialize.txt','w',newline='\r\n') as f:
	f.write('[INITIALIZE]\n')
	f.write('SubjectID = {},\n'.format(sid))
	f.write('Session = {},\n'.format(exp))

f.close()

if not os.path.exists('data/'):
	os.makedirs('data/')

if not os.path.exists('data/{}/'.format(sid)):
	os.makedirs('data/{}/'.format(sid))
