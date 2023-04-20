def CheckTemps(Temperature_Alarm, Faulted, RelayCMD):
    from OVERLORD import ThermocoupleTemp
    
    while 1:
        Heater1_Temp = thermocoupleTemp(1)
        Heater2_Temp = thermocoupleTemp(2)
        if (Heater1_Temp > Cutoff_Temperature or Heater2_Temp > Cutoff_Temperature):
            
            Temperature_Alarm = 1
            Faulted = True
            RelayCMD = 'OPEN'
        elif (Heater1_Temp <= Cutoff_Temperature and Heater2_Temp <= Cutoff_Temperature and 'HEAT' in str(RequestedState)):
            Temperature_Alarm = False
            RelayCMD = 'CLSD'
        sleep (1)
    return Heater1_Temp, Heater2_Temp, Temperature_Alarm, Faulted, RelayCMD    
