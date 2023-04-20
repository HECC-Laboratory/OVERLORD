def CheckPressures(RefCondPressure, RefPressureLimit, RefVesselPressure, CO2PressureLimit, BoostedCO2Pressure, Faulted, RelayCMD):
    global OverPressure_Alarm
  
    if (RefCondPressure > RefPressureLimit or RefVesselPressure > RefPressureLimit or BoostedCO2Pressure > CO2PressureLimit):
        RelayCMD ='OPEN'
        OverPressure_Alarm = True
        Faulted = True
    elif (RefCondPressure <= RefPressureLimit and RefVesselPressure <= RefPressureLimit and BoostedCO2Pressure <= CO2PressureLimit):
        OverPressure_Alarm = False
    
    return Faulted, OverPressure_Alarm, RelayCMD