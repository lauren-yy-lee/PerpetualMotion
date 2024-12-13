# ////////////////////////////////////////////////////////////////
# //                     IMPORT STATEMENTS                      //
# ////////////////////////////////////////////////////////////////
import os
import math
import sys
import time
import threading

from jedi.debug import speed

os.environ["DISPLAY"] = ":0.0"

from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import *
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.slider import Slider
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.clock import Clock
from kivy.animation import Animation
from functools import partial
from kivy.config import Config
from kivy.core.window import Window
from pidev.kivy import DPEAButton
from pidev.kivy import PauseScreen
from time import sleep
from dpeaDPi.DPiComputer import *
from dpeaDPi.DPiStepper import *
from datetime import datetime

# ////////////////////////////////////////////////////////////////
# //                     HARDWARE SETUP                         //
# ////////////////////////////////////////////////////////////////
"""Stepper Motor goes into MOTOR 0 )
    Limit Switch associated with Stepper Motor goes into HOME 0
    One Sensor goes into IN 0
    Another Sensor goes into IN 1
    Servo Motor associated with the Gate goes into SERVO 1
    Motor Controller for DC Motor associated with the Stairs goes into SERVO 0"""

# ////////////////////////////////////////////////////////////////
# //                      GLOBAL VARIABLES                      //
# //                         CONSTANTS                          //
# ////////////////////////////////////////////////////////////////
ON = False
OFF = True
HOME = True
TOP = False
OPEN = False
CLOSE = True
YELLOW = .180, 0.188, 0.980, 1
BLUE = 0.917, 0.796, 0.380, 1
DEBOUNCE = 0.1
INIT_RAMP_SPEED = 2
RAMP_LENGTH = 725


# ////////////////////////////////////////////////////////////////
# //            DECLARE APP CLASS AND SCREENMANAGER             //
# //                     LOAD KIVY FILE                         //
# ////////////////////////////////////////////////////////////////
class MyApp(App):
    def build(self):
        self.title = "Perpetual Motion"
        return sm


Builder.load_file('main.kv')
Window.clearcolor = (.1, .1, .1, 1)  # (WHITE)

# ////////////////////////////////////////////////////////////////
# //                    SLUSH/HARDWARE SETUP                    //
# ////////////////////////////////////////////////////////////////
sm = ScreenManager()


# ////////////////////////////////////////////////////////////////
# //                       MAIN FUNCTIONS                       //
# //             SHOULD INTERACT DIRECTLY WITH HARDWARE         //
# ////////////////////////////////////////////////////////////////

# ////////////////////////////////////////////////////////////////
# //        DEFINE MAINSCREEN CLASS THAT KIVY RECOGNIZES        //
# //                                                            //
# //   KIVY UI CAN INTERACT DIRECTLY W/ THE FUNCTIONS DEFINED   //
# //     CORRESPONDS TO BUTTON/SLIDER/WIDGET "on_release"       //
# //                                                            //
# //   SHOULD REFERENCE MAIN FUNCTIONS WITHIN THESE FUNCTIONS   //
# //      SHOULD NOT INTERACT DIRECTLY WITH THE HARDWARE        //
# ////////////////////////////////////////////////////////////////
dpiComputer = DPiComputer()
dpiComputer.initialize()

dpiStepper = DPiStepper()
dpiStepper.setBoardNumber(0)
time = datetime

if dpiStepper.initialize() != True:
    print("Communication with the DPiStepper board failed.")

microstepping = 8
dpiStepper.setMicrostepping(microstepping)

speed_steps_per_second = 200 * microstepping
accel_steps_per_second_per_second = speed_steps_per_second
dpiStepper.setSpeedInStepsPerSecond(0, speed_steps_per_second)
dpiStepper.setAccelerationInStepsPerSecondPerSecond(0, accel_steps_per_second_per_second)

stepperStatus = dpiStepper.getStepperStatus(0)
print(f"Pos = {stepperStatus}")

stepper_num = 0

class MainScreen(Screen):
    staircaseSpeedText = '0'
    rampSpeed = INIT_RAMP_SPEED
    staircaseSpeed = 40
    gate = False
    stair = False

    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.initialize()

    def toggleGate(self):
        print("Open and Close gate here")

    def toggleStaircase(self):
        print("Turn on and off staircase here")

    def toggleRamp(self):
        print("Move ramp up and down here")

    def auto(self):
        dpiStepper.enableMotors(True)
        dpiStepper.moveToHomeInSteps(stepper_num, 1, 8000, 45000)
        self.setRampSpeed()
        dpiStepper.enableMotors(False)
        if dpiComputer.readDigitalIn(dpiComputer.IN_CONNECTOR__IN_0) == 0:
            self.moveRamp()
            self.turnOnStaircase()
            sleep(8)
            self.openGate()
            self.turnOnStaircase()
            sleep(1)
            self.openGate()
            Clock.schedule_interval(self.isBallAtBottomOfRamp,0.05)

    def initialize(self):
        print("Close gate, stop staircase and home ramp here")

    def resetColors(self):
        self.ids.gate.color = YELLOW
        self.ids.staircase.color = YELLOW
        self.ids.ramp.color = YELLOW
        self.ids.auto.color = BLUE

    def quit(self):
        print("Exit")
        MyApp().stop()

    def debounce(self):
        print("what even is debounce haha")

    def openGate(self):
        servo_num = 1
        if not self.gate:
            dpiComputer.writeServo(servo_num, 180)
            self.gate = True
        else:
            dpiComputer.writeServo(servo_num, 0)
            self.gate = False

    def turnOnStaircase(self):
        servo_num = 0
        if not self.stair:
            dpiComputer.writeServo(servo_num, int(90*(self.ids.staircaseSpeed.value/50)+90))
            self.stair = True
        else:
            dpiComputer.writeServo(servo_num, 90)
            self.stair = False

    def moveRamp(self):
        dpiStepper.enableMotors(True)
        dpiStepper.moveToRelativePositionInSteps(stepper_num,-45000, True)
        dpiStepper.moveToRelativePositionInSteps(stepper_num,45000,True)
        dpiStepper.moveToHomeInSteps(stepper_num, 1, 16000, 45000)
        dpiStepper.enableMotors(False)

    def setRampSpeed(self, value=0):
        speed_steps_per_second = 1600*(8*(self.ids.rampSpeed.value/200)+2)
        print(speed_steps_per_second)
        accel_steps_per_second_per_second = speed_steps_per_second
        dpiStepper.setSpeedInStepsPerSecond(stepper_num, speed_steps_per_second)
        dpiStepper.setAccelerationInStepsPerSecondPerSecond(stepper_num, accel_steps_per_second_per_second)

        # global speed_steps_per_second
        # speed_steps_per_second = 1600 * self.ids.rampSpeed.value
        # print(speed_steps_per_second)

    def setStaircaseSpeed(self):
        print("useless")

    def isBallAtBottomOfRamp(self, dt=0):
        if dpiComputer.readDigitalIn(dpiComputer.IN_CONNECTOR__IN_0) == 0:
            Clock.unschedule(self.isBallAtTopOfRamp)
            self.auto()

    def isBallAtTopOfRamp(self):
        print("unnecessary")


sm.add_widget(MainScreen(name='main'))

# ////////////////////////////////////////////////////////////////
# //                          RUN APP                           //
# ////////////////////////////////////////////////////////////////
if __name__ == "__main__":
    # Window.fullscreen = True
    # Window.maximize()
    MyApp().run()