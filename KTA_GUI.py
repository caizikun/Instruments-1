#!/usr/bin/env python
# pylint: disable=R0901
# pylint: disable=C0103
# pylint: disable=R0904
# pylint: disable=R0924
# pylint: disable=F0401

import Tkinter as tk
import tkMessageBox
import test_station.test_fixture.instruments.serial as serial

from test_station.test_fixture.instruments.kta_223 import KTA223


DID_READ_CONFIG = False
import sys
sys.path.append("c:/square/s1-factory-test")    # flex S1
sys.path.append("c:/square/factory-test")   # foxlink PT
sys.path.append("d:/square/factory-test")  # foxlink FT and beyond
try:
    import station_config
    DID_READ_CONFIG = True
except SystemError as the_exception:
    TITLE = "Station Config Error"
    MESSAGE = ("File station_config.py not found:\n---\n%s\n---\nWill open using hard-coded defaults."
               % str(the_exception))
    tkMessageBox.showerror(title=TITLE, message=MESSAGE)


ENABLE_KTA = 1
STATION = 'R4PT'
if DID_READ_CONFIG:
    STATION = station_config.station_type
KTA_COM_PORT = None
if DID_READ_CONFIG:
    KTA_COM_PORT = station_config.kta_com_port

REL_LBL_1 = "1"
REL_LBL_2 = "2"
REL_LBL_3 = "3"
REL_LBL_4 = "4"
REL_LBL_5 = "5"
REL_LBL_6 = "6"
REL_LBL_7 = "7"
REL_LBL_8 = "8"

if STATION is 'QST':
    if KTA_COM_PORT is None:    # since we only have one copy of each station, default is safe guess.
        KTA_COM_PORT = 6
    REL_LBL_1 = "ACC_PWR (3V3)"
    REL_LBL_3 = "12V"
    REL_LBL_2 = "VBUS LOAD"

if STATION is 'FCT':
    if KTA_COM_PORT is None:    # since we only have one copy of each station, default is safe guess.
        KTA_COM_PORT = 8
    REL_LBL_1 = "ACC_PWR (3V3)"
    REL_LBL_2 = "12V"
    REL_LBL_8 = "VBUS LOAD"

if STATION is 'R4PT':
    if KTA_COM_PORT is None:    # since we only have one copy of each station, default is safe guess.
        KTA_COM_PORT = 3
    REL_LBL_1 = "ON=MIC\nOFF=VBATT"
    REL_LBL_3 = "TESTING LED"
    REL_LBL_5 = "SSEL"
    REL_LBL_6 = "MISO"
    REL_LBL_7 = "SCLK"
    REL_LBL_8 = "MOSI"

if STATION is 'R4FT':
    if KTA_COM_PORT is None:    # since we only have one copy of each station, default is safe guess.
        KTA_COM_PORT = 3
    REL_LBL_1 = "DMM: \n0=LA\n1=RA"
    REL_LBL_2 = "DMM com: \n0=V/Ohm\n1=I"
    REL_LBL_3 = "PWR\nturn DMMCOM ON FIRST!"
    REL_LBL_4 = "ACTIVATE SWIPE"

if STATION is 'LAB':
    KTA_COM_PORT = 7
    REL_LBL_1 = "ACC_PWR (3V3)"
    REL_LBL_2 = "12V"
    REL_LBL_8 = "VBUS LOAD"


class StatusConsoleText(tk.Text):

    def Print(self, msg):
        self.config(state='normal')
        self.insert(tk.END, msg)
        self.see(tk.END)
        self.config(state='disabled')

    def SetBG(self, color):
        self.config(state='normal')
        self.config(bg=color)
        self.config(state='disabled')

    def Clear(self):
        self.config(state='normal')
        self.delete("1.0", tk.END)
        self.config(state='disabled')


def onAppExit():
    if not KTA is None:
        SetInitialRelayState()
        try:
            KTA.close()
        except serial.SerialException:
            root.destroy()

    root.destroy()


def OnBtn():
    print "button pushed"


def OnBtnAnInRead():
    ReadAndDisplayAnalogInValue(0)


def OnBtnRead_VBUS():
    ReadAndDisplayAnalogInValue(1)


def OnBtnRead_ACC_ID():
    ReadAndDisplayAnalogInValue(2)


def OnBtnRead_ACC_DET():
    ReadAndDisplayAnalogInValue(3)


def OnBtnDigInRead():
    ReadAndDisplayDigitalInValue("all")


def ReadAndDisplayAnalogInValue(channel):
    cons.Print("Read Analog Inputs:\n")
    ret = KTA.get_analogin_val_volts(channel)
    cons.Print("    %s\n" % ret)
    anValues.config(text=("%s" % ret))


def ReadAndDisplayDigitalInValue(channel):
    cons.Print("Read Digital Inputs:\n")
    ret = KTA.get_digital_in_status(channel)
    cons.Print("    %s\n" % ret)


def OnBtnR1():
    ToggleRelay(1, b1)


def OnBtnR2():
    ToggleRelay(2, b2)


def OnBtnR3():
    ToggleRelay(3, b3)


def OnBtnR4():
    ToggleRelay(4, b4)


def OnBtnR5():
    ToggleRelay(5, b5)


def OnBtnR6():
    ToggleRelay(6, b6)


def OnBtnR7():
    ToggleRelay(7, b7)


def OnBtnR8():
    ToggleRelay(8, b8)


def OnAllOff():
    cons.Print("Turning ALL relays Off...\n")
    KTA.turn_relay_off(0)
    SetRelayBtnColors(defaultBgColor)


def OnAllOn():
    cons.Print("Turning ALL relays On...\n")
    KTA.turn_relay_on(0)
    SetRelayBtnColors("grey")


def SetRelayBtnColors(color):
    b1.config(bg=color)
    b2.config(bg=color)
    b3.config(bg=color)
    b4.config(bg=color)
    b5.config(bg=color)
    b6.config(bg=color)
    b7.config(bg=color)
    b8.config(bg=color)


def ToggleRelay(channel, button):
    cons.Print("Toggle Relay %d:\n" % channel)
    stat = KTA.get_relay_status(channel)
    cons.Print("   initial state = %s\n" % stat)

    if stat == '1':
        cons.Print("   Turning Off...\n")
        KTA.turn_relay_off(channel)
        button.config(bg=defaultBgColor)
    else:
        cons.Print("   Turning On...\n")
        KTA.turn_relay_on(channel)
        button.config(bg="grey")


def SetInitialRelayState():
    if not KTA is None:
        KTA.set_relays_as_byte(0)

COMMON_FONT = "verdana 12"

root = tk.Tk()
root.title("KTA Debugger: %s station, COM%d" % (STATION, KTA_COM_PORT))
defaultBgColor = root.cget("bg")

# ROOT grid #
relayFrame = tk.Frame(root, bd=3)
relayFrame.grid(column=1, row=1)
anInFrame = tk.Frame(root, bd=3)
anInFrame.grid(column=2, row=1)
digInFrame = tk.Frame(root, bd=3)
digInFrame.grid(column=3, row=1)
cons = StatusConsoleText(root, font=COMMON_FONT, relief='sunken', bd=5, state='disabled')
cons.grid(column=1, row=2, columnspan=3)
cons.config(state='disabled')

# relay grid #
relayTitle = tk.Label(relayFrame, font=COMMON_FONT, text="Relays")
relayTitle.grid(row=1, column=1, columnspan=2)
b1 = tk.Button(relayFrame, font=COMMON_FONT, text=REL_LBL_1, command=OnBtnR1, width=10)
b1.grid(row=2, column=1)
b2 = tk.Button(relayFrame, font=COMMON_FONT, text=REL_LBL_2, command=OnBtnR2, width=10)
b2.grid(row=3, column=1)
b3 = tk.Button(relayFrame, font=COMMON_FONT, text=REL_LBL_3, command=OnBtnR3, width=10)
b3.grid(row=4, column=1)
b4 = tk.Button(relayFrame, font=COMMON_FONT, text=REL_LBL_4, command=OnBtnR4, width=10)
b4.grid(row=5, column=1)
b5 = tk.Button(relayFrame, font=COMMON_FONT, text=REL_LBL_5, command=OnBtnR5, width=10)
b5.grid(row=2, column=2)
b6 = tk.Button(relayFrame, font=COMMON_FONT, text=REL_LBL_6, command=OnBtnR6, width=10)
b6.grid(row=3, column=2)
b7 = tk.Button(relayFrame, font=COMMON_FONT, text=REL_LBL_7, command=OnBtnR7, width=10)
b7.grid(row=4, column=2)
b8 = tk.Button(relayFrame, font=COMMON_FONT, text=REL_LBL_8, command=OnBtnR8, width=10)
b8.grid(row=5, column=2)
allOff = tk.Button(relayFrame, font=COMMON_FONT, text="ALL OFF", command=OnAllOff, width=10)
allOff.grid(row=5, column=3)
allOn = tk.Button(relayFrame, font=COMMON_FONT, text="ALL ON", command=OnAllOn, width=10)
allOn.grid(row=2, column=3)

#analog inputs grid#
anTitle = tk.Label(anInFrame, font=COMMON_FONT, text="Analog Inputs")
anTitle.grid(column=1, row=1, columnspan=4)
anReadBtn = tk.Button(anInFrame, font=COMMON_FONT, text="All", command=OnBtnAnInRead)
anReadBtn.grid(column=1, row=2)
anReadBtn = tk.Button(anInFrame, font=COMMON_FONT, text="1 VBUS", command=OnBtnRead_VBUS)
anReadBtn.grid(column=2, row=2)
anReadBtn = tk.Button(anInFrame, font=COMMON_FONT, text="2 ACC_ID", command=OnBtnRead_ACC_ID)
anReadBtn.grid(column=3, row=2)
anReadBtn = tk.Button(anInFrame, font=COMMON_FONT, text="3 ACC_DET", command=OnBtnRead_ACC_DET)
anReadBtn.grid(column=4, row=2)
anValues = tk.Label(anInFrame, font=COMMON_FONT)
anValues.grid(column=1, row=3, columnspan=4)

# digital inputs
digTitle = tk.Label(digInFrame, font=COMMON_FONT, text="Digital Inputs")
digTitle.grid(column=1, row=1)
digReadBtn = tk.Button(digInFrame, font=COMMON_FONT, text="All", command=OnBtnDigInRead)
digReadBtn.grid(column=1, row=2)

# make the KTA control a global
KTA = None
if ENABLE_KTA:
    try:
        KTA = KTA223('COM%d' % KTA_COM_PORT)
        KTA.enable_debug()
    except serial.SerialException:
        cons.Print("Unable to connect to relay box on COM%d.  Please consult test engineer.\n" % KTA_COM_PORT)
        cons.SetBG("yellow")

# register an onExit handler to close out the KTA
root.wm_protocol("WM_DELETE_WINDOW", onAppExit)

tk.mainloop()
