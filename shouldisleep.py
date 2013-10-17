#!/usr/bin/python2

import time
import subprocess
import dbus

import pynotify


PERIOD = 5
BLOCKING_PROGRAMS = ['transmission']
APP_NAME = 'should-I-sleep'
inhibited = False
inhibition_reason = 'Unknown'
lock = -1


def check_suspend():
    if is_blocking_program_running() or is_client_connected():
        inhibit()

    else:
        un_inhibit()
    time.sleep(PERIOD)


def get_blocking_programs():
    return BLOCKING_PROGRAMS


def is_client_connected():
    global inhibition_reason
    ps = subprocess.Popen('netstat', shell=True, stdout=subprocess.PIPE)
    output = ps.communicate()[0]
    for line in output.split('\n'):
        if 'nfs' in line and 'localhost' in line:
            inhibition_reason = "Active NFS session : " + line
            return True
    return False


def is_blocking_program_running():
    global inhibition_reason
    ps = subprocess.Popen('ps aux', shell=True, stdout=subprocess.PIPE)
    output = ps.communicate()[0]
    for line in output.split('\n'):
        for program in BLOCKING_PROGRAMS:
            if program in line:
                inhibition_reason = "Running program : " + program
                return True
    return False


def suspend():
    notify(' suspending the system ...')
    bus = dbus.SystemBus()
    proxy_object = bus.get_object('org.freedesktop.login1', '/org/freedesktop/login1')
    pm = dbus.Interface(proxy_object, 'org.freedesktop.login1.Manager')
    pm.Suspend(True)


def notify(message):
    if pynotify.init(APP_NAME):
        n = pynotify.Notification(APP_NAME, message)
        n.show()


def inhibit():
    global lock
    global inhibited
    global inhibition_reason

    if inhibited:
        return

    notify('Suspend inhibited : ' + inhibition_reason)
    pm = get_dbus_object()
    lock = pm.Inhibit(APP_NAME, 0, 'Do not suspend while downloading a torrent or serving files thru NFS', 4);
    inhibited = True


def un_inhibit():
    global lock
    global inhibited

    if not inhibited:
        return
    notify("Suspend uninhibited")
    pm = get_dbus_object()
    pm.Uninhibit(lock)
    inhibited = False


def get_dbus_object():
    bus = dbus.SessionBus()
    proxy_object = bus.get_object('org.gnome.SessionManager', '/org/gnome/SessionManager')
    pm = dbus.Interface(proxy_object, 'org.gnome.SessionManager')
    return pm


while True:
    check_suspend()


