import spherov2
import time
import random
import csv
from datetime import datetime

import mido
from mido import Message

from spherov2 import scanner
from spherov2.sphero_edu import EventType, SpheroEduAPI
from spherov2.types import Color

from drum_patts import patterns

# constants
SPD = 200
TIME_SINCE_COLLISION = 3

# initialize spheros
SPHERO_1 = "SB-8965"
SPHERO_2 = "SB-6E5B"
SPHERO_3 = "SB-899E"
SPHERO_4 = "SB-9616"

# initialize timekeeping
prev_sec = datetime.now().second
last_time_check = time.time()

# intialize color palettes
RAINBOW = [Color(255, 0, 0), Color(255, 80, 0), Color(254, 180, 0), Color(0, 255, 0), Color(0, 0, 255), Color(100, 0, 255)]
PINKS = [Color(222, 49, 99), Color(255, 0, 255), Color(254, 91, 172), Color(255, 0, 144), Color(224, 17, 95)]
BLUES = [Color(0, 150, 255), Color(0, 0, 255), Color(0, 255, 255), Color(125, 249, 255), Color(93, 63, 211)]
GREENS = [Color(60, 200, 20), Color(9, 150, 30), Color(20, 70, 6), Color(39, 90, 27), Color(50, 205, 0)]
YELLOWS = [Color(255, 191, 0), Color(255, 215, 0), Color(228, 208, 10), Color(255, 160, 0), Color(250, 250, 51)]

last = PINKS[0]
default_on = True

# intialize interaction info
last_midi = 0
switched = False

# initialize pattern info
idx = 0
patt_len = 0
rpt = 2

with mido.open_input("AKM320") as inport:

    # connect to sphero
    all_toys = scanner.find_toys(toy_names=[SPHERO_1])
    print(all_toys)
    toy = all_toys[0]

    with SpheroEduAPI(toy) as ball:

        # initialize the ball
        ball.reset_aim()
        ball.set_main_led(last)

        # start exactly on an even second, as each measure is 2 seconds long for 4/4 TS and 120 bpm
        curr_sec = datetime.now().second

        if (curr_sec % 2 == 0):
            while (curr_sec % 2 == 0):
                curr_sec = datetime.now().second

        while (curr_sec % 2 != 0):
            curr_sec = datetime.now().second

        # beginning motion and time
        ball.set_speed(SPD)
        last_time_check = time.time()

        # performance loop
        while(True):

            # update timekeeping
            curr_time_check = time.time()
            curr_sec = datetime.now().second

            # if detect MIDI message
            for msg in inport.iter_pending():

                if (msg.type=="note_on" or msg.type=="note_off"):
                    # change color
                    if (msg.note == 72 or msg.note == 84): # high C or highest C --> RED
                        ball.set_main_led(RAINBOW[0])
                        default_on = False
                    elif msg.note == 74: # high D --> ORANGE
                        ball.set_main_led(RAINBOW[1])
                        default_on = False
                    elif msg.note == 76: # high E --> YELLOW
                        ball.set_main_led(RAINBOW[2])
                        default_on = False
                    elif msg.note == 77: # high F --> GREEN
                        ball.set_main_led(RAINBOW[3])
                        default_on = False
                    elif msg.note == 79: # high G --> BLUE
                        ball.set_main_led(RAINBOW[4])
                        default_on = False
                    elif msg.note == 81: # high A --> PURPLE
                        ball.set_main_led(RAINBOW[5])
                        default_on = False
                    elif msg.note == 83: # high B --> RETURN TO DEFAULT PALETTE
                        default_on = True

                    # change pattern movement
                    if msg.note == 60: # middle C RESTART PATTERNS
                        if (curr_sec % 2 == 0):
                            while (curr_sec % 2 == 0):
                                curr_sec = datetime.now().second

                        while (curr_sec % 2 != 0):
                            curr_sec = datetime.now().second
                        ball.set_heading(0)
                        ball.set_speed(SPD)
                        last_midi = 60
                    elif msg.note == 62: # middle D ROBOTS SPIN
                        ball.set_speed(0)
                        time.sleep(0.5)
                        last_midi = 59
                    elif msg.note == 64: # middle E ROBOTS STOP
                        ball.set_speed(0)
                        last_midi = 64
                    elif msg.note == 65: # middle F ROBOTS GO IN CIRCLES
                        ball.set_speed(0)
                        time.sleep(0.5)
                        last_midi = 65
                    elif msg.note == 67: # middle G ROBOTS SWITCH INSTRUMENTS
                        if (switched == False):
                            ball.set_speed(0)
                            time.sleep(0.5)
                            ball.set_heading(ball.get_heading() + 90)
                            time.sleep(0.5)
                            ball.set_speed(SPD)
                            switched = True
                        else:
                            switched = False
                    elif msg.note == 69: # middle A RETURN ROBOTS TO CENTER
                        if (switched == False):
                            ball.set_speed(0)
                            time.sleep(0.5)
                            ball.set_heading(0)
                            time.sleep(0.5)
                            ball.set_speed(200)
                            time.sleep(1)
                            ball.set_speed(0)
                            time.sleep(0.5)
                            ball.set_heading(-75)
                            time.sleep(0.5)
                            ball.set_speed(200)
                            time.sleep(1)
                            ball.set_speed(0)
                            time.sleep(0.5)
                            ball.set_heading(135)
                            time.sleep(0.5)
                            ball.set_speed(57)
                            time.sleep(0.5)
                            ball.set_speed(0)
                            time.sleep(0.5)
                            ball.set_heading(0)
                            switched = True
                            last_midi = 69
                        else:
                            switched = False

            # default color change each second
            if (curr_sec != prev_sec and default_on):
                prev_sec = curr_sec
                select = random.choice([c for c in PINKS if c != last])
                last = select
                ball.set_main_led(select)

            # if there are no MIDI messages, first check lingering effects
            if last_midi == 59:
                ball.spin(360, 1)
            elif last_midi == 65:
                ball.set_speed(SPD)
                time.sleep(0.75)
                ball.set_speed(0)
                time.sleep(0.25)
                ball.set_heading(ball.get_heading() + 90)
            elif last_midi == 69 or last_midi == 64:
                ball.set_speed(0)

            else: # otherwise default movement

                # collision detection + movement, or when the robot has not "collided" in over 4 sec
                if (ball.get_acceleration()['z'] <= 0.35) or ((curr_time_check - last_time_check) > TIME_SINCE_COLLISION):

                    # update music index
                    idx += 1

                    # pattern selection (if req)
                    if (idx >= patt_len):
                        rpt += 1
                        # leader repeats each pattern once
                        if (rpt >= 2):
                            patt_idx = random.randint(0, len(patterns)-1)
                            patt = patterns[patt_idx]
                            idx = 0
                            rpt = 0
                            patt_len = len(patt)

                            # append the new pattern index to the csv
                            with open('pattern.csv', 'a') as f_object:
                                writer = csv.writer(f_object)
                                writer.writerow([patt_idx])
                                f_object.close()

                        else:
                            idx = 0

                    # movement change
                    ball.stop_roll()
                    ball.set_heading(ball.get_heading() + 180)
                    time.sleep(patt[idx])
                    ball.set_speed(SPD)

                    # update last time a collision happened
                    last_time_check = time.time()
