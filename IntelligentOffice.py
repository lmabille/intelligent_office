import time

from IntelligentOfficeError import IntelligentOfficeError
import mock.GPIO as GPIO
from mock.RTC import RTC


class IntelligentOffice:
    # Pin number definition
    INFRARED_PIN_1 = 11
    INFRARED_PIN_2 = 12
    INFRARED_PIN_3 = 13
    INFRARED_PIN_4 = 15
    RTC_PIN = 16
    SERVO_PIN = 18
    PHOTO_PIN = 22  # photoresistor
    LED_PIN = 29
    CO2_PIN = 31
    FAN_PIN = 32

    LUX_MIN = 500
    LUX_MAX = 550

    CO2_MIN = 500
    CO2_MAX = 800

    PUD_OFF = 20
    PUD_UP = 22

    def __init__(self):
        """
        Constructor
        """
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        GPIO.setup(self.INFRARED_PIN_1, GPIO.IN)
        GPIO.setup(self.INFRARED_PIN_2, GPIO.IN)
        GPIO.setup(self.INFRARED_PIN_3, GPIO.IN)
        GPIO.setup(self.INFRARED_PIN_4, GPIO.IN)
        GPIO.setup(self.PHOTO_PIN, GPIO.IN)
        GPIO.setup(self.SERVO_PIN, GPIO.OUT)
        GPIO.setup(self.LED_PIN, GPIO.OUT)
        GPIO.setup(self.CO2_PIN, GPIO.IN)
        GPIO.setup(self.FAN_PIN, GPIO.OUT)

        self.rtc = RTC(self.RTC_PIN)
        self.pwm = GPIO.PWM(self.SERVO_PIN, 50)
        self.pwm.start(0)

        self.blinds_open = False
        self.light_on = False
        self.fan_switch_on = False

    def check_quadrant_occupancy(self, pin: int) -> bool:
        """
        Checks whether one of the infrared distance sensor on the ceiling detects something in front of it.
        :param pin: The data pin of the sensor that is being checked (e.g., INFRARED_PIN1).
        :return: True if the infrared sensor detects something, False otherwise.
        """

        if pin not in [self.INFRARED_PIN_1, self.INFRARED_PIN_2, self.INFRARED_PIN_3, self.INFRARED_PIN_4]:

            raise IntelligentOfficeError

        if GPIO.input(pin) > 0:
            return True

        return False

    def open_blinds(self) -> None:
        """
        Opens the window using the servo motor
        A motor angle of 180 degrees corresponds to a fully open door
        """
        duty_cycle = (180 / 18) + 2
        self.change_servo_angle(duty_cycle)
        self.blinds_open = 'OPENED'

    def close_blinds(self) -> None:
        """
        Closes the window door using the servo motor
        A motor angle of 0 degrees corresponds to a fully closed door
        """
        duty_cycle = (0 / 180) + 2
        self.change_servo_angle(duty_cycle)
        self.blinds_open = 'CLOSED'

    def manage_blinds_based_on_time(self) -> None:
        """
        Uses the RTC and servo motor to open/close the blinds based on current time and day.
        The system fully opens the blinds at 8:00 and fully closes them at 20:00
        each day except for Saturday and Sunday.
        """

        time_now = self.rtc.get_current_time_string()
        day = self.rtc.get_current_day()

        hour_now = int(time_now[0] + time_now[1])

        if hour_now > 8 and hour_now < 20 and day not in ['SATURDAY', 'SUNDAY'] and self.blinds_open != 'OPENED':
            self.open_blinds()
        elif self.blinds_open != 'CLOSED':
            self.close_blinds()

    def turn_light_on(self) -> None:
        """
        Turns on the smart lightbulb
        """
        GPIO.output(self.LED_PIN, True)
        self.light_on = True


    def turn_light_off(self) -> None:
        """
        Turns off the smart lightbulb
        """
        GPIO.output(self.LED_PIN, False)
        self.light_on = False

    def manage_based_on_photoresistor(self) -> None:
        if GPIO.input(self.PHOTO_PIN) < self.LUX_MIN:
            self.turn_light_on()
        elif GPIO.input(self.PHOTO_PIN) > self.LUX_MAX:
            self.turn_light_off()

    def get_occupied_quadrants(self) -> int:
        """
        Calculates the number of occupied quadrants in the office.
        :return: The number of occupied quadrants.
        """
        occupied_cadrants = 0
        for pin in [self.INFRARED_PIN_1, self.INFRARED_PIN_2, self.INFRARED_PIN_3, self.INFRARED_PIN_4]:
            if self.check_quadrant_occupancy(pin):
                occupied_cadrants += 1

        return occupied_cadrants

    def manage_light_level(self) -> None:
        """
        Tries to maintain the actual light level inside the office, measure by the photoresitor,
        between LUX_MIN and LUX_MAX.
        If the actual light level is lower than LUX_MIN the system turns on the smart light bulb.
        On the other hand, if the actual light level is greater than LUX_MAX, the system turns off the smart light bulb.

        Furthermore, When the last worker leaves the office (i.e., the office is now vacant), the intelligent office system 
        stops regulating the light level in the office and then turns off the smart light bulb. 
        When the first worker goes back into the office, the system resumes regulating the light level
        """

        if self.get_occupied_quadrants() == 0:
            GPIO.setup(self.PHOTO_PIN, GPIO.IN, pull_up_down=self.PUD_OFF)
            self.turn_light_off()
        else:
            GPIO.setup(self.PHOTO_PIN, GPIO.IN, 490, self.PUD_UP)
            self.manage_based_on_photoresistor()



    def turn_fan_on(self) -> None:
        """
        Turns on the exhaust fan
        """
        GPIO.output(self.FAN_PIN, True)
        self.fan_switch_on = True


    def turn_fan_off(self) -> None:
        """
        Turns off the exhaust fan
        """
        GPIO.output(self.FAN_PIN, False)
        self.fan_switch_on = False


    def monitor_air_quality(self) -> None:
        """
        Use the carbon dioxide sensor to monitor the level of CO2 in the office.
        If the amount of detected CO2 is greater than or equal to 800 PPM, the system turns on the
        switch of the exhaust fan until the amount of CO2 is lower than 500 PPM.
        """
        if GPIO.input(self.CO2_PIN) < self.CO2_MIN:
            self.turn_fan_off()
        elif GPIO.input(self.CO2_PIN) > self.CO2_MAX:
            self.turn_fan_on()

    def change_servo_angle(self, duty_cycle: float) -> None:
        """
        Changes the servo motor's angle by passing to it the corresponding PWM duty cycle signal
        :param duty_cycle: the length of the duty cycle
        """
        GPIO.output(self.SERVO_PIN, GPIO.HIGH)
        self.pwm.ChangeDutyCycle(duty_cycle)
        time.sleep(1)
        GPIO.output(self.SERVO_PIN, GPIO.LOW)
        self.pwm.ChangeDutyCycle(0)
