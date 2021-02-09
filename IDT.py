#!/usr/bin/env python

from psychopy import data, visual, core, event, logging
from psychopy.core import getTime
from psychopy.hardware.emulator import launchScan
import numpy as np
from datetime import datetime
import sys
import os
import shutil
import configparser
import json

########## used throughout ##########

VERB        = 1							# write more information to terminal
SPEED       = 1							# greatly decrease ISI, for testing
NOW         = [0,1]						# randomize position of immediate choice on screen
ISI_FAST    = 0.25						# new ISI for testing
CLOCK       = core.Clock()					# clock used for timing 
ISI_DIST    = np.hstack((np.linspace(1,4,150),
		np.linspace(4,7,100),
		np.linspace(7,11,50)))  			# interstimulus interval distribution with median 4 s

########## used throughout ##########

########## PART A: INITIALIZATION AND SETUP ##########

##### 1. read data written by the initializer

# requires running initializer.py
# also requires config_initialize.txt being present in current folder

init = configparser.ConfigParser()
init.read("config_initialize.txt")
sid     = [ x.strip() for x in init.get("INITIALIZE", "SubjectID").split(",") ]
session = [ x.strip() for x in init.get("INITIALIZE", "Session").split(",") ]
sid     = str(sid[0])
session = int(session[0])

# set up commodity information
# LARGER LATER amount set to $1000

commodityD = "$"
commodityI = commodityD
amountD = float(1000)
amountI = amountD
directory = os.path.dirname(os.path.abspath(sys.argv[0]))

##### 2. set up the logfile name
now_time = datetime.now()
init_datetime = now_time.strftime("%m-%d-%Y-%H-%M--%S")
init_date = now_time.strftime("%m-%d-%Y")
init_time = now_time.strftime("%H-%M-%S")
log_filename = "{}/data/{}/IDT_forparsing_{}_{}_{}.csv".format(directory,sid,sid,session,init_datetime)

##### 3. Get the out of scanner information (k-value)

kvalue_path = "data/{}/kvalue_{}_{}.txt".format(sid,sid,session)

IPs = []
JBs = []
with open(kvalue_path) as f:
	data_dict = json.load(f)

for key in data_dict:
	if "IP" in key:
		IPs.append(data_dict[key])
	elif key == "kvalue":
		kvalue = data_dict[key]
	else:
		JBs.append(data_dict[key])	
	
f.close()

if VERB > 0:
	print("K-value:",kvalue)
	if JBs[0] > 1 or JBs[1] > 0:
		print("Warning: JB rules FAILED. Inconsistent responses detected")

##### 4. individualize task based on k-value

# note: see Koffarnus, et al 2017, Neuroimage Paper

if kvalue > 0.03542:

	delays = ["1 day", "1 week", "1 month", "3 months"]
	sorted_delays = delays
	IP_index = 0

elif kvalue > 0.0098:

	delays = ["1 week", "1 month", "3 months", "1 year"]
	sorted_delays = delays
	IP_index = 1

elif kvalue > 0.002813:

	delays = ["1 month", "3 months", "1 year", "5 years"]
	sorted_delays = delays
	IP_index = 2
	
else:

	delays = ["3 months", "1 year", "5 years", "25 years"]
	sorted_delays = delays 
	IP_index = 3

if VERB > 0:
	print(delays)

##### 5. randomize the order of the delays and set variables

question = 0
current_delay = 0
other_delay = 0
screenText = ["XXXXXXX","XXXXXXX"]
screenText2 = ["XXXXXXX","XXXXXXX"]
now = 1
first_time = 1
response = 0
task_end_on = 0
trial_num = 0
IPs = [0.0]*7
amount = 0.5
amtText = ["",""]
amtText0I = ""
amtText0D = ""
delText = ["",""]

##### 6. Set up the logfile header

logfile = open(log_filename, "w")
logfile.write("Subject ID,{}\n".format(sid))
logfile.write("Session,{}\n".format(session))

logfile.write("Date,Time,CommodityD,CommodityI,Amount,EquivAmt,Task type,Amount sign,Time sign,Zero\n")

logfile.write("{},{},{},{},{},{}".format(init_date,
					init_time,
					commodityD,
					commodityI,
					amountD,
					amountI))
logfile.write(",Delay disc,Gains,Future,Implicit\n")
logfile.write("Delayed Amount,{}\n\n".format(amountD))
logfile.write("Trial number,Stimulus onset,Response time,SS amount,LL amount,SS delay,LL delay,Response [-1O;0I;1D],Now loc [0L;1R]\n")

##### 7. Load data from configuration file.

# note: this information can be edited for personalization

config = configparser.ConfigParser()

config.read("config_inscanner.txt")
rightkeys    = [ x.strip() for x in config.get("SETTINGS", "right_trigger").split(",") ]
leftkeys     = [ x.strip() for x in config.get("SETTINGS", "left_trigger").split(",") ]
quitkeys     = [ x.strip() for x in config.get("SETTINGS", "quitkeys").split(",") ]
trigger      = config.get("SETTINGS", "trigger")
TR           = config.get("SETTINGS", "TR")
alltriggers  = []
alltriggers.extend(rightkeys)
alltriggers.extend(leftkeys)
alltriggers.extend(quitkeys)

########## END PART A ###################################

########## PART B: DEFINING AUXILLARY FUNCTIONS ##########

class DD():

	def instructions():

		# write the instructions screen

		title = visual.TextStim(window,
					text      = "",
					color     = [1,1,1],
					pos       = [0,0],
					wrapWidth = 1.5)
		title.text = '''Use the left or right key to choose the option you prefer in each case. Keep your eyes focused on the center of the screen.'''
		title.draw()
		window_instructions = window.flip()
		logging.data("Instructions:{}".format(window_instructions))
		core.wait(7)

	def switchNewText():
		global current_delay, delays

		# write the screen that is shown when switching to a new delay

		newset = visual.TextStim(window,
					text = "",
					color = [1,1,1],
					pos = [0,0.3],
					wrapWidth = 1.5)

		newset.text = "Next Delay: {}".format(delays[current_delay])
		newset.draw()
		window_nextDelay = window.flip()
		logging.data("Next Delay:{}".format(window_nextDelay))
		core.wait(3)

	def switchNewBack():

		# write some text for the trial screen

		newset = visual.TextStim(window,
					text = "",
					color = [1,1,1],
					pos = [0, 0.3],
					wrapWidth = 1.5)
		newset.text = "Which would you rather choose?"
		newset.draw()

	def switchScrTxt():
		global screenText, newset, isi

		# write text for the interstimulus interval

		newset = visual.TextStim(window,
					text = "",
					color = [1,1,1],
					pos = [0,0.3],
					wrapWidth = 1.5)
		newset.text = "Which would you rather choose?"

		left_choice = visual.TextStim(window,
						text = "",
						color = [1,1,1],
						pos = [-0.3, 0.1],
						wrapWidth = 1.5)
		left_choice2 = visual.TextStim(window,
						text = "",
						color = [1,1,1],
						pos = [-0.3, 0],
						wrapWidth = 1.5)
		right_choice = visual.TextStim(window,
						text = "",
						color = [1,1,1],
						pos = [0.3, 0.1],
						wrapWidth = 1.5)
		right_choice2 = visual.TextStim(window,
						text = "",
						color = [1,1,1],
						pos = [0.3, 0],
						wrapWidth = 1.5)
		fixation = visual.ShapeStim(window,
						vertices = ((0, -0.05), (0, 0.05), (0,0), (-0.05,0), (0.05,0)),
						pos = [0,0],
						closeShape = False)

		screenText = ["XXXXXXX","XXXXXXX"]
		screenText2 = ["XXXXXXX","XXXXXXX"]
		left_choice.text = screenText[0]
		right_choice.text = screenText[1]
		left_choice2.text = screenText2[0]
		right_choice2.text = screenText2[1]
		left_choice.draw()
		right_choice.draw()
		left_choice2.draw()
		right_choice2.draw()
		fixation.draw()
		newset.draw()
		window_switchScreenText = window.flip()
		logging.data("Switch Screen Text:{}".format(window_switchScreenText))

		if SPEED > 0:
			core.wait(ISI_FAST)
		else:
			core.wait(isi)

	def switchNow():
		global cnow

		# randomize the position of the immediate choice

		cnow = np.random.choice(NOW)

	def switchIndiffPt():
		global current_delay, amounts, noncontrolamounts

		"""
		this function is used to set up the amounts that will be used for the trials.
		the list containing the values consists mainly of fractions that will lower
		the delayed value. it also includes 'now' and 'notnow' options that allow 
		for adding control trials and for trials in which no immediate option is presented.
		see Koffarnus et al. 2017 Neuroimage paper
		"""

		indiff = IPs[IP_index + sorted_delays.index(delays[current_delay])]
		
		amounts = [1.0, 0.95, 0.85, 0.75, 0.65, 0.55, 0.45, 0.35, 0.25, 0.15, 0.05, 0.0]
		noncontrolamounts = [0.95, 0.85, 0.75, 0.65, 0.55, 0.45, 0.35, 0.25, 0.15, 0.05]
		amounts.append(indiff)
		amounts.append(indiff + 0.04)
		amounts.append(indiff + 0.08)
		amounts.append(indiff - 0.04)
		amounts.append(indiff - 0.08)

		for i in range(12, 17):
			if amounts[i] > 1: amounts[i] -= 0.1
			if amounts[i] < 0: amounts[i] += 0.1

		amounts.append("now")
		amounts.append("now")
		amounts.append("now")

		if current_delay == 0:
			amounts.append("notnow1")
			amounts.append("notnow2")
			amounts.append("notnow3")
			amounts.append("notnow{}".format(np.random.choice([1,2,3])))
			amounts.append("notnow{}".format(np.random.choice([1,2,3])))

		if current_delay == 1:
			amounts.append("notnow0")
			amounts.append("notnow2")
			amounts.append("notnow3")
			amounts.append("notnow{}".format(np.random.choice([0,2,3])))

		if current_delay == 2:
			amounts.append("notnow0")
			amounts.append("notnow1")
			amounts.append("notnow3")
			amounts.append("notnow{}".format(np.random.choice([0,1,3])))

		if current_delay == 3:
			amounts.append("notnow0")
			amounts.append("notnow1")
			amounts.append("notnow2")
			amounts.append("notnow{}".format(np.random.choice([0,1,2])))
			amounts.append("notnow{}".format(np.random.choice([0,1,2])))

		np.random.shuffle(amounts)

	def switchDelays():
		global amounts, noncontrolamounts, cnow

		"""
		this function is for switching the delay text. this is required when
		the trial is a control trial or when the trial does not have an
		immediate option available

		if the trial is a control trial with both options being offered now, then
		both delays are written as now and the smaller amount is chosen from the 
		a separate list. 

		if the trial has no immediate option available, the smaller amount is chosen from
		a separate list, and the 'other delay' is chosen based on the integer value attached
		to the notnow string.

		otherwise, the trial continues as usual
		"""

		if amounts[question] == "now":	
			delText[cnow] = "now"
			delText[1 - cnow] = "now"
			amounts[question] = np.random.choice(noncontrolamounts)

		elif "notnow" in str(amounts[question]):
			other_delay = int(amounts[question][6])
			amounts[question] = np.random.choice(noncontrolamounts)
			if sorted_delays.index(delays[other_delay]) < sorted_delays.index(delays[current_delay]):
				delText[cnow] = "in {}".format(delays[other_delay])
				delText[1 - cnow] = "in {}".format(delays[current_delay])
			else:
				delText[cnow] = "in {}".format(delays[current_delay])
				delText[1 - cnow] = "in {}".format(delays[other_delay])

		else:
			delText[cnow] = "now"
			delText[1 - cnow] = "in {}".format(delays[current_delay])

	def switchCommodityI():
		global cnow

		# change text for the immediately available commodity
		# taking into account the decimal places

		if commodityI == "$":
			amtText0I = "$0"
			if amountI < 1000:
				amtText[cnow] = "${3:.0f}".format(float(amountI*amounts[question]))
			else:
				amtText[cnow] = "${:.0f}".format(float(round(amountI*amounts[question])))

		else:
			amtText0I = "0 {}".format(commodityI)

			if amountI < 1:
				amtText[cnow] = "{1:.2f} {}".format(float(amountI*amounts[question]), commodityI)
			elif amountI < 10:
				amtText[cnow] = "{1:.1f} {}".format(float(amountI*amounts[question]), commodityI)
			else:
				amtText[cnow] = "{} {}".format(float(round(amountI*amounts[question])), commodityI)

	def switchCommodityD():
	
		# change text for the delayed commodity
		# taking into account the decimal places

		if commodityD == "$":
			amtText0D = "$0"
			if amountD < 1000:
				amtText[1 - cnow] = "${3:.0f}".format(amountD)
			else:
				amtText[1 - cnow] = "${:.0f}".format(round(amountD))
		else:
			amtText0D = "0 {}".format(commodityD)
			if amountD < 1:
				amtText[1 - cnow] = "{1:.2f} {}".format(float(amount), commoidtyD)
			elif amountD < 10:
				amtText[1 - cnow] = "{1:.1f} {}".format(float(amountD), commodityD)
			else:
				amtText[1 - cnow] = "{} {}".format(float(round(amountD,0)), commodityD)


	def switchExplicit():

		# explictly configure the text for the trial screen

		screenText[cnow] = "{}".format(amtText[cnow])
		screenText2[cnow] = "{}{}".format(amtText0I, delText[cnow])
		screenText[1 - cnow] = "{}".format(amtText[1 - cnow])
		screenText2[1 - cnow] = "{}{}".format(amtText0D, delText[1 - cnow])

	def leftandright():
		global cnow, screenText, amtText

		# write the commodity amounts to either side of the screen

		left_choice = visual.TextStim(window,
						text = "",
						color = [1,1,1],
						pos = [-0.3, 0.1],
						wrapWidth = 1.5)

		right_choice = visual.TextStim(window,
						text = "",
						color = [1,1,1],
						pos = [0.3, 0.1],
						wrapWidth = 1.5)
		
		if cnow == 0:
			left_choice.text = screenText[cnow]
			right_choice.text = screenText[1 - cnow]
		else:
			left_choice.text = screenText[1 - cnow]
			right_choice.text = screenText[cnow]

		left_choice.draw()
		right_choice.draw()

	def left2andright2():
		global cnow, screenText2, delText

		# write the delays to either side of the screen

		left_choice2 = visual.TextStim(window,
						text = "",
						color = [1,1,1],
						pos = [-0.3, 0],
						wrapWidth = 1.5)
		right_choice2 = visual.TextStim(window,
						text = "",
						color = [1,1,1],
						pos = [0.3, 0],
						wrapWidth = 1.5)

		if cnow == 0:
			left_choice2.text = screenText2[cnow]
			right_choice2.text = screenText2[1 - cnow]
			now_location = "left"
		else:
			left_choice2.text = screenText2[1 - cnow]
			right_choice2.text = screenText2[cnow]
			now_location = "right"
		left_choice2.draw()
		right_choice2.draw()

	def showTaskEnd():

		# write and display the task complete screen

		the_end = visual.TextStim(window,
					text = "Task Complete",
					pos = [0,0])
		the_end.draw()
		window_taskEnd = window.flip()
		logging.data("Show Task End:{}".format(window_taskEnd))
		core.wait(5)
		core.quit()

	def launchTheScan():

		# configure menu screen from psychopy function

		settings = dict([("TR",TR), ("volumes",2000), ("sync",trigger)])
		menu_screen = launchScan(window, settings, globalClock = CLOCK, simResponses = None, mode = "Scan", esc_key = "escape", instr = "Select Scan or Test, press enter", wait_msg = "Waiting for scanner...", wait_timeout = 30, log = True)

########## END PART B #####################

########## PART C: MAIN FUNCTION ##########

"""
In the main function, the code will iterate through 98 trials. the four delays used
are based on the individual k-value. the responses and timing, as well as information
about each trial, are captured and written to a csv file, which can be parsed 
with our python parser to generate AFNI stim files.

The interstimulus interval is based on the delay discounting paradigm used by MacKillop et al. 
It is chosen from a distribution between 1 and 11 seconds that has an average of about 4 seconds. 
In that paradigm, subjects are allotted 6 seconds to make a decision before the task moves to the 
next trial. if the choice is made in under 6 seconds, the remaining time is added to the choice 
from the isi distribution.

(See supplementary information for Amlung, et al. 2012 'Dissociable Brain Signatures 
of Choice Conflict and Immediate Reward Preferences in Alcohol Use Disorders').

This task removes the restriction on time and requires participant input to move the task forward.
"""

def main():
	global screenText, question, amountRow, delay, amount, current_delay, screenText2
	global isi, now, first_time, response, task_end_on, indiff, amounts, amountlist
	global noncontrolamounts, ST, RT, amtText, amtText0I, amtText0D, delText, trial_num

	DD.launchTheScan()
	DD.instructions()

	if first_time:
		first_time = 0

		while question < 50:
			if current_delay == 0 and question == 0: DD.switchNewText()
			DD.switchNow()
			DD.switchNewBack()
			if question == 0: DD.switchIndiffPt()
			DD.switchDelays()
			DD.switchCommodityI()
			DD.switchCommodityD()
			DD.switchExplicit()
			DD.leftandright()
			DD.left2andright2()
			window_trialPresentation = window.flip()
			ST = CLOCK.getTime()
			logging.data("Trial Presentation:{}".format(window_trialPresentation))

			allKeys = event.waitKeys(keyList = alltriggers)
			for thisKey in allKeys:
				first_time = 1
				RT = CLOCK.getTime()
				if thisKey in leftkeys and cnow == 0:
					response = 0
				elif thisKey in leftkeys and cnow == 1:
					response = 1
				elif thisKey in rightkeys and cnow == 0:
					response = 1
				elif thisKey in rightkeys and cnow == 1:
					response = 0
				else:
					core.quit()
				logging.data("Choice {}:{}".format(question,thisKey))

				if (RT - ST < 6):
					isi = np.random.choice(ISI_DIST) + (6 - (RT-ST))
				else:
					isi = np.random.choice(ISI_DIST)

				logfile.write("{},{},{},{},{},{},{},{},{}\n".format(trial_num,
										ST,
										RT,
										screenText[cnow],
										screenText[1-cnow],
										screenText2[cnow],
										screenText2[1-cnow],
										response,
										cnow))
				trial_num += 1
				if question < len(amounts) - 1:
					question += 1
					DD.switchScrTxt()

				else:
					if current_delay == 3:
						question = 99
						first_time = 0
					else:
						question = 0
						current_delay += 1
						if VERB > 0:
							print(current_delay)
						DD.switchNewText()

		DD.showTaskEnd()
	else:
		if question < 50: first_time = 1

		return 1

########## END PART C ###################

if __name__ == "__main__":
	window = visual.Window(fullscr = True, color = "black")
	logging.LogFile(f="data/{}/IDT_psychopy_logging_{}_{}.csv".format(sid,sid,session),level=0)
	main()
	logging.flush()

# having served its purpose, we move the config file to the subject directory
shutil.move("config_initialize.txt", "data/{}/".format(sid))
logfile.close()
	
