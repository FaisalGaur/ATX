# coding: utf-8
#
# author: codeskyblue(hzsunshx)
# created: 2016-05-16
# modified: 2016-08-19
#
# Experiment of caculate FPS of android without root
# code reference from chromiumwebapps/chromium
#
# It is insteresting to know this way which can calculate not only fps, but also every frame use time.
# Is it really useful, I don't know, really don't know.
# so code just stop here.

import time
import subprocess
import re
import csv

import numpy as np
import matplotlib.pyplot as plt
import datetime as dt

nanoseconds_per_second = 1e9

def subprocess_cmd(command):
    try:
        
        process = subprocess.Popen(command,stdout=subprocess.PIPE, shell=True)
        proc_stdout = process.communicate()[0].strip()
        return proc_stdout
    
    except Exception, error:
        print error

def old_top_view():
    try:
        out = subprocess_cmd("adb shell \"dumpsys window windows | grep -E 'mCurrentFocus'\"")
        top_view = None
        view_name = out.split()
        view_name = view_name[-1]
        top_view = view_name[:-1]

        return top_view

    except Exception, error:
        print error


def get_top_view():
    try:
        out = subprocess.check_output(['adb', 'shell', 'dumpsys', 'SurfaceFlinger'])
        lines = out.replace('\r\n', '\n').splitlines()
        max_area = 0
        top_view = None
        for index, line in enumerate(lines):
            line = line.strip()
            if not line.startswith('+ Layer '):
                continue
            m = re.search(r'\((.+)\)', line)
            if not m:
                continue
            view_name = m.group(1)
            (x0, y0, x1, y1) = map(int, re.findall(r'(\d+)', lines[index+4]))
            cur_area = (x1-x0) * (y1-y0)
            if cur_area > max_area:
                max_area = cur_area
                top_view = view_name
        return top_view

    except Exception, error:
        print error

def init_frame_data(view):
    try:
        out = subprocess.check_output(['adb', 'shell', 'dumpsys', 'SurfaceFlinger', '--latency-clear', view])
        if out.strip() != '':
            raise RuntimeError("Not supported.")
        time.sleep(0.1)
        (refresh_period, timestamps) = frame_data(view)
        base_timestamp = 0
        base_index = 0
        for timestamp in timestamps:
            if timestamp != 0:
                base_timestamp = timestamp
                break
            base_index += 1

        if base_timestamp == 0:
            print("Initial frame collect failed, Trying alternate method")
        return (refresh_period, base_timestamp, timestamps[base_index:])

    except Exception, error:
        print error


def frame_data(view):
    try:
        out = subprocess.check_output(['adb', 'shell', 'dumpsys', 'SurfaceFlinger', '--latency', view])
        results = out.splitlines()
        refresh_period = long(results[0]) / nanoseconds_per_second
        timestamps = []
        for line in results[1:]:
            fields = line.split()
            if len(fields) != 3:
                continue
            (start, submitting, submitted) = map(int, fields)
            if submitting == 0:
                continue

            timestamp = submitting/nanoseconds_per_second
            timestamps.append(timestamp)
        return (refresh_period, timestamps)

    except Exception, error:
        print 'Failed to get application latency data'

    
def plot_data(fps_count,current_time,x_axis_start, x_axis_end):
    try:
        plt.rcParams['toolbar'] = 'None' 
        fig = plt.figure(figsize=(6, 4),num='Frame Rate Counter')
        current_time_format = current_time.strftime("%H:%M:%S")
        plt.title('Current FPS: {}  TIME: {}'.format(fps_count,current_time_format))
        plt.axis([x_axis_start, x_axis_end, 0, 65])
        plt.grid(b=True, which='major',axis='both', color='0.65', linestyle='-')
        plt.vlines(current_time, 0,fps_count,colors='b', linewidth=5)
        plt.xlabel('Time -->')
        plt.ylabel('FPS -->')
        fig.tight_layout()
        plt.pause(0.05)
        
    except Exception, error:
        print 'Could not plot graph!'
        print error
                  

def save_csv(col_1,col_2,mode):
    try:
        with open('fps_data.csv',mode) as out:
            csv_out=csv.writer(out)
            csv_out.writerow([col_1,col_2])

    except Exception, error:
        print 'Could not save csv file'
        print error

def continue_collect_frame_data():
    try:
        
        view =  get_top_view()
        if view is None:
            view = old_top_view()

        refresh_period, base_timestamp, timestamps = init_frame_data(view)

        if base_timestamp == 0:
            view = 'SurfaceView'
        print 'Current view:', view
        
                
        timestamps = []
        refresh_period, base_timestamp, timestamps = init_frame_data(view)
        t_minus = dt.timedelta(seconds=-13)
        t_plus = dt.timedelta(seconds=+3)

    except Exception, error:
        print error
        print 'Make sure device is connected and test application is running'
        
    try:
        
        while True:
            refresh_period, tss = frame_data(view)
            last_index = 0
            if timestamps:
                recent_timestamp = timestamps[-2]
                last_index = tss.index(recent_timestamp)
            timestamps = timestamps[:-2] + tss[last_index:]
            
            time.sleep(1)
            
            ajusted_timestamps = []
            for secs in timestamps[:]:
                secs -= base_timestamp
                if secs > 1e6: # too large, just ignore
                    continue
                ajusted_timestamps.append(secs)

            from_time = ajusted_timestamps[-1] - 1.0
            fps_count = 0
            for secs in ajusted_timestamps:
                if secs > from_time:
                    fps_count += 1

            current_time = dt.datetime.now()
            print fps_count,current_time
            time_format = current_time.strftime("%H:%M:%S")
            save_csv(fps_count,time_format,'ab')

            x_axis_start = current_time + t_minus
            x_axis_end = current_time + t_plus
         
            plot_data(fps_count,current_time,x_axis_start, x_axis_end)             

    except Exception, error:
        print 'Could not run tests on current application window'
    except KeyboardInterrupt:
        print 'Closed by user!'
        pass


if __name__ == '__main__':
    save_csv('FPS','TIME','wb')
    continue_collect_frame_data()
    plt.close('all')

    

