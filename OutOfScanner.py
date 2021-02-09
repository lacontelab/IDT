#!/usr/bin/env python

'''This script is the out of scanner version of the discounting task.'''
from psychopy import data, visual, core, event
from datetime import datetime 
import time
import numpy as np
import os 
from scipy.optimize import curve_fit
import shutil
import configparser
import json

########## CHANGE FOR TESTING  ######

# set SPEED to 1 to put the script in testing mode; isi greatly decreased
SPEED = 1

# set VERB to 1 to output more to the terminal
VERB = 0 

####################################

########## PART A: INITIALIZATION AND SETUP ##########

##### iterate through these delays and ask a specific number of questions for each of them 
delays = ['1 day', '1 week', '1 month', '3 months', '1 year', '5 years', '25 years']
sorteddelays = delays
np.random.shuffle(delays)
commodity = '$'

##### read config_initialize.txt to get subjectID and session #
init = configparser.ConfigParser()
init.read('config_initialize.txt')
sid = [ x.strip() for x in init.get('INITIALIZE','SubjectID').split(',') ]
exp = [ x.strip() for x in init.get('INITIALIZE','Session').split(',') ]
sid = str(sid[0])
exp = str(exp[0])

##### create the stimuli for the task
window             = visual.Window(fullscr = True,color="black")
initialtitle1      = visual.TextStim(window, text = 'This is the Out of Scanner Task',
	pos 	   = [0, 0.3],
	wrapWidth  = 1.5)
initialtitle2      = visual.TextStim(window, text = 'Press return to continue with the task', pos = [0, -0.1], wrapWidth=1.5)
instructions       = visual.TextStim(window, text = 'Please use the left or right key to choose the option you prefer in each case',
	color      = (1.0,1.0,1.0),
	pos        = [0, 0],
	wrapWidth  = 1.5)
title              = visual.TextStim(window, text = 'Which would you rather have?', 
	pos        = [0, 0.3],
	wrapWidth  = 1.5)
lefty              = visual.TextStim(window, text = ' ', pos = [-0.3, 0])
righty             = visual.TextStim(window, text = ' ', pos = [0.3, 0])
taskend            = visual.TextStim(window, text = 'Task Complete!', pos=[0,0])

left_choice        = visual.TextStim(window, text = ' ', 
	pos        = [-0.3, .1],
	height     = 0.1)

right_choice       = visual.TextStim(window, text = ' ',
	pos        = [0.3, 0.1],
	height     = 0.1)


##### constants that can change in the experiment 

answers      = [i for i in range(6)]	# initialize a list for answers
currentdelay = 0        		# this will be a counter used to iterate through the delays list
delayamount  = 1000     		# this will not change. criteria can be built in to facilitate a change here
amount       = 0.5              	# set at half to iterate toward indifference point (ID)
NOW          = [0, 1]           	# will get a choice of 1 or 0
response     = 0            		# initialize the response
screenText   = ['','']    		# initialize the money strings
question     = 0            		# initialize the question counter

firsttime    = 0			# trigger for beginning the task
stim_onset   = 0			# track stimulus onset timing
trialnum     = 0			# track trial number
IPs          = [0.0]*7			# initiate list for indifference points

##### initialize timing for logfile
tt = core.getTime()

##### initialize the logfile for writing
now_time = datetime.now()
init_time = now_time.strftime('%m-%d-%Y-%H-%M')
log_filename = 'AdjAmt_{}_{}_{}_{}_{}.csv'.format(sid,exp,delayamount,commodity,init_time)
   
logfile = open(log_filename,'w')    
logfile.write('Subject ID,{}\n'.format(sid))
logfile.write('Experiment,{}\n'.format(exp))
logfile.write('Delayed Amount,{}\n'.format(delayamount))
logfile.write('Commodity,{}\n'.format(commodity))
logfile.write('Trial number,Stimulus onset,Response time,Immediate amount,Delay,Response [0I;1D], Now loc [0L;1R]\n') 

##### Extract the information from config_outofscanner.txt
# note: this text file can be modified to personalize the task

config = configparser.ConfigParser()
config.read('config_outofscanner.txt')
rightkeys   = [ x.strip() for x in config.get('SETTINGS','right_trigger').split(',') ]
leftkeys    = [ x.strip() for x in config.get('SETTINGS','left_trigger').split(',') ]
quitkeys    = [ x.strip() for x in config.get('SETTINGS','quitkeys').split(',') ]
trigger     = [ x.strip() for x in config.get('SETTINGS','trigger').split(',') ]
alltriggers = []
alltriggers.extend(rightkeys)
alltriggers.extend(leftkeys)
alltriggers.extend(quitkeys)
alltriggers.extend(trigger)

if VERB > 0:
	print(alltriggers)

########## END PART A ###########

########## PART B: DEFINING AUXILLARY FUNCTIONS ##########

class DD():

	def move(src,dest): # move the important files to the new participant directory
		shutil.move(src,dest)

	def initialtitle(): # set up the first screen
		initialtitle1.draw()
		initialtitle2.draw()
		window.flip()
		firstKey = event.waitKeys(keyList = alltriggers)
		for key in firstKey:
			if key in trigger:
				continue
			else:
				core.quit()

	def instructions(): # show the instructions
		instructions.draw()
		window.flip()
		core.wait(5)

	def title(): # draw the which would you rather have line                       
		title.draw() 

	def ISI(): # draw the ISI cross
		#ISI.draw()
		title.draw()
		window.flip()
		if SPEED > 0:
			core.wait(0.05)
		else:
			core.wait(1)

	def switchNow(): # randomize the position of the immediate option                   
		global cnow
		cnow = np.random.choice(NOW)
		if cnow == 0:
			lefty.text   = 'now'
			righty.text  = 'in {}'.format(delays[currentdelay]) 
			now_location = 'left'
		else:
			lefty.text   = 'in {}'.format(delays[currentdelay])
			righty.text  = 'now'
			now_location = 'right'
		lefty.draw()
		righty.draw()

	def group(number): # 1000 becomes 1,000
		s = '{}'.format(number)
		groups = []
		while s and s[-1].isdigit():
			groups.append(s[-3:])
			s = s[:-3]
		if VERB > 0:
			print(groups)
		return s + ','.join(reversed(groups))
        
	def setAmount(): # if using less than 1000 as delay amount, use two decimal places
		global cnow, amount
		if delayamount < 1000:
			screenText[cnow]     = '${3:.2f}'.format(float(amount*delayamount))
			screenText[1 - cnow] = '${3:.2f}'.format(delayamount)
		else:
			screenText[cnow]     = '${}'.format(DD.group(int(amount*delayamount)))
			screenText[1 - cnow] = '${}'.format(DD.group(delayamount))

	def getAmount(response): # titrate immediate amount after a choice is made
		global amount
		if response == 0:
			amount = amount - (0.5**(question+2))
		else:
			amount = amount + (0.5**(question+2))
		if VERB > 0:
			print(amount)

	def switchMoney(): # put the immediate monetary option in the correct location
		global cnow
		if cnow == 0:
			left_choice.text  = screenText[cnow]
			right_choice.text = screenText[1 - cnow]
		else:
			left_choice.text  = screenText[1 - cnow]
			right_choice.text = screenText[cnow]
		left_choice.draw()
		right_choice.draw()

	def func(xvalues,k): # calculate the k value
		return 1/(1+(xvalues*k))


########## END PART B ##########

########## PART C: MAIN FUNCTION ##########

''' in the main function, we will call the other functions to go through the trials.
there will be 6 titrations for each of 7 delays, giving a total of 42 trials. the k-value
is calculated, and the IPs, kvalue, and JB rules are written to a text file. the file is 
parsed by the in scanner version to get relevant information for personalizing the task. '''


def main():
	global question, currentdelay, now_location, cnow, amount, response, \
		stim_onset, trialnum, firsttime

	DD.initialtitle()
	DD.instructions()
	if firsttime:
		stim_onset = tt
		firsttime = 0        

	while question < 6: 
		DD.switchNow()
		DD.title()
		DD.setAmount()
		DD.switchMoney()
		window.flip()
		ST = core.getTime() - tt 				# stimulus onset time calculated here
		allKeys = event.waitKeys(keyList = alltriggers)   
		for thisKey in allKeys:
			firsttime = 1
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
			RT = core.getTime() - tt			# response time calculated here 

			# for each choice, we record the trial number, stim onset time, response time,
			# the amount available NOW, the current temporal delay, the participant response,
			# and the location of the NOW choice.

			logfile.write('{},{},{},{},{},{},{}\n'.format(trialnum,
									ST,
									RT,
									int(amount*delayamount),
									delays[currentdelay],
									response,
									cnow))
			trialnum = trialnum + 1
			DD.getAmount(response)

			if VERB > 0:
				print(cnow,',', response)

			answers[question] = response
			if question < 5:
				question = question + 1
				DD.ISI()
			else:
				if VERB > 0:
					print(amount)
				IPs[sorteddelays.index(delays[currentdelay])] = amount
				if VERB > 0:
					print(IPs)
				question = 0
				amount = 0.5
				if currentdelay == 6:
					for i in range(7):
						logfile.write('{},'.format(sorteddelays[i]))
					logfile.write('\n')
					for i in range(7):
						logfile.write('{},'.format(IPs[i]))
					logfile.write('\n')
					JB1 = 0
					for i in range(6):
						if IPs[i+1] - IPs[i] > 0.2: JB1 += 1
					JB2 = 0
					if IPs[0] - IPs[6] < 0.1: JB2 = 1

					xx = [1,7,30.44,91.32,365.25,1826.25,9131.25]  # number of days per delay

					# the JB (Johnson Bickel) rules determine whether the responses are consistent
					# with delay discounting. Failure to pass these rules may relfect further inspection.

					JBpass = True
					if JB1 > 1: JBpass = False
					if JB2 > 0: JBpass = False
					logfile.write('JB Rule 1,{}\n'.format(JB1))
					logfile.write('JB Rule 2,{}\n'.format(JB2))
					
					if JBpass == False:
						print("Warning: Inconsistency detected")
					
					xvalues = np.array(xx)
					yvalues = np.array(IPs)
					(popt, pcov) = curve_fit(DD.func, xvalues, yvalues, p0 = 0.01)
					logfile.write('k value,{}\n'.format(float(popt)))
					IPs.append(popt)
					IPs.append(JB1)
					IPs.append(JB2)
					DD.ISI()
					taskend.draw()
					kvalue_file = 'kvalue_{}_{}.txt'.format(sid,exp)

					# store Indifference points, kvalue, and JB rules to json file
					data_dict = {}
					data_dict["IP_1day"] = IPs[0]
					data_dict["IP_1week"] = IPs[1]
					data_dict["IP_1month"] = IPs[2]
					data_dict["IP_3months"] = IPs[3]
					data_dict["IP_1year"] = IPs[4]
					data_dict["IP_5years"] = IPs[5]
					data_dict["IP_25years"] = IPs[6]
					data_dict["kvalue"] = float(popt)
					data_dict["JB1"] = JB1
					data_dict["JB2"] = JB2
					with open(kvalue_file,"w") as k:
						json.dump(data_dict,k)
					k.close()
					dirname = os.path.dirname(os.path.abspath(__file__))
					source_kfile = os.path.join(dirname,kvalue_file)
					source_logfile = os.path.join(dirname,log_filename)
					destination = dirname + '/data/{}/'.format(sid)
					if VERB > 0:
						print("Directory name:",dirname)
						print("Source file:",source_kfile)
						print("Destination:",destination)
					if not os.path.exists(destination):
						os.makedirs(destination)
					logfile.close()
					DD.move(source_kfile,destination)
					DD.move(source_logfile,destination)
					KVAL = visual.TextStim(window,text='Your k value: {}'.format(float(popt)), pos = [0, -0.2])
					KVAL.draw()
					window.flip()
					core.wait(12)
                    
					core.quit()
				else:
					currentdelay += 1
				DD.ISI()
                
if __name__ == '__main__':
	main()
