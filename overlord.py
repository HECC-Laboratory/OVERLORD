import RPi.GPIO as GPIO            # import RPi.GPIO module  
from time import sleep             # lets us have a delay
import sys, time
from sys import stdout
from daqhats import hat_list, HatIDs, mcc118, mcc134, HatError, TcTypes, mcc152, OptionFlags
import os.path, socket, threading, os, sys, select
import numpy as arr
import struct
import json, threading
import socket, multiprocessing
from StartThreadedRoutines import StartThreadedRoutines
#from ExhaustFanCheck import CheckExhaustFan
from ListenForO2Sensor import ListenForO2Sensor
from CheckPressures import CheckPressures
from CheckTemps import CheckTemps
#from RecieveSettings import RecieveSettings

# Import the module for controlling the stepper motor
from MoveStepper import MoveStepper

  

#Some initial conditions
Cutoff_Temperature = 60
RefPressureLimit = 150 #psia
CO2PressureLimit = 2100 #psia
RefCondPressure = 0
RefVesselPressure = 0
RefVesselTemp = 0
CO2SupplyTemp = 0
CO2RecoveryTemp = 0
CO2SupplyPressure = 0
CO2RecoveryPressure = 0
BoostedCO2Pressure = 0
HaskelInletPressure = 0
O2_Alarm = 0
RequestedState = 0
Faulted = False
CurrentState = 'STARTUP'
global ExhaustFanCmd
ExhaustFanCMD = 'OFF'
ExhaustFan_State = 'OFF'
RelayCMD = 'OPEN'
samples = 0
ExVCurrentPosition = 0
ExVPosition = 0
iterationStart = 0
Heater1_Temp = 0
Heater2_Temp = 0
relay = 'OFF'
RelayState = 'OFF'
FirstConnect = False
Temperature_Alarm = False
OverPressure_Alarm = False
Connected = False


#EZDriver pins: 
Enable_Pin = 7
Direction_Pin = 15
Step_Pin = 18
ExVPosition_Pin = 0

#other input and output pins

ExhaustFanRelay_Pin = 10 #pin number for the exuast fan relay

O2Sensor_Pin = 5 #pin number for the O2 Sensor
HeaterRelays_Pin = 19 #pin for the heater relays

#GPIO setup
GPIO.setmode(GPIO.BOARD)             # choose BCM or BOARD
GPIO.setwarnings(False)
GPIO.setup(ExhaustFanRelay_Pin, GPIO.OUT)
GPIO.setup(O2Sensor_Pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) #use a pull down to keep it low unless voltage is applied from sensor
GPIO.setmode(GPIO.BOARD)             # choose BCM or BOARD
GPIO.setwarnings(False)
GPIO.add_event_detect(O2Sensor_Pin, GPIO.RISING, callback=ListenForO2Sensor,bouncetime=200)
GPIO.setup(HeaterRelays_Pin, GPIO.OUT)
GPIO.output(ExhaustFanRelay_Pin, 0)

#pin setup for stepper driver
GPIO.setup(Enable_Pin, GPIO.OUT)
GPIO.setup(Step_Pin, GPIO.OUT)
GPIO.setup(Direction_Pin, GPIO.OUT)
GPIO.output(Enable_Pin, 1) #enable is off when high

#thermocouple input setup
hat = mcc134(1) #The card in position 1
tc_type = TcTypes.TYPE_K

#probably a better way to do this...
hat.tc_type_write(0, tc_type)
hat.tc_type_write(1, tc_type)

#method to read mcc118 voltage
def getVoltage(port):
    totalVoltage = 0
    for x in range(0, 10): #take 10 measurements rapidly
        voltage = mcc118(0).a_in_read(int(port))
        totalVoltage += voltage

    voltage = totalVoltage / 10 #average the 10 measuremetns and only report the average.
    return voltage


#method to rotate EXV stepper
def MoveExV(steps):
    Move_ExV.MoveStepper(steps) #calls the threaded method


#method to read temperature from thermocouples
def thermocoupleTemp(channel):
    temp = hat.t_in_read(int(channel))
    return temp

                
def truncate(f, n):
    '''Truncates/pads a float f to n decimal places without rounding'''
    s = '{}'.format(f)
    if 'e' in s or 'E' in s:
        return '{0:.{1}f}'.format(f, n)
    i, p, d = s.partition('.')
    return '.'.join([i, (d+'0'*n)[:n]])

def TruncAndFillT(variable):
    variable = truncate(variable, 2)
    variable = variable.zfill(6)
    variable = variable.encode()
    return variable

def TruncAndFillExV(variable):
    variable = truncate(variable, 0)
    variable = variable.zfill(5)
    variable = variable.encode()
    return variable


def Calculate_ExV_Position():
    global ExVCurrentPosition
    global ExVCommand
    global ExVPosition
    global debug
    
    ExVCommand = 20*ExVPositionPercent #20,000 steps on this particular stepper - this will change based on the exv
    motor_thread = threading.Thread(target=MoveStepper, args=(Enable_Pin, Step_Pin, Direction_Pin, ExVCurrentPosition,ExVCommand,))
    motor_thread.start()
    ExVCurrentPosition = ExVCommand
    ExVPosition = ExVCurrentPosition/20 #20,000 again

def INITIALIZE(): #is run the first time to start the EXV at zero
    global ExVCurrentPosition
    global oldPos
    
    #runs EXV closed all the way and resets position
    GPIO.output(Enable_Pin, 0)
    GPIO.output(Direction_Pin, 1)
    for x in range(0,  25000): #more than 20,000 to make sure it's definitely closed - stepper will just bounce against the farthest it can move
        GPIO.output(Step_Pin, 1)
        sleep(0.0000051)
        GPIO.output(Step_Pin, 0)
        sleep(0.0000051)
    
    GPIO.output(Enable_Pin, 1)
    ExVCurrentPosition = 0
    oldPos = 0
    
def RecieveSettings(TCPMessage):
    
    global RefVesselPressure 
    global RefCondPressure
    global RefVesselTemp
    global CO2SupplyTemp
    global CO2RecoveryTemp
    global CO2SupplyPressure
    global CO2RecoveryPressure
    global BoostedCO2Pressure
    global HaskelInletPressure
    global ExVPositionPercent
    global ExhaustFanCMD
    global RequestedState
    #global TCPMessage
    global Connected
    
    try:
        RequestedState = TCPMessage[0]
        RefVesselPressure_b= TCPMessage[1] #grabs the next *4 bits out of the TCP command
        RefVesselPressure = float(RefVesselPressure_b) /10 #converts it from the format on the excel doc to a decimal number
        
        RefCondPressure_b = TCPMessage[2]
        RefCondPressure = float(RefCondPressure_b)/ 10
        
        RefVesselTemp_b = TCPMessage[3]
        RefVesselTemp = float(RefVesselTemp_b) /10
        
        CO2SupplyTemp_b = TCPMessage[4]
        CO2SupplyTemp = float(CO2SupplyTemp_b) /10
        
        CO2RecoveryTemp_b = TCPMessage[5]
        CO2RecoveryTemp =float(CO2RecoveryTemp_b) /10
      
        CO2SupplyPressure_b = TCPMessage[6]
        CO2SupplyPressure= float(CO2SupplyPressure_b) 
        
        CO2RecoveryPressure_b = TCPMessage[7]
        CO2RecoveryPressure = float(CO2RecoveryPressure_b)
        
        BoostedCO2Pressure_b = TCPMessage[8]
        BoostedCO2Pressure = float(BoostedCO2Pressure_b)
        
        HaskelInletPressure_b = TCPMessage[9]
        HaskelInletPressure = float(HaskelInletPressure_b) /10
        
        ExVPosition_b = TCPMessage[10]
        ExVPositionPercent = float(ExVPosition_b) /10
        
       
        ExhaustFanCMD = str(TCPMessage[11])
        Send_Data()
    except:
        print("LabVIEW disconnected")
        RequestedState = 'IDLE'
        Connected = False
        s.close()
        sleep(3)
        ConnectTCP()
    
def Send_Data():
    Overlord_State = CurrentState
    Heater1_Data = TruncAndFillT(Heater1_Temp)
    Heater2_Data = TruncAndFillT(Heater2_Temp)
    Relay_State = relay
    ExV = TruncAndFillExV(ExVPosition)
    conn.send(Overlord_State.encode())
    conn.send(b'EX')
    conn.send(ExhaustFan_State.encode())          
    conn.send(b'H1')
    conn.send(Heater1_Data)
    conn.send(b'H2')
    conn.send(Heater2_Data)
    conn.send(b'RE')
    conn.send(Relay_State.encode())
    conn.send(b'EXV')
    conn.send(ExV)
    conn.send(b'\r\n')
   
##Open the heater relays when there is a problem        
def OpenRelays():
    global RelayStatus

    GPIO.output(HeaterRelays_Pin, 0)
    RelayStatus = 'OPEN'

##close the heater relays when things are OK
def CloseRelays():
    global RelayStatus
    
    GPIO.output(HeaterRelays_Pin, 1)
    RelayStatus = 'CLSD'

def RelayMonitor():
    while 1:

        if 'CLSE' in str(RelayCMD):
            CloseRelays()
        elif 'OPEN' in str(RelayCMD):
            OpenRelays()
        sleep(0.1)
        
def CheckExhaustFan():
   
    while 1:
        
        if 'ON' in str(ExhaustFanCMD):
           ExhaustFan(ExhaustFanRelay_Pin, 1)
        elif 'OFF' in str(ExhaustFanCMD) and O2_Alarm == False:
           ExhaustFan(ExhaustFanRelay_Pin, 0)
        sleep(1)
    
def ExhaustFan(ExhaustFanRelay_Pin, state):
    global ExhaustFan_State
    
    GPIO.output(ExhaustFanRelay_Pin, state)
    if (state == 1):
        ExhaustFan_State = 'ON'
    elif (state == 0):
        ExhaustFan_State = 'OFF'

def ConnectTCP():
    global conn
    global Connected
    global FirstConnect
    global sock
    global RequestedState
   
     #### THIS PART IS NEEDED TO CONNECT TO TCP/IP####
    HOST = '0.0.0.0' # The remote host - windows machine running the LabVIEW Server
    PORT = 2055 # The same port as used by the server - defined in LabVIEW
    buffer_size = 56
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, buffer_size)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.settimeout(2)
    sock.bind(('', PORT))
    try:
            
            sock.listen()
            conn, addr = sock.accept()
            Connected = True
            FirstConnect = True
            print("connected to LabIEW from:" + str(addr))
    except:
            print("Waiting for LabIEW to connect")
            sock.close()
            sleep(3)
            Connected = False
            ConnectTCP()
            pass
    return sock
    

##Listen for a tCP/IP command
def ListenForCommand():
    global RequestedState
    global TCPMessage
    global Connected
    global sock
    
    ConnectTCP()
    while 1:
        
         try:
            if (Connected):
                bits = conn.recv(2)
                if not bits:
                    Connected = False
                    RequestedState = 'IDLE'
                    print("Labview quit")
                    sock.shutdown(socket.SHUT_RDWR)
                    sleep(3)
                    sock.close()
                    sleep(3)
                    ConnectTCP()
                if (Connected) and (bits):
                    bits = int(bits)
                    msg = conn.recv(bits).decode('ascii')
                    TCPMessage = msg.split(',')
                    #print(TCPMessage)
                    sleep(.5)
                    RecieveSettings(TCPMessage)
            else:
                print("trying to reconnect to LabIEW")
                RequestedState = 'IDLE'
                sock.shutdown(socket.SHUT_RDWR)
                sleep(3)
                sock.close()
                sleep(3)
                ConnectTCP()

                
         except:
            Connected = False
            print("no TCP/IP connection is active")
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()
            sleep(3)
            print(exception)
            RequestedState = 'IDLE'
            ConnectTCP()

        
#Start the TCP/IP thread in the background

command_listener = threading.Thread(target=ListenForCommand)
command_listener.start()

 #listen for O2 Sensor in an interrupt
#o2_listener = threading.Thread(target=ListenForO2Sensor, args=(O2Sensor_Pin, ExhaustFanRelay_Pin,))
#o2_listener.start()

#Start the pressure monitor in a thread
pressure_monitor = threading.Thread(target=CheckPressures, args=(RefCondPressure, RefPressureLimit, RefVesselPressure, CO2PressureLimit, BoostedCO2Pressure, Faulted, RelayCMD,))
pressure_monitor.start()


ExhaustFan_monitor = threading.Thread(target=CheckExhaustFan, args=())
ExhaustFan_monitor.start()

Temp_monitor = threading.Thread(target=CheckTemps, args=(Temperature_Alarm, Faulted, RelayCMD,))
Temp_monitor.start

relay_state = threading.Thread(target=RelayMonitor)
relay_state.start()

while 1:
    try:
       
        if (not FirstConnect):
            print ("experiment is ready to initialize")
            sleep(5)
            
        if 'REST' in str(RequestedState): #RESET Requested Clear Faults and Initialize ExV
            CurrentState = 'RESETTING'
            Faulted = False
            O2_Alarm = False
            Temperature_Alarm = False
            Overpressure_Alarm = False
            sleep(5)
            
        elif 'INIT' in str(RequestedState):
            FirstConnect=True
            INITIALIZE()
            CurrentState = 'INIT-DONE'
            
            
        elif 'HEAT' in str(RequestedState): #Operate Experiment normally, close heater relays
            if (Faulted):
               CurrentState = 'FALT'
    
            elif (not Faulted):    
                CurrentState = 'HEAT-MODE'
                Calculate_ExV_Position()
                RelayCMD = 'CLSE'
                

        elif 'IDLE' in str(RequestedState): #Experiment is idle and waiting for an updated state, relays open
                CurrentState = 'IDLE-MODE'
                if (Faulted):
                   CurrentState = 'FALT'
               
            
        s = f"""
            #{'-'*60}
            # OVERLORD State                            {CurrentState}
            # LabVIEW Connected:                        {Connected}
            # OverPressure Alarm:                       {OverPressure_Alarm}
            # Temperature Alarm:                        {Temperature_Alarm}
            # Heater Relay Status:                      {RelayStatus}
            # Exhaust Fan Command:                      {ExhaustFanCMD}
            # Exhaust Fan State:                        {ExhaustFan_State}
            # Heater Temps:                             {Heater1_Temp, Heater2_Temp}
            # CondenserPressure:                        {'{:12.1f}'.format(RefCondPressure)} psia
            # Refrigerant Vessel Pressure:              {'{:12.1f}'.format(RefVesselPressure)} psia
            # Refrigerant Vessel Temperature:           {'{:12.1f}'.format(RefVesselTemp)} psia
            # CO2 Supply Tank Temperature:              {'{:12.1f}'.format(CO2SupplyTemp)} psia
            # CO2 Supply Tank Pressure:                 {'{:12.1f}'.format(CO2SupplyPressure)} psia
            # CO2 Recovery Tank Temperature:            {'{:12.1f}'.format(CO2RecoveryTemp)} psia
            # CO2 Recovery Tank Pressure:               {'{:12.1f}'.format(CO2RecoveryPressure)} psia
            # Boosted CO2 Pressure:                     {'{:12.1f}'.format(BoostedCO2Pressure)} psia
            # Haskel Air Pressure:                      {'{:12.1f}'.format(HaskelInletPressure)} psia
            #{'-'*60}
            #"""

        print(s)
        sleep(.5)
    except:
        print(exception)
        pass
   
    
    
stdout.flush()


