def MoveStepper(Enable, Step, Direction, ExVCurrentPosition, steps):
    import RPi.GPIO as GPIO
    from time import sleep
    GPIO.output(Enable, 0)
    steps = int(steps)
    
    if (steps > ExVCurrentPosition):
        GPIO.output(Direction, 0)
        while (steps > ExVCurrentPosition):
            GPIO.output(Step, 1)
            sleep(0.00000005)
            GPIO.output(Step, 0)
            sleep(0.000005)
            ExVCurrentPosition += 1
    elif (steps < ExVCurrentPosition):
        GPIO.output(Direction, 1)
        while (steps < ExVCurrentPosition):
            GPIO.output(Step, 1)
            sleep(0.00000005)
            GPIO.output(Step, 0)
            sleep(0.000005)
            ExVCurrentPosition -= 1
    GPIO.output(Enable, 1)
    return ExVCurrentPosition