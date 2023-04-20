def StartThreadedRoutines():
    import threading
    import socket
    
    ExhaustFan_monitor = threading.Thread(target=CheckExhaustFan)
    ExhaustFan_monitor.start()
    
def CheckExhaustFan():
    while 1:
        print("ExhautFanCheck")
        if '-ON' in str(ExhaustFanCmd):
           ExhaustFan(1)
        elif 'OFF' in str(ExhaustFanCmd) and O2_Alarm == 0:
           ExhaustFan(0)
        sleep(1)