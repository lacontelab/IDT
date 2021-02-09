#!/usr/bin/env python

# !/opt/miniconda3/envs/py27/bin/python

import sys
import os.path
import numpy as np

VERB=2

delay_strings=['in 1 day', 'in 1 week', 'in 1 month', 'in 3 months', 'in 1 year', 'in 5 years', 'in 25 years']
STIM_COND=['hard', 'easy', 'immediate', 'delayed', 'immediateA', 'immediateU', 'control', 'notcontrol']
STIM_COND.append("short")
STIM_COND.append("long")
STIM_COND.append("all")
hard_choice_frac = 0.2
minimum_amount = 0

if len(sys.argv) < 3:
    print('Usage: {} <output prefix [required]> ' \
          '<logfile 1 [required]> ' \
          '<logfile 2 [optional]> ' \
          '<...> ' \
          '<logfile n [optional]> '.format(sys.argv[0]))
    
    sys.exit(1)
    
output_prefix = sys.argv[1]
logfile_list = []
for i in range(2, len(sys.argv)):
    
    try:
        logfile_list.append(str(sys.argv[i]))
    except:
        print('ERROR <logfile {}> must be a string!'.format(i-1))
        sys.exit(1)
        
class stimlog:
    def __init__(self, logfile_list):
        self.logfile_list = logfile_list
        self.max_delay_amount = float(1000)
        self.logfile = []
        self.trial_number = []
        self.onset_time = []
        self.response_time = []
        self.ss_amount = []
        self.ll_amount = []
        self.ss_delay = []
        self.ll_delay = []
        self.response = []
        self.now_loc = []
        
        if len(list(set(logfile_list) & set(logfile_list))) != len(logfile_list):
            print('ERROR: The same filename was specified for multiple logfiles')
            raise
        
    def parse(self):
        
        for logfile in self.logfile_list:
            
            if VERB > 0:
                print('Parsing: {}'.format(logfile))
                
            try:
                f = open(logfile, 'r')
            except:
                print('ERROR: Opening logfile: {} failed!'.format(logfile))
                raise
            
            ln = 0
            header = 1
            for line in f:
                ln = ln + 1
                
                try:
                    vals = line.split(',')
                except:
                    print('ERROR: Could not split line: {} in logfile'.format(ln))
                    raise
                
                if len(vals) < 1:
                    continue
                
                if header:
                    if vals[0] == 'Delayed Amount':
                        try:
                            self.max_delay_amount = float(vals[1])
                        except:
                            print('ERROR: Could not split line: {} in logfile'.format(ln))
                            raise
                        
                    if vals[0] == 'Trial number':
                        header = 0
                        
                    continue
                
                if len(vals) == 9:
                    
                    try:
                        self.logfile.append(logfile)
                        self.trial_number.append(int(vals[0]))
                        self.onset_time.append(float(vals[1]))
                        self.response_time.append(float(vals[2]))
                        #self.ss_amount.append(float(vals[3].strip('gain $')))
                        #self.ll_amount.append(float(vals[4].strip('gain $')))
                        if 'gain $' in vals[3]:
                            self.ss_amount.append(float(vals[3].strip('""').strip('gain $')))
                            self.ll_amount.append(float(vals[4].strip('""').strip('gain $')))
                        elif 'lose $' in vals[3]:
                            self.ss_amount.append(float(vals[3].strip('""').strip('lose $')))
                            self.ll_amount.append(float(vals[4].strip('""').strip('lose $')))
                        else:
                            self.ss_amount.append(float(vals[3].strip('$')))
                            self.ll_amount.append(float(vals[4].strip('$')))
                        
                        #if int(vals[8]) == 0:
                        self.ss_delay.append(str(vals[5]))
                        self.ll_delay.append(str(vals[6]))
                        #elif int(vals[8]) == 1:
                            #self.ll_delay.append(str(vals[5]))
                            #self.ss_delay.append(str(vals[6]))
                        self.response.append(int(vals[7]))
                        self.now_loc.append(int(vals[8]))
                    except:
                        print('ERROR: Parsing error in line {} of logfile: {}'.format(ln,logfile))
                        raise
                else:
                    print('ERROR: Expecting 8, comma-separated values.') 
                    print('      Line: {} has: {}'.format(ln,len(vals)))
                    print('      {}'.format(line))
                    raise                
        f.close()
                
slog = stimlog(logfile_list)
slog.parse()

if VERB > 1:
    for i in range(0,len(slog.trial_number)):
        print('-------------------------------------')
        print('    logfile name    : {}'.format(slog.logfile[i]))
        print('    trial nr        : {}'.format(slog.trial_number[i]))
        print('    onset_time      : {:5.2f}'.format(slog.onset_time[i]))
        print('    resposne_time   : {:5.2f}'.format(slog.response_time[i]))
        print('    ss_amount       : {}'.format(slog.ss_amount[i]))
        print('    ll_amount       : {}'.format(slog.ll_amount[i]))
        print('    ss_delay        : {}'.format(slog.ss_delay[i]))
        print('    ll_delay        : {}'.format(slog.ll_delay[i]))
        print('    response        : {}'.format(slog.response[i]))
        print('    now_loc         : {}'.format(slog.now_loc[i]))
        
ll_delays_presented = list(set(slog.ll_delay) & set(delay_strings))

ss_delays_presented = list(set(slog.ss_delay) & set(delay_strings))

ss_amount_all_choices = []
ss_amount_now_choices = []
ss_amount_later_choices = []
id_point = []

reaction_times = [slog.response_time[i] - slog.onset_time[i] for i in range(len(slog.response_time))]
mean_reaction_times = np.mean(reaction_times)
median_reaction_times = np.median(reaction_times)
std_reaction_times = np.std(reaction_times)


for d in range(0,len(ll_delays_presented)):
    
    ll_delay_presented = ll_delays_presented[d]
    
    ss_amount_all_choices.append([])
    ss_amount_now_choices.append([])
    ss_amount_later_choices.append([])

    for i in range(0,len(slog.trial_number)):
        
        if slog.ss_delay[i] == 'now' and slog.ll_delay[i] == ll_delays_presented[d]:
            try:
                ss_amount = float(slog.ss_amount[i])
                #ss_amount = str(slog.ss_amount[i])
            except:
                print('ERROR: Cannot determine immediate amount for {}'.format(slog.ss_amount[i]))
                sys.exit(1)
                
            ss_amount_all_choices[d].append(ss_amount)
            
            if slog.response[i] == 0:
                
                if VERB > 1:
                    print('ll_delay_presented: {}, ss_delay = {}, ll_delay = {}, amount = {}, trial num = {}'.format(ll_delay_presented,slog.ss_delay[i],slog.ll_delay[i],ss_amount,slog.trial_number[i]))
                    
                ss_amount_now_choices[d].append(ss_amount)
                
            elif slog.response[i] == 1:
                
                ss_amount_later_choices[d].append(ss_amount)
                
    ss_amount_all_choices[d].sort(reverse=True)
    
    n_now = len(ss_amount_now_choices[d])
    n_all = len(ss_amount_all_choices[d])
    
    if n_now > 0 and n_now < n_all:
        id_point.append((ss_amount_all_choices[d][n_now] + ss_amount_all_choices[d][n_now - 1])/2.0)
        
    elif n_now == n_all:
        id_point.append((ss_amount_all_choices[d][-1] + slog.max_delay_amount)/2.0)
        
    else:
        id_point.append((ss_amount_all_choices[d][0])/2.0)
stim_cond = dict((key, ([], [], [])) for key in STIM_COND)
print(id_point)
#id_point.reverse()
newnclist=[]
newdlist=[]
newclist=[]
print(ll_delays_presented)
for i in range(0,len(slog.trial_number)):
    
    time_string = '{:.3f}:{:.3f}'.format(slog.onset_time[i],(slog.response_time[i]-slog.onset_time[i]))            
    stim_cond["all"][0].append(time_string)
    stim_cond["all"][1].append(slog.logfile[i])

    if slog.ss_amount[i] != minimum_amount and slog.ss_amount[i] != slog.max_delay_amount:
        if slog.ss_delay[i] == 'now' and slog.ll_delay[i] != 'now':
            stim_cond['immediateA'][0].append(time_string)
            stim_cond['immediateA'][1].append(slog.logfile[i])
        elif slog.ss_delay[i] != 'now' and slog.ll_delay[i] == 'now':
            stim_cond['immediateA'][0].append(time_string)
            stim_cond['immediateA'][1].append(slog.logfile[i])
        elif slog.ss_delay[i] != slog.ll_delay[i] and slog.ss_delay[i] != 'now':
            stim_cond['immediateU'][0].append(time_string)
            stim_cond['immediateU'][1].append(slog.logfile[i])
        elif slog.ss_delay[i] != slog.ll_delay[i] and slog.ll_delay[i] != 'now':
            stim_cond['immediateU'][0].append(time_string)
            stim_cond['immediateU'][1].append(slog.logfile[i])


    if float(slog.response_time[i] - slog.onset_time[i]) > median_reaction_times:
        stim_cond["long"][0].append(time_string)
        stim_cond["long"][1].append(slog.logfile[i])
    else:
        stim_cond["short"][0].append(time_string)
        stim_cond["short"][1].append(slog.logfile[i])

                        
    if slog.ss_amount[i] == minimum_amount or slog.ss_amount[i] == slog.max_delay_amount or \
       slog.ss_delay[i] == slog.ll_delay[i]:
        stim_cond['control'][0].append(time_string)
        stim_cond['control'][1].append(slog.logfile[i])        
        NC=False
    else:
        stim_cond['notcontrol'][0].append(time_string)
        stim_cond['notcontrol'][1].append(slog.logfile[i])         
        NC=True
        newnclist.append('o')

        if slog.response[i] == 0:
            stim_cond['immediate'][0].append(time_string)
            stim_cond['immediate'][1].append(slog.logfile[i])        
        else: 
            stim_cond['delayed'][0].append(time_string)
            stim_cond['delayed'][1].append(slog.logfile[i])    
            
        if NC:
            print(slog.ss_delay[i], slog.ll_delay[i])
            for d in range(0,len(ll_delays_presented)):                         # d from 0 to 3
                if slog.ss_delay[i] == 'now' and slog.ll_delay[i] == ll_delays_presented[d]:        
                    id_point_dist = abs(id_point[d] - slog.ss_amount[i])
                    if id_point_dist <= slog.max_delay_amount*hard_choice_frac:
                        stim_cond['hard'][0].append(time_string)
                        stim_cond['hard'][1].append(slog.logfile[i])
                    else:
                        stim_cond['easy'][0].append(time_string)
                        stim_cond['easy'][1].append(slog.logfile[i])             
#print(newnclist)    
#print(len(newclist))            
#print(len(newdlist))
for sc in STIM_COND:
    filename = output_prefix + '_' + sc + '.1D'
    if os.path.isfile(filename):
        print('Warning: Overwriting output file: {}'.format(filename))
        
    stim_cond[sc][2].append(filename)
    
for sc in STIM_COND:
    
    file = open(stim_cond[sc][2][0], 'w')
    
    if VERB>0:
        print('Writing: {}'.format(stim_cond[sc][2][0]))
        
    for logfile in slog.logfile_list:
        event_count = 0
        for i in range(0,len(stim_cond[sc][0])):
            if stim_cond[sc][1][i] == logfile:
                file.write('{} '.format(stim_cond[sc][0][i]))
                event_count = event_count + 1
                
        if event_count == 0:
            file.write('*\n')
        else:
            file.write('\n')
    file.close()

sys.exit(0)

# fix this so that it will integrate ll_amount and 9 value columns
