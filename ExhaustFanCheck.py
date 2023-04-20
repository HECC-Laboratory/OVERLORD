def CheckExhaustFan(ExhaustFanRelay_Pin, ExhaustFanCMD, O2_Alarm):
    from ExhaustFan import ExhaustFan
    from time import sleep
    global ExhaustFan
    
    while 1:
        
        if 'ON' in str(ExhaustFanCMD):
           ExhaustFan(ExhaustFanRelay_Pin, 1)
           print("exhaust fan on")
        elif 'OFF' in str(ExhaustFanCMD) and O2_Alarm == False:
           ExhaustFan(ExhaustFanRelay_Pin, 0)
           print("exhaust Fan off")
           print(ExhaustFanCMD)
        sleep(.1)
    return ExhaustFan