def ListenForO2Sensor(O2Sensor_Pin, ExhaustFanRelay_Pin):
    from ExhaustFan import ExhaustFan
    
    global O2_Alarm
    global Faulted
    global RelayCMD
    
    
#meant to act like an interrupt.  I don't know how it resets after it does a cleanup
    RelayCMD = 'OPEN'
    ExhaustFan(ExhaustFanRelay_Pin, 1)
    Faulted = True
    O2_Alarm = True
    return O2_Alarm, Faulted