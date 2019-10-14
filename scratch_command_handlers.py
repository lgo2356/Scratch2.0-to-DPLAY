# -*- coding: utf-8 -*-

"""
Created on Wed Nov  25 13:17:15 2013

@author: Alan Yorinks
Copyright (c) 2013-14 Alan Yorinks All right reserved.

@co-author: Sjoerd Dirk Meijer, fromScratchEd.nl (language support)

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""

import logging
import datetime
import ConfigParser
import time
import threading


class ScratchCommandHandlers:
    """
    This class processes any command received from Scratch 2.0

    If commands need to be added in the future, a command handler method is
    added to this file and the command_dict at the end of this file is
    updated to contain the method. Command names must be the same in the json .s2e Scratch
    descriptor file.
    """
    # get translation strings from xlate.cfg
    config = ConfigParser.ConfigParser()
    config.read('utills\\xlate.cfg')

    ln_languages = config.get('translation_lists', 'ln_languages').split(',')
    ln_ENABLE = config.get('translation_lists', 'ln_ENABLE').split(',')
    ln_DISABLE = config.get('translation_lists', 'ln_DISABLE').split(',')
    ln_INPUT = config.get('translation_lists', 'ln_INPUT').split(',')
    ln_OUTPUT = config.get('translation_lists', 'ln_OUTPUT').split(',')
    ln_PWM = config.get('translation_lists', 'ln_PWM').split(',')
    ln_SERVO = config.get('translation_lists', 'ln_SERVO').split(',')
    ln_TONE = config.get('translation_lists', 'ln_TONE').split(',')
    ln_SONAR = config.get('translation_lists', 'ln_SONAR').split(',')
    ln_OFF = config.get('translation_lists', 'ln_OFF').split(',')
    ln_ON = config.get('translation_lists', 'ln_ON').split(',')

    '''For DPLAY'''
    In_LEFT = config.get('translation_lists', 'In_LEFT').split(',')
    In_RIGHT = config.get('translation_lists', 'In_RIGHT').split(',')
    In_FORWARD = config.get('translation_lists', 'In_FORWARD').split(',')
    In_REVERSE = config.get('translation_lists', 'In_REVERSE').split(',')
    In_STOP = config.get('translation_lists', 'In_STOP').split(',')
    In_C = config.get('translation_lists', 'In_C').split(',')
    In_C3 = config.get('translation_lists', 'In_C3').split(',')
    In_D = config.get('translation_lists', 'In_D').split(',')
    In_Eb = config.get('translation_lists', 'In_D3').split(',')
    In_E = config.get('translation_lists', 'In_E').split(',')
    In_F = config.get('translation_lists', 'In_F').split(',')
    In_F3 = config.get('translation_lists', 'In_F3').split(',')
    In_G = config.get('translation_lists', 'In_G').split(',')
    In_G3 = config.get('translation_lists', 'In_G3').split(',')
    In_A = config.get('translation_lists', 'In_A').split(',')
    In_Bb = config.get('translation_lists', 'In_A3').split(',')
    In_B = config.get('translation_lists', 'In_B').split(',')
    In_MUTE = config.get('translation_lists', 'In_MUTE').split(',')

    # pin counts for the board
    total_pins_discovered = 0
    number_of_analog_pins_discovered = 0

    # lists to keep track of which pins need to be included in the poll responses
    digital_poll_list = []
    analog_poll_list = []

    # detected pin capability map
    pin_map = {}

    # instance variable for PyMata
    firmata = None

    # debug state - 0 == off and 1 == on
    debug = 0

    # base report string to be modified in response to a poll command
    # PIN and VALUE will be replaced with pin number and the current value for the pin
    digital_reporter_base = 'digital_read/PIN VALUE'
    analog_reporter_base = 'analog_read/PIN VALUE'

    # convenience definition for cr + lf
    end_of_line = "\r\n"

    # indices into the command list sent to each command method
    CMD_COMMAND = 0  # this is the actual command
    CMD_ENABLE_DISABLE = 1  # enable or disable pin
    CMD_PIN = 1  # pin number for all commands except the Enable/Disable
    CMD_PIN_ENABLE_DISABLE = 2
    CMD_DIGITAL_MODE = 3  # pin mode
    CMD_VALUE = 2  # value pin to be set to
    CMD_TONE_FREQ = 2  # frequency for tone command
    CMD_TONE_DURATION = 3  # tone duration
    CMD_SERVO_DEGREES = 2  # number of degrees for servo position
    CMD_DEBUG = 1  # debugger on or off

    ENTRY_VALUE = 1

    '''For DPLAY'''
    DIGITAL_ON = 1
    DIGITAL_OFF = 0
    DC_FORWARD = False
    DC_REVERSE = False

    CMD_DC_LEFT_RIGHT = 1
    CMD_DIGITAL_SWITCH = 2
    CMD_DC_DIRECTION = 2
    CMD_DPLAY_TONE_FREQ = 3
    CMD_DPLAY_TONE_FREQ_en = 4
    CMD_TONE_OCTAVE = 4
    CMD_TONE_TIME = 5

    WAITING = ''
    COUNT = 0
    CANCEL_COUNT = 0

    # noinspection PyPep8Naming
    def check_CMD_ENABLE_DISABLE(self, command):
        if command in self.ln_ENABLE:
            return 'Enable'
        if command in self.ln_DISABLE:
            return 'Disable'

    # noinspection PyPep8Naming
    def check_CMD_DIGITAL_MODE(self, command):
        if command in self.ln_INPUT:
            return 'Input'
        if command in self.ln_OUTPUT:
            return 'Output'
        if command in self.ln_PWM:
            return 'PWM'
        if command in self.ln_SERVO:
            return 'Servo'
        if command in self.ln_TONE:
            return 'Tone'
        if command in self.ln_SONAR:
            return 'SONAR'

    # noinspection PyPep8Naming
    def ON_OFF(self, command):
        if command in self.ln_OFF:
            return 'Off'
        if command in self.ln_ON:
            return 'On'

    def LEFT_RIGHT(self, command):
        if command in self.In_LEFT:
            return 'Left'
        if command in self.In_RIGHT:
            return 'Right'

    def DIRECTION(self, command):
        if command in self.In_FORWARD:
            return 'Forward'
        if command in self.In_REVERSE:
            return 'Reverse'
        if command in self.In_STOP:
            return 'Stop'

    def match_scale(self, command):
        if command in self.In_C:
            return 'C'
        if command in self.In_C3:
            return 'C#'
        if command in self.In_D:
            return 'D'
        if command in self.In_Eb:
            return 'Eb'
        if command in self.In_E:
            return 'E'
        if command in self.In_F:
            return 'F'
        if command in self.In_F3:
            return 'F#'
        if command in self.In_G:
            return 'G'
        if command in self.In_G3:
            return 'G#'
        if command in self.In_A:
            return 'A'
        if command in self.In_Bb:
            return 'Bb'
        if command in self.In_B:
            return 'B'
        if command in self.In_MUTE:
            return 'Mute'

    def __init__(self, firmata, com_port, total_pins_discovered, number_of_analog_pins_discovered):
        """
        The class constructor creates the pin lists for the pins that will report
        data back to Scratch as a result of a poll request.
        @param total_pins_discovered:
        @param number_of_analog_pins_discovered:
        """
        self.firmata = firmata  
        self.com_port = com_port
        self.total_pins_discovered = total_pins_discovered
        self.number_of_analog_pins_discovered = number_of_analog_pins_discovered
        self.first_poll_received = False
        self.debug = 0

        # Create a pin list for poll data based on the total number of pins( digital table)
        # and a pin list for the number of analog pins.
        # Pins will be marked using Firmata Pin Types
        for x in range(self.total_pins_discovered):
            self.digital_poll_list.append(self.firmata.IGNORE)

        for x in range(self.number_of_analog_pins_discovered):
            self.analog_poll_list.append(self.firmata.IGNORE)

    def do_command(self, command):
        """
        This method looks up the command that resides in element zero of the command list
        within the command dictionary and executes the method for the command.
        Each command returns string that will be eventually be sent to Scratch
        @param command: This is a list containing the Scratch command and all its parameters
        @return: String to be returned to Scratch via HTTP
        """
        method = self.command_dict.get(command[0])

        if command[0] != "poll":
            # turn on debug logging if requested
            if self.debug == 'On':
                debug_string = "DEBUG: "
                debug_string += str(datetime.datetime.now())
                debug_string += ": "
                for data in command:
                    debug_string += "".join(map(str, data))
                    debug_string += ' '
                logging.debug(debug_string)
                print debug_string
        return method(self, command)

    #noinspection PyUnusedLocal
    def poll(self, command):
        # look for first poll and when received let the world know we are ready!
        """
        This method scans the data tables and assembles data for all reporter
        blocks and returns the data to the caller.
        @param command: This is a list containing the Scratch command and all its parameters It is unsused
        @return: 'okay'
        """

        if not self.first_poll_received:
            logging.info('Scratch detected! Ready to rock and roll...')
            print 'Scratch detected! Ready to rock and roll...'
            self.first_poll_received = True

        # assemble all output pin reports

        # first get the current digital and analog pin values from firmata
        digital_response_table = self.firmata.get_digital_response_table()
        analog_response_table = self.firmata.get_analog_response_table()

        # for each pin in the poll list that is set as an INPUT,
        # retrieve the pins value from the response table and build the response
        # string

        # digital first
        # responses = ''
        responses = self.WAITING

        for pin in range(self.total_pins_discovered):
            if self.digital_poll_list[pin] == self.firmata.INPUT:
                pin_number = str(pin)
                pin_entry = digital_response_table[pin]
                value = str(pin_entry[1])

                if value == '0':
                    value = 'false\n'
                elif value == '1':
                    value = 'true\n'

                report_entry = self.digital_reporter_base
                report_entry = report_entry.replace("PIN", pin_number)
                report_entry = report_entry.replace("VALUE", value)
                responses += report_entry
                responses += self.end_of_line

        for pin in range(self.total_pins_discovered):
            if self.digital_poll_list[pin] == self.firmata.INPUT:
                pin_number = str(pin)
                pin_entry = digital_response_table[pin]
                value = str(pin_entry[self.ENTRY_VALUE])
                pressed = '눌림'
                pressed_en = 'on(1)'
                unpressed = '안눌림'
                unpressed_en = 'off(0)'
                # pressed = 'on(1)'
                # unpressed = 'off(0)'

                # '눌림'
                if value == '0':
                    value = 'false\n'
                elif value == '1':
                    value = 'true\n'
                report_entry = "digital_read_switch/PIN/SWITCH VALUE"
                report_entry = report_entry.replace("PIN", pin_number)
                report_entry = report_entry.replace("SWITCH", pressed)
                report_entry = report_entry.replace("VALUE", value)
                responses += report_entry
                responses += self.end_of_line

                # 'on(1)'
                if value == '0':
                    value = 'false\n'
                elif value == '1':
                    value = 'true\n'
                report_entry = "digital_read_switch/PIN/SWITCH VALUE"
                report_entry = report_entry.replace("PIN", pin_number)
                report_entry = report_entry.replace("SWITCH", pressed_en)
                report_entry = report_entry.replace("VALUE", value)
                responses += report_entry
                responses += self.end_of_line

                # '안눌림'
                # value 다시 초기화
                value = str(pin_entry[self.ENTRY_VALUE])
                if value == '0':
                    value = 'true\n'
                elif value == '1':
                    value = 'false\n'
                report_entry = "digital_read_switch/PIN/SWITCH VALUE"
                report_entry = report_entry.replace("PIN", pin_number)
                report_entry = report_entry.replace("SWITCH", unpressed)
                report_entry = report_entry.replace("VALUE", value)
                responses += report_entry
                responses += self.end_of_line

                # 'off(1)'
                if value == '0':
                    value = 'false\n'
                elif value == '1':
                    value = 'true\n'
                report_entry = "digital_read_switch/PIN/SWITCH VALUE"
                report_entry = report_entry.replace("PIN", pin_number)
                report_entry = report_entry.replace("SWITCH", unpressed_en)
                report_entry = report_entry.replace("VALUE", value)
                responses += report_entry
                responses += self.end_of_line

                # 기울기
                value = str(pin_entry[self.ENTRY_VALUE])
                left = '왼쪽'
                left_en = 'Left'
                right = '오른쪽'
                right_en = 'Right'

                # '왼쪽'
                if value == '0':
                    value = 'false\n'
                elif value == '1':
                    value = 'true\n'
                report_entry = "digital_read_slope/PIN/SLOPE VALUE"
                report_entry = report_entry.replace("PIN", pin_number)
                report_entry = report_entry.replace("SLOPE", left)
                report_entry = report_entry.replace("VALUE", value)
                responses += report_entry
                responses += self.end_of_line

                # 'Left'
                if value == '0':
                    value = 'false\n'
                elif value == '1':
                    value = 'true\n'
                report_entry = "digital_read_slope/PIN/SLOPE VALUE"
                report_entry = report_entry.replace("PIN", pin_number)
                report_entry = report_entry.replace("SLOPE", left_en)
                report_entry = report_entry.replace("VALUE", value)
                responses += report_entry
                responses += self.end_of_line

                # '오른쪽'
                # value 다시 초기화
                value = str(pin_entry[self.ENTRY_VALUE])
                if value == '0':
                    value = 'true\n'
                elif value == '1':
                    value = 'false\n'
                report_entry = "digital_read_slope/PIN/SLOPE VALUE"
                report_entry = report_entry.replace("PIN", pin_number)
                report_entry = report_entry.replace("SLOPE", right)
                report_entry = report_entry.replace("VALUE", value)
                responses += report_entry
                responses += self.end_of_line

                # 'Right'
                if value == '0':
                    value = 'false\n'
                elif value == '1':
                    value = 'true\n'
                report_entry = "digital_read_slope/PIN/SLOPE VALUE"
                report_entry = report_entry.replace("PIN", pin_number)
                report_entry = report_entry.replace("SLOPE", right_en)
                report_entry = report_entry.replace("VALUE", value)
                responses += report_entry
                responses += self.end_of_line

        # now check for any analog reports to be added
        for pin in range(self.number_of_analog_pins_discovered):
            if self.analog_poll_list[pin] != self.firmata.IGNORE:
                pin_number = str(pin)
                pin_entry = analog_response_table[pin]
                value = str(pin_entry[self.ENTRY_VALUE])

                report_entry = self.analog_reporter_base
                report_entry = report_entry.replace("PIN", pin_number)
                report_entry = report_entry.replace("VALUE", value)
                responses += report_entry
                responses += self.end_of_line

        if responses == '':
            responses = 'okay'
        return responses

    #noinspection PyUnusedLocal
    def send_cross_domain_policy(self, command):
        """
        This method returns cross domain policy back to Scratch upon request.
        It keeps Flash happy.
        @param command: Command and all possible parameters in list form
        @return: policy string
        """
        policy = "<cross-domain-policy>\n"
        policy += "  <allow-access-from domain=\"*\" to-ports=\""
        policy += str(self.com_port)
        policy += "\"/>\n"
        policy += "</cross-domain-policy>\n\0"
        return policy

    #noinspection PyUnusedLocal
    def reset_arduino(self, command):
        """
        This method will send the reset command to the arduino and the poll tables
        @param command: Command and all possible parameters in list form
        @return: 'okay'
        """
        # reset the tables
        for x in range(self.total_pins_discovered):
            self.digital_poll_list[x] = self.firmata.IGNORE

        for x in range(self.number_of_analog_pins_discovered):
            self.analog_poll_list[x] = self.firmata.IGNORE
        self.firmata.reset()
        self.debug = 0
        return 'okay'

    def digital_pin_mode(self, command):
        """
        This method will set the poll list table appropriately and
        send the arduino a set_pin  configuration message.
        @param command: Command and all possible parameters in list form
        @return: 'okay'
        """
        if not command[self.CMD_PIN_ENABLE_DISABLE].isdigit():
            logging.debug('digital_pin_mode: The pin number must be set to a numerical value')
            print 'digital_pin_mode: The pin number must be set to a numerical value'
            return 'okay'

        pin = int(command[self.CMD_PIN_ENABLE_DISABLE]) # index 3

        # test for a valid pin number
        if pin >= self.total_pins_discovered:
            logging.debug('digital_pin_mode: pin %d exceeds number of pins on board' % pin)
            print 'digital_pin_mode: pin %d exceeds number of pins on board' % pin
            return 'okay'
        # ok pin is range, but make
        else:
            if command[0] == 'digital_pin_mode':
                # now test for enable or disable
                if self.check_CMD_ENABLE_DISABLE(command[self.CMD_ENABLE_DISABLE]) == 'Enable':
                    # choices will be input or some output mode
                    if self.check_CMD_DIGITAL_MODE(command[self.CMD_DIGITAL_MODE]) == 'Input':
                        if self.valid_digital_pin_mode_type(pin, self.firmata.INPUT):
                            # set the digital poll list for the pin
                            self.digital_poll_list[pin] = self.firmata.INPUT
                            # send the set request to the Arduino
                            self.firmata.set_pin_mode(pin, self.firmata.INPUT, self.firmata.DIGITAL)
                        else:
                            logging.debug('digital_pin_mode: Pin %d does not support INPUT mode' % pin)
                            print 'digital_pin_mode: Pin %d does not support INPUT mode ' % pin
                            return 'okay'
                    elif self.check_CMD_DIGITAL_MODE(command[self.CMD_DIGITAL_MODE]) == 'SONAR':
                            # any digital input pin can be used for SONAR
                            if self.valid_digital_pin_mode_type(pin, self.firmata.INPUT):
                                self.digital_poll_list[pin] = self.firmata.INPUT
                                self.firmata.sonar_config(pin, pin)
                            else:
                                logging.debug('digital_pin_mode: Pin %d does not support SONAR mode' % pin)
                                print 'digital_pin_mode: Pin %d does not support SONAR mode' % pin
                                return 'okay'
                    else:
                        # an output mode, so just clear the poll bit
                        if self.check_CMD_DIGITAL_MODE(command[self.CMD_DIGITAL_MODE]) == 'Output':
                            if self.valid_digital_pin_mode_type(pin, self.firmata.OUTPUT):
                                self.digital_poll_list[pin] = self.firmata.OUTPUT
                                self.firmata.set_pin_mode(pin, self.firmata.OUTPUT, self.firmata.DIGITAL)
                            else:
                                logging.debug('digital_pin_mode: Pin %d does not support OUTPUT mode' % pin)
                                print 'digital_pin_mode: Pin %d does not support OUTPUT mode' % pin
                                return 'okay'
                        elif self.check_CMD_DIGITAL_MODE(command[self.CMD_DIGITAL_MODE]) == 'PWM':
                            if self.valid_digital_pin_mode_type(pin, self.firmata.PWM):
                                self.digital_poll_list[pin] = self.firmata.PWM
                                self.firmata.set_pin_mode(pin, self.firmata.PWM, self.firmata.DIGITAL)
                            else:
                                logging.debug('digital_pin_mode: Pin %d does not support PWM mode' % pin)
                                print 'digital_pin_mode: Pin %d does not support PWM mode' % pin
                                return 'okay'
                        elif self.check_CMD_DIGITAL_MODE(command[self.CMD_DIGITAL_MODE]) == 'Tone':
                            # Tone can be on any pin so we look for OUTPUT
                            if self.valid_digital_pin_mode_type(pin, self.firmata.OUTPUT):
                                self.digital_poll_list[pin] = self.firmata.TONE_TONE
                                # self.firmata.set_pin_mode(pin, self.firmata.TONE_TONE, self.firmata.DIGITAL)
                                self.firmata.set_pin_mode(pin, self.firmata.OUTPUT, self.firmata.DIGITAL)
                            else:
                                logging.debug('digital_pin_mode: Pin %d does not support TONE mode' % pin)
                                print 'digital_pin_mode: Pin %d does not support TONE mode' % pin
                                return 'okay'
                        elif self.check_CMD_DIGITAL_MODE(command[self.CMD_DIGITAL_MODE]) == 'Servo':
                            if self.valid_digital_pin_mode_type(pin, self.firmata.SERVO):
                                self.digital_poll_list[pin] = self.firmata.SERVO
                                self.firmata.servo_config(pin)
                            else:
                                logging.debug('digital_pin_mode: Pin %d does not support SERVO mode' % pin)
                                print 'digital_pin_mode: Pin %d does not support SERVO mode' % pin
                                return 'okay'
                        else:
                            logging.debug('digital_pin_mode: Unknown output mode %s' % command[self.CMD_DIGITAL_MODE])
                            print 'digital_pin_mode: Unknown output mode %s' % command[self.CMD_DIGITAL_MODE]
                            return 'okay'
                if self.check_CMD_ENABLE_DISABLE(command[self.CMD_ENABLE_DISABLE]) == 'Disable':
                    # disable pin of any type by setting it to IGNORE in the table
                    self.digital_poll_list[pin] = self.firmata.IGNORE
                    # this only applies to Input pins. For all other pins we leave the poll list as is
                    if self.check_CMD_DIGITAL_MODE(command[self.CMD_DIGITAL_MODE]) == 'Input':
                        # send a disable reporting message
                        self.firmata.disable_digital_reporting(pin)
                    if self.check_CMD_DIGITAL_MODE(command[self.CMD_DIGITAL_MODE]) == 'SONAR':
                        # send a disable reporting message
                        self.firmata.disable_digital_reporting(pin)
            elif command[0] == 'digital_pin_mode_en':
                # now test for enable or disable
                if command[self.CMD_ENABLE_DISABLE] == 'Use':
                    # choices will be input or some output mode
                    if command[self.CMD_DIGITAL_MODE] == 'input':
                        if self.valid_digital_pin_mode_type(pin, self.firmata.INPUT):
                            # set the digital poll list for the pin
                            self.digital_poll_list[pin] = self.firmata.INPUT
                            # send the set request to the Arduino
                            self.firmata.set_pin_mode(pin, self.firmata.INPUT, self.firmata.DIGITAL)
                        else:
                            logging.debug('digital_pin_mode: Pin %d does not support INPUT mode' % pin)
                            print 'digital_pin_mode: Pin %d does not support INPUT mode ' % pin
                            return 'okay'
                    elif command[self.CMD_DIGITAL_MODE] == 'tone%20detection':
                        # any digital input pin can be used for SONAR
                        if self.valid_digital_pin_mode_type(pin, self.firmata.INPUT):
                            self.digital_poll_list[pin] = self.firmata.INPUT
                            self.firmata.sonar_config(pin, pin)
                        else:
                            logging.debug('digital_pin_mode: Pin %d does not support SONAR mode' % pin)
                            print 'digital_pin_mode: Pin %d does not support SONAR mode' % pin
                            return 'okay'
                    else:
                        # an output mode, so just clear the poll bit
                        if command[self.CMD_DIGITAL_MODE] == 'output':
                            if self.valid_digital_pin_mode_type(pin, self.firmata.OUTPUT):
                                self.digital_poll_list[pin] = self.firmata.OUTPUT
                                self.firmata.set_pin_mode(pin, self.firmata.OUTPUT, self.firmata.DIGITAL)
                            else:
                                logging.debug('digital_pin_mode: Pin %d does not support OUTPUT mode' % pin)
                                print 'digital_pin_mode: Pin %d does not support OUTPUT mode' % pin
                                return 'okay'
                        elif command[self.CMD_DIGITAL_MODE] == 'current%20regulation':
                            if self.valid_digital_pin_mode_type(pin, self.firmata.PWM):
                                self.digital_poll_list[pin] = self.firmata.PWM
                                self.firmata.set_pin_mode(pin, self.firmata.PWM, self.firmata.DIGITAL)
                            else:
                                logging.debug('digital_pin_mode: Pin %d does not support PWM mode' % pin)
                                print 'digital_pin_mode: Pin %d does not support PWM mode' % pin
                                return 'okay'
                        elif command[self.CMD_DIGITAL_MODE] == 'tone':
                            # Tone can be on any pin so we look for OUTPUT
                            if self.valid_digital_pin_mode_type(pin, self.firmata.OUTPUT):
                                self.digital_poll_list[pin] = self.firmata.TONE_TONE
                                # self.firmata.set_pin_mode(pin, self.firmata.TONE_TONE, self.firmata.DIGITAL)
                                self.firmata.set_pin_mode(pin, self.firmata.OUTPUT, self.firmata.DIGITAL)
                            else:
                                logging.debug('digital_pin_mode: Pin %d does not support TONE mode' % pin)
                                print 'digital_pin_mode: Pin %d does not support TONE mode' % pin
                                return 'okay'
                        elif command[self.CMD_DIGITAL_MODE] == 'servo%20motor':
                            if self.valid_digital_pin_mode_type(pin, self.firmata.SERVO):
                                self.digital_poll_list[pin] = self.firmata.SERVO
                                self.firmata.servo_config(pin)
                            else:
                                logging.debug('digital_pin_mode: Pin %d does not support SERVO mode' % pin)
                                print 'digital_pin_mode: Pin %d does not support SERVO mode' % pin
                                return 'okay'
                        else:
                            logging.debug('digital_pin_mode: Unknown output mode %s' % command[self.CMD_DIGITAL_MODE])
                            print 'digital_pin_mode: Unknown output mode %s' % command[self.CMD_DIGITAL_MODE]
                            return 'okay'
                if self.check_CMD_ENABLE_DISABLE(command[self.CMD_ENABLE_DISABLE]) == 'Disable':
                    # disable pin of any type by setting it to IGNORE in the table
                    self.digital_poll_list[pin] = self.firmata.IGNORE
                    # this only applies to Input pins. For all other pins we leave the poll list as is
                    if self.check_CMD_DIGITAL_MODE(command[self.CMD_DIGITAL_MODE]) == 'Input':
                        # send a disable reporting message
                        self.firmata.disable_digital_reporting(pin)
                    if self.check_CMD_DIGITAL_MODE(command[self.CMD_DIGITAL_MODE]) == 'SONAR':
                        # send a disable reporting message
                        self.firmata.disable_digital_reporting(pin)
            # normal http return for commands
            return 'okay'

    def digital_pin_mode_ja(self, command_ja):
        """
        This method will call digital_pin_mode after reordering
        command arguments (from Japanese order to English order).
        @param command: Command and all possible parameters in list form
        @return: 'okay'
        """
        command = ['digital_pin_mode'] + [command_ja[i] for i in [3, 1, 2]]
        return self.digital_pin_mode(command)

    def valid_digital_pin_mode_type(self, pin, pin_mode):
        """
        This is a utility method to determine if the pin supports the pin mode
        @param pin: Pin number
        @param pin_mode: Pin Mode
        @return: True if the mode is supported or False if it not supported.
        """
        pin_modes = self.pin_map[pin]
        if pin_mode in pin_modes:
            return True
        else:
            return False

    def analog_pin_mode(self, command):
        """
        This method will set the poll list table appropriately and
        send the arduino the correct configuration message.
        @param command: Command and all possible parameters in list form
        @return: 'okay'
        """

        if not command[self.CMD_PIN_ENABLE_DISABLE].isdigit():
            logging.debug('analog_pin_mode: The pin number must be set to a numerical value')
            print 'analog_pin_mode: The pin number must be set to a numerical value'
            return 'okay'

        pin = int(command[self.CMD_PIN_ENABLE_DISABLE])
        # Normally analog pins act as inputs only, but the DUE allow analog ins
        # test for a valid pin number
        if pin >= self.number_of_analog_pins_discovered:
            print 'analog_pin_mode: pin %d exceeds number of analog pins on board' % pin
            logging.debug('analog_pin_mode: pin %d exceeds number of analog pins on board' % pin)
            return 'okay'
        else:
            if command[0] == 'analog_pin_mode':
                # now test for enable or disable
                if self.check_CMD_ENABLE_DISABLE(command[self.CMD_ENABLE_DISABLE]) == 'Enable':
                    # enable the analog pin
                    self.analog_poll_list[pin] = self.firmata.INPUT
                    self.firmata.set_pin_mode(pin, self.firmata.INPUT, self.firmata.ANALOG)
                else:
                    # Set analog poll list entry for the pin to IGNORE.
                    # Disable reporting
                    self.analog_poll_list[pin] = self.firmata.IGNORE
                    self.firmata.disable_analog_reporting(pin)
            elif command[0] == 'analog_pin_mode_en':
                # now test for enable or disable
                if command[self.CMD_ENABLE_DISABLE] == 'Use':
                    # enable the analog pin
                    self.analog_poll_list[pin] = self.firmata.INPUT
                    self.firmata.set_pin_mode(pin, self.firmata.INPUT, self.firmata.ANALOG)
                else:
                    # Set analog poll list entry for the pin to IGNORE.
                    # Disable reporting
                    self.analog_poll_list[pin] = self.firmata.IGNORE
                    self.firmata.disable_analog_reporting(pin)

        return 'okay'

    def analog_pin_mode_ja(self, command_ja):
        """
        This method will call analog_pin_mode after reordering
        command arguments (from Japanese order to English order).
        @param command: Command and all possible parameters in list form
        @return: 'okay'
        """
        command = ['analog_pin_mode'] + [command_ja[i] for i in [2, 1]]
        return self.analog_pin_mode(command)

    def digital_write(self, command):
        """
        This method outputs a 0 or a 1 to the designated digital pin that has been previously
        been configured as an output.

        If the pin is configured as an INPUT, writing a HIGH value with digitalWrite()
        will enable an internal 20K pullup resistor (see the tutorial on digital pins on arduino site).
        Writing LOW will disable the pullup. The pullup resistor is enough to light an LED dimly,
        so if LEDs appear to work, but very dimly, this is a likely cause.
        The remedy is to set the pin to an output.

        @param command: Command and all possible parameters in list form
        @return: okay
        """
        # test pin as a digital output pin in poll list table

        if not command[self.CMD_PIN].isdigit():
            logging.debug('digital_write: The pin number must be set to a numerical value')
            print 'digital_write: The pin number must be set to a numerical value'
            return 'okay'

        pin = int(command[self.CMD_PIN])

        if self.digital_poll_list[pin] == self.firmata.OUTPUT:
            self.firmata.digital_write(pin, int(command[self.CMD_VALUE]))
            return 'okay'
        # for pullup - see description above
        elif self.digital_poll_list[pin] == self.firmata.INPUT:
            self.firmata.digital_write(pin, int(command[self.CMD_VALUE]))
            return 'okay'
        else:
            print 'digital write: Pin %d must be enabled before writing to it.' % pin
            logging.debug('digital write: Pin %d must be enabled before writing to it.' % pin)
            return 'okay'

    '''
    def analog_write(self, command):
        """
        This method write the value (0-255) to the digital pin that has been
        previously been specified as a PWM pin. NOTE: Pin number is the digital
        pin number and not an analog pin number.
        @param command: Command and all possible parameters in list form
        @return: okay or _problem
        """
        if command[self.CMD_VALUE] == 'VAL':
            logging.debug('analog_write: The value field must be set to a numerical value')
            print 'analog_write: The value field must be set to a numerical value'
            return 'okay'

        if not command[self.CMD_PIN].isdigit():
            logging.debug('analog_write: The pin number must be set to a numerical value')
            print 'analog_write: The pin number must be set to a numerical value'
            return 'okay'

        pin = int(command[self.CMD_PIN])

        if self.digital_poll_list[pin] == self.firmata.PWM:
            # check to make sure that the value is in the range of 0-255
            if 0 <= int(command[1]) <= 255:
                self.firmata.analog_write(pin, int(command[self.CMD_VALUE]))
                return 'okay'
            else:
                print 'analog_write data value %d is out of range. It should be between 0-255' % \
                      int(command[self.CMD_VALUE])
                logging.debug('analog_write data value %d is out of range. It should be between 0-255' %
                              int(command[self.CMD_VALUE]))
                return '_problem analog_write data value %d is out of range. It should be between 0-255' % \
                       int(command[self.CMD_VALUE])
        else:
            print'analog_write: Pin %d must be enabled before writing to it.' % pin
            logging.debug('analog_write: Pin %d must be enabled before writing to it.' % pin)
            return '_problem Pin must be enabled before writing to it.'
    '''

    def play_tone(self, command):
        # check to make sure pin was configured for tone
        """
        This method will play a tone for the specified pin in command
        @param command: Command and all possible parameters in list form
        @return: okay or _problem
        """

        if not command[self.CMD_PIN].isdigit():
            logging.debug('play_tome: The pin number must be set to a numerical value')
            print 'play_tone: The pin number must be set to a numerical value'
            return 'okay'

        pin = int(command[self.CMD_PIN])

        if self.digital_poll_list[pin] == self.firmata.TONE_TONE:
            #noinspection PyUnusedLocal
            value = command[1]
            self.firmata.play_tone(pin, self.firmata.TONE_TONE, int(command[self.CMD_TONE_FREQ]),
                                   int(command[self.CMD_TONE_DURATION]))
            return 'okay'
        else:
            print 'play_tone: Pin %d was not enabled as TONE.' % pin
            logging.debug('play_tone: Pin %d was not enabled as TONE.' % pin)
            return 'okay'

    def tone_off(self, command):
       # check to make sure pin was configured for tone
        """
        This method will force tone to be off.
        @param command: Command and all possible parameters in list form
        @return: okay
        """

        if not command[self.CMD_PIN].isdigit():
            logging.debug('tone_off: The pin number must be set to a numerical value')
            print 'tone_off: The pin number must be set to a numerical value'
            return 'okay'

        pin = int(command[self.CMD_PIN])

        if self.digital_poll_list[pin] == self.firmata.TONE_TONE:
            #noinspection PyUnusedLocal
            value = command[1]
            self.firmata.play_tone(pin, self.firmata.TONE_NO_TONE, 0, 0)  
            return 'okay'
        else:
            print 'tone_off: Pin %d was not enabled as TONE.' % pin
            logging.debug('tone_off: Pin %d was not enabled as TONE.' % pin)
            return 'okay'

    def debug_control(self, command):
        """
        This method controls command block debug logging
        @param command: Either On or Off
        @return: okay
        """
        self.debug = self.ON_OFF(command[self.CMD_DEBUG])
        return 'okay'

    def set_servo_position(self, command):
        # check to make sure pin was configured for servo
        """
        This method will command the servo position if the digital pin was
        previously configured for Servo operation.
        A maximum of 180 degrees is allowed
        @param command: Command and all possible parameters in list form
        @return: okay
        """

        if not command[self.CMD_PIN].isdigit():
            logging.debug('servo_position: The pin number must be set to a numerical value')
            print 'servo_position: The pin number must be set to a numerical value'
            return 'okay'

        pin = int(command[self.CMD_PIN])

        if self.digital_poll_list[pin] == self.firmata.SERVO:
            if 0 <= int(command[self.CMD_SERVO_DEGREES]) <= 180:
                self.firmata.analog_write(pin,  int(command[self.CMD_SERVO_DEGREES]))
                return 'okay'
            else:
                print "set_servo_position: Request of %d degrees. Servo range is 0 to 180 degrees" % int(command[1])
                # noinspection PyPep8
                logging.debug("set_servo_position: Request of %d degrees. Servo range is 0 to 180 degrees"
                        % int(command[1]))
                return 'okay'
        else:
            print 'set_servo_position: Pin %d was not enabled for SERVO operations.' % pin
            logging.debug('set_servo_position: Pin %d was not enabled for SERVO operations.' % pin)
            return '_problem Pin was not enabled for SERVO operations.'

    def digital_read(self, command):
        """
        This method retrieves digital input information for Snap!
        @param command: Command and all possible parameters in list form
        @return: Current value of digital input pin
        """
        digital_response_table = self.firmata.get_digital_response_table()
        if self.digital_poll_list[int(command[self.CMD_PIN])] == self.firmata.INPUT:
            pin_number = command[self.CMD_PIN]
            pin_entry = digital_response_table[int(pin_number)]
            value = str(pin_entry[1])
            report_entry = value
            report_entry += self.end_of_line
            return report_entry

    def analog_read(self, command):
        """
        This method retrieves analog input information for Snap!
        @param: command: Command and all possible parameters in list form
        @return: Current value of analog input pin
        """

        pin = int(command[1])
        self.analog_poll_list[pin] = self.firmata.INPUT
        self.firmata.set_pin_mode(pin, self.firmata.INPUT, self.firmata.ANALOG)

        analog_response_table = self.firmata.get_analog_response_table()
        if self.analog_poll_list[int(command[self.CMD_PIN])] != self.firmata.IGNORE:
            pin_number = command[self.CMD_PIN]
            pin_entry = analog_response_table[int(pin_number)]
            value = str(pin_entry[1])
            report_entry = value
            report_entry += self.end_of_line
            return report_entry

    """
    Scratch 2.0 command methods for D PLAY
    """
    """
    새로운 블록 command 추가시 주의할 점
    블록에서 받아오는 value 값이 숫자나 영어가 아닐 시 URL 인코딩해야 합니다. (xlate.cfg 파일에 등록하면 됩니다.)
    """
    def command_translate(self, command):
        """
        URL 인코딩 문자(%0D%0A)를 제거하는 메소드 입니다.
        """
        if '%0D%0A' in command:
            command_translate = str(command)
            command_translate = command_translate.replace('%0D%0A', '')
            result = command_translate
            return result
        else:
            return command

    def digital_on_off(self, command):
        if command[0] == 'digital_pin_on_off':
            # pin 번호 저장
            pin = int(command[self.CMD_PIN])

            # pin 번호에 디지털 출력 모드 활성화
            self.digital_poll_list[pin] = self.firmata.OUTPUT
            self.firmata.set_pin_mode(pin, self.firmata.OUTPUT, self.firmata.DIGITAL)

            if self.ON_OFF(command[self.CMD_DIGITAL_SWITCH]) == 'On':
                if self.digital_poll_list[pin] == self.firmata.OUTPUT:
                    self.firmata.digital_write(pin, self.DIGITAL_ON)
                    return 'okay'
                # for pull up - see description above
                elif self.digital_poll_list[pin] == self.firmata.INPUT:
                    self.firmata.digital_write(pin, self.DIGITAL_ON)
                    return 'okay'
            elif self.ON_OFF(command[self.CMD_DIGITAL_SWITCH]) == 'Off':
                self.firmata.digital_write(pin, self.DIGITAL_OFF)
                # disable pin of any type by setting it to IGNORE in the table
                self.digital_poll_list[pin] = self.firmata.IGNORE
                # this only applies to Input pins. For all other pins we leave the poll list as is
                self.firmata.disable_digital_reporting(pin)
        elif command[0] == 'digital_pin_on_off_en':
            # pin 번호 저장
            pin = int(command[2])

            # pin 번호에 디지털 출력 모드 활성화
            self.digital_poll_list[pin] = self.firmata.OUTPUT
            self.firmata.set_pin_mode(pin, self.firmata.OUTPUT, self.firmata.DIGITAL)

            if command[1] == 'on(1)':
                if self.digital_poll_list[pin] == self.firmata.OUTPUT:
                    self.firmata.digital_write(pin, self.DIGITAL_ON)
                    return 'okay'
                # for pull up - see description above
                elif self.digital_poll_list[pin] == self.firmata.INPUT:
                    self.firmata.digital_write(pin, self.DIGITAL_ON)
                    return 'okay'
            elif command[1] == 'off(0)':
                self.firmata.digital_write(pin, self.DIGITAL_OFF)
                # disable pin of any type by setting it to IGNORE in the table
                self.digital_poll_list[pin] = self.firmata.IGNORE
                # this only applies to Input pins. For all other pins we leave the poll list as is
                self.firmata.disable_digital_reporting(pin)
        return 'okay'

    def analog_write(self, command):
        """
        This method write the value (0-255) to the digital pin that has been
        previously been specified as a PWM pin. NOTE: Pin number is the digital
        pin number and not an analog pin number.
        @param command: Command and all possible parameters in list form
        @return: okay or _problem
        """
        # Replace \r\n character in command
        if command[self.CMD_VALUE] == 'VAL':
            logging.debug('analog_write: The value field must be set to a numerical value')
            print 'analog_write: The value field must be set to a numerical value'
            return 'okay'

        if not command[self.CMD_PIN].isdigit():
            logging.debug('analog_write: The pin number must be set to a numerical value')
            print 'analog_write: The pin number must be set to a numerical value'
            return 'okay'

        if command[self.CMD_VALUE] == '':
            return 'okay'

        command[self.CMD_VALUE] = self.command_translate(command[self.CMD_VALUE])
        value = int(float(command[self.CMD_VALUE]))

        pin = int(command[self.CMD_PIN])
        self.digital_poll_list[pin] = self.firmata.PWM
        self.firmata.set_pin_mode(pin, self.firmata.PWM, self.firmata.DIGITAL)

        if self.digital_poll_list[pin] == self.firmata.PWM:
            # check to make sure that the value is in the range of 0-255
            if 0 <= value <= 255:
                self.firmata.analog_write(pin, value)
                return 'okay'
            else:
                print 'analog_write data value %d is out of range. It should be between 0-255' % value
                logging.debug('analog_write data value %d is out of range. It should be between 0-255' % value)
                return '_problem analog_write data value %d is out of range. It should be between 0-255' % value
        else:
            print'analog_write: Pin %d must be enabled before writing to it.' % pin
            logging.debug('analog_write: Pin %d must be enabled before writing to it.' % pin)
            return '_problem Pin must be enabled before writing to it.'

    def LED_control(self, command):
        # command: ['LED_control', <pin number>, <value>]
        # en_command: ['LED_control_en', <value>, <pin number>]
        if command[0] == 'LED_control':
            pin = int(command[self.CMD_PIN])
            self.digital_poll_list[pin] = self.firmata.OUTPUT
            self.firmata.set_pin_mode(pin, self.firmata.OUTPUT, self.firmata.DIGITAL)

            if self.ON_OFF(command[2]) == 'On':
                self.firmata.digital_write(pin, self.DIGITAL_ON)
                return 'okay'
            elif self.ON_OFF(command[2]) == 'Off':
                self.firmata.digital_write(pin, self.DIGITAL_OFF)
                return 'okay'
        elif command[0] == 'LED_control_en':
            pin = int(command[2])
            self.digital_poll_list[pin] = self.firmata.OUTPUT
            self.firmata.set_pin_mode(pin, self.firmata.OUTPUT, self.firmata.DIGITAL)

            if command[1] == 'on(1)':
                self.firmata.digital_write(pin, self.DIGITAL_ON)
                return 'okay'
            elif command[1] == 'off(0)':
                self.firmata.digital_write(pin, self.DIGITAL_OFF)
                return 'okay'
        return 'okay'

    def motor_direction(self, command):
        left_pin3 = 3
        left_pin5 = 5
        right_pin6 = 6
        right_pin11 = 11

        if command[0] == 'motor_direction':
            if self.LEFT_RIGHT(command[self.CMD_DC_LEFT_RIGHT]) == 'Left':
                # Left
                self.digital_poll_list[left_pin3] = self.firmata.OUTPUT
                self.firmata.set_pin_mode(left_pin3, self.firmata.OUTPUT, self.firmata.DIGITAL)
                self.digital_poll_list[left_pin5] = self.firmata.OUTPUT
                self.firmata.set_pin_mode(left_pin5, self.firmata.OUTPUT, self.firmata.DIGITAL)

                if self.DIRECTION(command[self.CMD_DC_DIRECTION]) == 'Forward':
                    self.DC_FORWARD = True
                    self.DC_REVERSE = False
                    self.firmata.digital_write(left_pin3, self.DIGITAL_OFF)
                    self.firmata.digital_write(left_pin5, self.DIGITAL_ON)
                    return 'okay'
                if self.DIRECTION(command[self.CMD_DC_DIRECTION]) == 'Reverse':
                    self.DC_FORWARD = False
                    self.DC_REVERSE = True
                    self.firmata.digital_write(left_pin3, self.DIGITAL_ON)
                    self.firmata.digital_write(left_pin5, self.DIGITAL_OFF)
                    return 'okay'
                elif self.DIRECTION(command[self.CMD_DC_DIRECTION]) == 'Stop':
                    self.DC_FORWARD = False
                    self.DC_REVERSE = False
                    self.firmata.digital_write(left_pin3, self.DIGITAL_OFF)
                    self.firmata.digital_write(left_pin5, self.DIGITAL_OFF)
                    self.digital_poll_list[left_pin3] = self.firmata.IGNORE
                    self.digital_poll_list[left_pin5] = self.firmata.IGNORE
                    self.firmata.disable_digital_reporting(left_pin3)
                    self.firmata.disable_digital_reporting(left_pin5)
                    return 'okay'
            elif self.LEFT_RIGHT(command[self.CMD_DC_LEFT_RIGHT]) == 'Right':
                # Right
                self.digital_poll_list[right_pin6] = self.firmata.OUTPUT
                self.firmata.set_pin_mode(right_pin6, self.firmata.OUTPUT, self.firmata.DIGITAL)
                self.digital_poll_list[right_pin11] = self.firmata.OUTPUT
                self.firmata.set_pin_mode(right_pin11, self.firmata.OUTPUT, self.firmata.DIGITAL)

                if self.DIRECTION(command[self.CMD_DC_DIRECTION]) == 'Forward':
                    self.DC_FORWARD = True
                    self.DC_REVERSE = False
                    self.firmata.digital_write(right_pin6, self.DIGITAL_ON)
                    self.firmata.digital_write(right_pin11, self.DIGITAL_OFF)
                    return 'okay'
                if self.DIRECTION(command[self.CMD_DC_DIRECTION]) == 'Reverse':
                    self.DC_FORWARD = False
                    self.DC_REVERSE = True
                    self.firmata.digital_write(right_pin6, self.DIGITAL_OFF)
                    self.firmata.digital_write(right_pin11, self.DIGITAL_ON)
                    return 'okay'
                elif self.DIRECTION(command[self.CMD_DC_DIRECTION]) == 'Stop':
                    self.DC_FORWARD = False
                    self.DC_REVERSE = False
                    self.firmata.digital_write(right_pin6, self.DIGITAL_OFF)
                    self.firmata.digital_write(right_pin11, self.DIGITAL_OFF)
                    self.digital_poll_list[right_pin6] = self.firmata.IGNORE
                    self.digital_poll_list[right_pin11] = self.firmata.IGNORE
                    self.firmata.disable_digital_reporting(right_pin6)
                    self.firmata.disable_digital_reporting(right_pin11)
                    return 'okay'
        elif command[0] == 'motor_direction_en':
            if command[self.CMD_DC_LEFT_RIGHT] == 'Left':
                if command[self.CMD_DC_DIRECTION] == 'Forward':
                    self.DC_FORWARD = True
                    self.DC_REVERSE = False
                    self.firmata.digital_write(left_pin3, self.DIGITAL_OFF)
                    self.firmata.digital_write(left_pin5, self.DIGITAL_ON)
                    return 'okay'
                if command[self.CMD_DC_DIRECTION] == 'Backward':
                    self.DC_FORWARD = False
                    self.DC_REVERSE = True
                    self.firmata.digital_write(left_pin3, self.DIGITAL_ON)
                    self.firmata.digital_write(left_pin5, self.DIGITAL_OFF)
                    return 'okay'
                elif command[self.CMD_DC_DIRECTION] == 'Stop':
                    self.DC_FORWARD = False
                    self.DC_REVERSE = False
                    self.firmata.digital_write(left_pin3, self.DIGITAL_OFF)
                    self.firmata.digital_write(left_pin5, self.DIGITAL_OFF)
                    self.digital_poll_list[left_pin3] = self.firmata.IGNORE
                    self.digital_poll_list[left_pin5] = self.firmata.IGNORE
                    self.firmata.disable_digital_reporting(left_pin3)
                    self.firmata.disable_digital_reporting(left_pin5)
                    return 'okay'
            elif command[self.CMD_DC_LEFT_RIGHT] == 'Right':
                if command[self.CMD_DC_DIRECTION] == 'Forward':
                    self.DC_FORWARD = True
                    self.DC_REVERSE = False
                    self.firmata.digital_write(right_pin6, self.DIGITAL_ON)
                    self.firmata.digital_write(right_pin11, self.DIGITAL_OFF)
                    return 'okay'
                if command[self.CMD_DC_DIRECTION] == 'Backward':
                    self.DC_FORWARD = False
                    self.DC_REVERSE = True
                    self.firmata.digital_write(right_pin6, self.DIGITAL_OFF)
                    self.firmata.digital_write(right_pin11, self.DIGITAL_ON)
                    return 'okay'
                elif command[self.CMD_DC_DIRECTION] == 'Stop':
                    self.DC_FORWARD = False
                    self.DC_REVERSE = False
                    self.firmata.digital_write(right_pin6, self.DIGITAL_OFF)
                    self.firmata.digital_write(right_pin11, self.DIGITAL_OFF)
                    self.digital_poll_list[right_pin6] = self.firmata.IGNORE
                    self.digital_poll_list[right_pin11] = self.firmata.IGNORE
                    self.firmata.disable_digital_reporting(right_pin6)
                    self.firmata.disable_digital_reporting(right_pin11)
                    return 'okay'

    def motor_speed_control(self, command):
        left_pin3 = 3
        left_pin5 = 5
        right_pin6 = 6
        right_pin11 = 11

        command[self.CMD_VALUE] = self.command_translate(command[self.CMD_VALUE])

        if command[self.CMD_VALUE] == 'VAL':
            logging.debug('analog_write: The value field must be set to a numerical value')
            print 'analog_write: The value field must be set to a numerical value'
            return 'okay'

        if self.LEFT_RIGHT(command[self.CMD_DC_LEFT_RIGHT]) == 'Left':
            # Left
            self.digital_poll_list[left_pin3] = self.firmata.PWM
            self.firmata.set_pin_mode(left_pin3, self.firmata.PWM, self.firmata.DIGITAL)
            self.digital_poll_list[left_pin5] = self.firmata.PWM
            self.firmata.set_pin_mode(left_pin5, self.firmata.PWM, self.firmata.DIGITAL)

            # check to make sure that the value is in the range of 0-255
            if 0 <= int(float(command[self.CMD_VALUE])) <= 100:
                speed = int(float(command[self.CMD_VALUE]) * 2.55)

                if speed >= 90:
                    if self.DC_FORWARD is True:
                        self.firmata.analog_write(left_pin3, self.DIGITAL_OFF)
                        self.firmata.analog_write(left_pin5, speed)
                        return 'okay'
                    elif self.DC_REVERSE is True:
                        self.firmata.analog_write(left_pin3, speed)
                        self.firmata.analog_write(left_pin5, self.DIGITAL_OFF)
                        return 'okay'
                elif 20 < speed < 90:
                    if self.DC_FORWARD is True:
                        self.firmata.analog_write(left_pin3, self.DIGITAL_OFF)
                        self.firmata.analog_write(left_pin5, 90)
                        return 'okay'
                    elif self.DC_REVERSE is True:
                        self.firmata.analog_write(left_pin3, 90)
                        self.firmata.analog_write(left_pin5, self.DIGITAL_OFF)
                        return 'okay'
                elif 0 <= speed <= 20:
                    self.firmata.digital_write(left_pin3, self.DIGITAL_OFF)
                    self.firmata.digital_write(left_pin5, self.DIGITAL_OFF)
                    # disable pin of any type by setting it to IGNORE in the table
                    self.digital_poll_list[left_pin3] = self.firmata.IGNORE
                    self.digital_poll_list[left_pin5] = self.firmata.IGNORE
                    return 'okay'
            else:
                print 'analog_write data value %d is out of range. It should be between 0-255' % \
                    int(command[self.CMD_VALUE])
                logging.debug('analog_write data value %d is out of range. It should be between 0-255' %
                              int(command[self.CMD_VALUE]))
                return '_problem analog_write data value %d is out of range. It should be between 0-255' % \
                       int(command[self.CMD_VALUE])
        elif self.LEFT_RIGHT(command[self.CMD_DC_LEFT_RIGHT]) == 'Right':
            # Right
            self.digital_poll_list[right_pin6] = self.firmata.PWM
            self.firmata.set_pin_mode(right_pin6, self.firmata.PWM, self.firmata.DIGITAL)
            self.digital_poll_list[right_pin11] = self.firmata.PWM
            self.firmata.set_pin_mode(right_pin11, self.firmata.PWM, self.firmata.DIGITAL)

            if 0 <= int(command[2]) <= 100:
                speed = int(int(command[2]) * 2.55)

                if speed >= 90:
                    if self.DC_FORWARD is True:
                        self.firmata.analog_write(right_pin6, speed)
                        self.firmata.analog_write(right_pin11, self.DIGITAL_OFF)
                        return 'okay'
                    elif self.DC_REVERSE is True:
                        self.firmata.analog_write(right_pin6, self.DIGITAL_OFF)
                        self.firmata.analog_write(right_pin11, speed)
                        return 'okay'
                elif 0 < speed < 90:
                    if self.DC_FORWARD is True:
                        self.firmata.analog_write(right_pin6, 90)
                        self.firmata.analog_write(right_pin11, self.DIGITAL_OFF)
                        return 'okay'
                    elif self.DC_REVERSE is True:
                        self.firmata.analog_write(right_pin6, self.DIGITAL_OFF)
                        self.firmata.analog_write(right_pin6, 90)
                        return 'okay'
                elif speed == 0:
                    self.firmata.digital_write(right_pin6, self.DIGITAL_OFF)
                    self.firmata.digital_write(right_pin11, self.DIGITAL_OFF)
                    # disable pin of any type by setting it to IGNORE in the table
                    self.digital_poll_list[right_pin6] = self.firmata.IGNORE
                    self.digital_poll_list[right_pin11] = self.firmata.IGNORE
                    return 'okay'
            else:
                print 'analog_write data value %d is out of range. It should be between 0-255' % \
                    int(command[self.CMD_VALUE])
                logging.debug('analog_write data value %d is out of range. It should be between 0-255' %
                              int(command[self.CMD_VALUE]))
                return '_problem analog_write data value %d is out of range. It should be between 0-255' % \
                       int(command[self.CMD_VALUE])

    def buzzer(self, command):
        # command: ['buzzer', <command_id>, <pin number>, <tone>, <octave>, <beat>]
        # en_command: ['buzzer_en', <command_id>, <pin number>, <beat>, <tone>, <octave>]

        if command[0] == 'buzzer':
            command_id = command[1]
            frequency = 0
            # millimeter second
            sec = int(float(command[self.CMD_TONE_TIME]) * 1000)
            sec2 = float(command[self.CMD_TONE_TIME])

            report_entry = '_busy ID'
            report_entry = report_entry.replace("ID", command_id)
            self.WAITING += report_entry
            self.WAITING += self.end_of_line
            self.start_timer(sec2)

            if command[self.CMD_TONE_OCTAVE] == '1':
                if self.match_scale(command[self.CMD_DPLAY_TONE_FREQ]) == 'C':
                    frequency = 262
                if self.match_scale(command[self.CMD_DPLAY_TONE_FREQ]) == 'C#':
                    frequency = 278
                if self.match_scale(command[self.CMD_DPLAY_TONE_FREQ]) == 'D':
                    frequency = 294
                if self.match_scale(command[self.CMD_DPLAY_TONE_FREQ]) == 'Eb':
                    frequency = 311
                if self.match_scale(command[self.CMD_DPLAY_TONE_FREQ]) == 'E':
                    frequency = 330
                if self.match_scale(command[self.CMD_DPLAY_TONE_FREQ]) == 'F':
                    frequency = 349
                if self.match_scale(command[self.CMD_DPLAY_TONE_FREQ]) == 'F#':
                    frequency = 370
                if self.match_scale(command[self.CMD_DPLAY_TONE_FREQ]) == 'G':
                    frequency = 392
                if self.match_scale(command[self.CMD_DPLAY_TONE_FREQ]) == 'G#':
                    frequency = 415
                if self.match_scale(command[self.CMD_DPLAY_TONE_FREQ]) == 'A':
                    frequency = 440
                if self.match_scale(command[self.CMD_DPLAY_TONE_FREQ]) == 'Bb':
                    frequency = 466
                if self.match_scale(command[self.CMD_DPLAY_TONE_FREQ]) == 'B':
                    frequency = 494
                if self.match_scale(command[self.CMD_DPLAY_TONE_FREQ]) == 'Mute':
                    frequency = 0
            elif command[self.CMD_TONE_OCTAVE] == '2':
                if self.match_scale(command[self.CMD_DPLAY_TONE_FREQ]) == 'C':
                    frequency = 523
                if self.match_scale(command[self.CMD_DPLAY_TONE_FREQ]) == 'C#':
                    frequency = 554
                if self.match_scale(command[self.CMD_DPLAY_TONE_FREQ]) == 'D':
                    frequency = 587
                if self.match_scale(command[self.CMD_DPLAY_TONE_FREQ]) == 'Eb':
                    frequency = 622
                if self.match_scale(command[self.CMD_DPLAY_TONE_FREQ]) == 'E':
                    frequency = 659
                if self.match_scale(command[self.CMD_DPLAY_TONE_FREQ]) == 'F':
                    frequency = 699
                if self.match_scale(command[self.CMD_DPLAY_TONE_FREQ]) == 'F#':
                    frequency = 740
                if self.match_scale(command[self.CMD_DPLAY_TONE_FREQ]) == 'G':
                    frequency = 784
                if self.match_scale(command[self.CMD_DPLAY_TONE_FREQ]) == 'G#':
                    frequency = 831
                if self.match_scale(command[self.CMD_DPLAY_TONE_FREQ]) == 'A':
                    frequency = 880
                if self.match_scale(command[self.CMD_DPLAY_TONE_FREQ]) == 'Bb':
                    frequency = 932
                if self.match_scale(command[self.CMD_DPLAY_TONE_FREQ]) == 'B':
                    frequency = 988
                if self.match_scale(command[self.CMD_DPLAY_TONE_FREQ]) == 'Mute':
                    frequency = 0
            elif command[self.CMD_TONE_OCTAVE] == '3':
                if self.match_scale(command[self.CMD_DPLAY_TONE_FREQ]) == 'C':
                    frequency = 1047
                if self.match_scale(command[self.CMD_DPLAY_TONE_FREQ]) == 'C#':
                    frequency = 1109
                if self.match_scale(command[self.CMD_DPLAY_TONE_FREQ]) == 'D':
                    frequency = 1175
                if self.match_scale(command[self.CMD_DPLAY_TONE_FREQ]) == 'Eb':
                    frequency = 1245
                if self.match_scale(command[self.CMD_DPLAY_TONE_FREQ]) == 'E':
                    frequency = 1319
                if self.match_scale(command[self.CMD_DPLAY_TONE_FREQ]) == 'F':
                    frequency = 1397
                if self.match_scale(command[self.CMD_DPLAY_TONE_FREQ]) == 'F#':
                    frequency = 1475
                if self.match_scale(command[self.CMD_DPLAY_TONE_FREQ]) == 'G':
                    frequency = 1568
                if self.match_scale(command[self.CMD_DPLAY_TONE_FREQ]) == 'G#':
                    frequency = 1661
                if self.match_scale(command[self.CMD_DPLAY_TONE_FREQ]) == 'A':
                    frequency = 1760
                if self.match_scale(command[self.CMD_DPLAY_TONE_FREQ]) == 'Bb':
                    frequency = 1865
                if self.match_scale(command[self.CMD_DPLAY_TONE_FREQ]) == 'B':
                    frequency = 1976
                if self.match_scale(command[self.CMD_DPLAY_TONE_FREQ]) == 'Mute':
                    frequency = 0

            pin = int(command[2])
            if self.digital_poll_list[pin] != self.firmata.TONE_TONE:
                self.digital_poll_list[pin] = self.firmata.TONE_TONE
                self.firmata.set_pin_mode(pin, self.firmata.OUTPUT, self.firmata.DIGITAL)

            if self.digital_poll_list[pin] == self.firmata.TONE_TONE:
                self.firmata.play_tone(pin, self.firmata.TONE_TONE, frequency, sec)
                self.digital_poll_list[pin] = self.firmata.IGNORE
                return 'okay'
            else:
                print 'play_tone: Pin %d was not enabled as TONE.' % pin
                logging.debug('play_tone: Pin %d was not enabled as TONE.' % pin)
                return 'okay'
        elif command[0] == 'buzzer_en':
            command_id = command[1]
            frequency = 0
            sec = int(float(command[3]) * 1000)
            sec2 = float(command[3])

            report_entry = '_busy ID'
            report_entry = report_entry.replace("ID", command_id)
            self.WAITING += report_entry
            self.WAITING += self.end_of_line
            self.start_timer(sec2)

            if command[5] == '1':
                if command[self.CMD_DPLAY_TONE_FREQ_en] == 'C':
                    frequency = 262
                if command[self.CMD_DPLAY_TONE_FREQ_en] == 'C%23':
                    frequency = 278
                if command[self.CMD_DPLAY_TONE_FREQ_en] == 'D':
                    frequency = 294
                if command[self.CMD_DPLAY_TONE_FREQ_en] == 'E%E2%99%AD':
                    frequency = 311
                if command[self.CMD_DPLAY_TONE_FREQ_en] == 'E':
                    frequency = 330
                if command[self.CMD_DPLAY_TONE_FREQ_en] == 'F':
                    frequency = 349
                if command[self.CMD_DPLAY_TONE_FREQ_en] == 'F%23':
                    frequency = 370
                if command[self.CMD_DPLAY_TONE_FREQ_en] == 'G':
                    frequency = 392
                if command[self.CMD_DPLAY_TONE_FREQ_en] == 'G%23':
                    frequency = 415
                if command[self.CMD_DPLAY_TONE_FREQ_en] == 'A':
                    frequency = 440
                if command[self.CMD_DPLAY_TONE_FREQ_en] == 'B%E2%99%AD':
                    frequency = 466
                if command[self.CMD_DPLAY_TONE_FREQ_en] == 'B':
                    frequency = 494
                if command[self.CMD_DPLAY_TONE_FREQ_en] == 'Mute':
                    frequency = 0
            elif command[5] == '2':
                if command[self.CMD_DPLAY_TONE_FREQ_en] == 'C':
                    frequency = 523
                if command[self.CMD_DPLAY_TONE_FREQ_en] == 'C%23':
                    frequency = 554
                if command[self.CMD_DPLAY_TONE_FREQ_en] == 'D':
                    frequency = 587
                if command[self.CMD_DPLAY_TONE_FREQ_en] == 'E%E2%99%AD':
                    frequency = 622
                if command[self.CMD_DPLAY_TONE_FREQ_en] == 'E':
                    frequency = 659
                if command[self.CMD_DPLAY_TONE_FREQ_en] == 'F':
                    frequency = 699
                if command[self.CMD_DPLAY_TONE_FREQ_en] == 'F%23':
                    frequency = 740
                if command[self.CMD_DPLAY_TONE_FREQ_en] == 'G':
                    frequency = 784
                if command[self.CMD_DPLAY_TONE_FREQ_en] == 'G%23':
                    frequency = 831
                if command[self.CMD_DPLAY_TONE_FREQ_en] == 'A':
                    frequency = 880
                if command[self.CMD_DPLAY_TONE_FREQ_en] == 'B%E2%99%AD':
                    frequency = 932
                if command[self.CMD_DPLAY_TONE_FREQ_en] == 'B':
                    frequency = 988
                if command[self.CMD_DPLAY_TONE_FREQ_en] == 'Mute':
                    frequency = 0
            elif command[5] == '3':
                if command[self.CMD_DPLAY_TONE_FREQ_en] == 'C':
                    frequency = 1047
                if command[self.CMD_DPLAY_TONE_FREQ_en] == 'C%23':
                    frequency = 1109
                if command[self.CMD_DPLAY_TONE_FREQ_en] == 'D':
                    frequency = 1175
                if command[self.CMD_DPLAY_TONE_FREQ_en] == 'E%E2%99%AD':
                    frequency = 1245
                if command[self.CMD_DPLAY_TONE_FREQ_en] == 'E':
                    frequency = 1319
                if command[self.CMD_DPLAY_TONE_FREQ_en] == 'F':
                    frequency = 1397
                if command[self.CMD_DPLAY_TONE_FREQ_en] == 'F%23':
                    frequency = 1475
                if command[self.CMD_DPLAY_TONE_FREQ_en] == 'G':
                    frequency = 1568
                if command[self.CMD_DPLAY_TONE_FREQ_en] == 'G%23':
                    frequency = 1661
                if command[self.CMD_DPLAY_TONE_FREQ_en] == 'A':
                    frequency = 1760
                if command[self.CMD_DPLAY_TONE_FREQ_en] == 'B%E2%99%AD':
                    frequency = 1865
                if command[self.CMD_DPLAY_TONE_FREQ_en] == 'B':
                    frequency = 1976
                if command[self.CMD_DPLAY_TONE_FREQ_en] == 'Mute':
                    frequency = 0

            pin = int(command[2])
            if self.digital_poll_list[pin] != self.firmata.TONE_TONE:
                self.digital_poll_list[pin] = self.firmata.TONE_TONE
                self.firmata.set_pin_mode(pin, self.firmata.OUTPUT, self.firmata.DIGITAL)

            if self.digital_poll_list[pin] == self.firmata.TONE_TONE:
                self.firmata.play_tone(pin, self.firmata.TONE_TONE, frequency, sec)
                self.digital_poll_list[pin] = self.firmata.IGNORE
                return 'okay'
            else:
                print 'play_tone: Pin %d was not enabled as TONE.' % pin
                logging.debug('play_tone: Pin %d was not enabled as TONE.' % pin)
                return 'okay'

    def servo_motor_control(self, command):
        command[self.CMD_VALUE] = self.command_translate(command[self.CMD_VALUE])
        pin = int(command[self.CMD_PIN])

        self.digital_poll_list[pin] = self.firmata.SERVO
        self.firmata.servo_config(pin)

        if self.digital_poll_list[pin] == self.firmata.SERVO:
            if 0 <= int(command[self.CMD_SERVO_DEGREES]) <= 180:
                self.firmata.analog_write(pin, int(command[self.CMD_SERVO_DEGREES]))
                self.digital_poll_list[pin] = self.firmata.IGNORE
                return 'okay'
            else:
                print "set_servo_position: Request of %d degrees. Servo range is 0 to 180 degrees" % int(command[1])
                # noinspection PyPep8
                logging.debug("set_servo_position: Request of %d degrees. Servo range is 0 to 180 degrees" % int(command[1]))
                return 'okay'
        else:
            print 'set_servo_position: Pin %d was not enabled for SERVO operations.' % pin
            logging.debug('set_servo_position: Pin %d was not enabled for SERVO operations.' % pin)
            return '_problem Pin was not enabled for SERVO operations.'

    def robot_movement(self, command):
        left_pin3 = 3
        left_pin5 = 5
        right_pin6 = 6
        right_pin11 = 11

        # Left
        self.digital_poll_list[left_pin3] = self.firmata.OUTPUT
        self.firmata.set_pin_mode(left_pin3, self.firmata.OUTPUT, self.firmata.DIGITAL)
        self.digital_poll_list[left_pin5] = self.firmata.OUTPUT
        self.firmata.set_pin_mode(left_pin5, self.firmata.OUTPUT, self.firmata.DIGITAL)
        # Right
        self.digital_poll_list[right_pin6] = self.firmata.OUTPUT
        self.firmata.set_pin_mode(right_pin6, self.firmata.OUTPUT, self.firmata.DIGITAL)
        self.digital_poll_list[right_pin11] = self.firmata.OUTPUT
        self.firmata.set_pin_mode(right_pin11, self.firmata.OUTPUT, self.firmata.DIGITAL)

        if command[0] == 'robot_movement_timer':
            if self.DIRECTION(command[1]) == 'Forward':
                self.DC_FORWARD = True
                self.DC_REVERSE = False
                self.firmata.digital_write(left_pin3, self.DIGITAL_OFF)
                self.digital_poll_list[left_pin3] = self.firmata.IGNORE
                self.firmata.digital_write(left_pin5, self.DIGITAL_ON)

                self.firmata.digital_write(right_pin6, self.DIGITAL_ON)
                self.firmata.digital_write(right_pin11, self.DIGITAL_OFF)
                self.digital_poll_list[right_pin11] = self.firmata.IGNORE
            elif self.DIRECTION(command[1]) == 'Reverse':
                self.DC_FORWARD = False
                self.DC_REVERSE = True
                self.firmata.digital_write(left_pin3, self.DIGITAL_ON)
                self.firmata.digital_write(left_pin5, self.DIGITAL_OFF)
                self.digital_poll_list[left_pin5] = self.firmata.IGNORE

                self.firmata.digital_write(right_pin6, self.DIGITAL_OFF)
                self.digital_poll_list[right_pin6] = self.firmata.IGNORE
                self.firmata.digital_write(right_pin11, self.DIGITAL_ON)
            elif self.LEFT_RIGHT(command[1]) == 'Left':
                self.DC_FORWARD = False
                self.DC_REVERSE = False
                self.firmata.digital_write(left_pin3, self.DIGITAL_OFF)
                self.firmata.digital_write(left_pin5, self.DIGITAL_OFF)
                self.digital_poll_list[left_pin3] = self.firmata.IGNORE
                self.digital_poll_list[left_pin5] = self.firmata.IGNORE

                self.firmata.digital_write(right_pin6, self.DIGITAL_ON)
                self.firmata.digital_write(right_pin11, self.DIGITAL_OFF)
                self.digital_poll_list[right_pin11] = self.firmata.IGNORE
            elif self.LEFT_RIGHT(command[1]) == 'Right':
                self.DC_FORWARD = False
                self.DC_REVERSE = False
                self.firmata.digital_write(left_pin3, self.DIGITAL_OFF)
                self.digital_poll_list[left_pin3] = self.firmata.IGNORE
                self.firmata.digital_write(left_pin5, self.DIGITAL_ON)

                self.firmata.digital_write(right_pin6, self.DIGITAL_OFF)
                self.firmata.digital_write(right_pin11, self.DIGITAL_OFF)
                self.digital_poll_list[right_pin6] = self.firmata.IGNORE
                self.digital_poll_list[right_pin11] = self.firmata.IGNORE
            return 'okay'
        elif command[0] == 'robot_movement_timer_en':
            if command[1] == 'Forward':
                self.DC_FORWARD = True
                self.DC_REVERSE = False
                self.firmata.digital_write(left_pin3, self.DIGITAL_OFF)
                self.digital_poll_list[left_pin3] = self.firmata.IGNORE
                self.firmata.digital_write(left_pin5, self.DIGITAL_ON)

                self.firmata.digital_write(right_pin6, self.DIGITAL_ON)
                self.firmata.digital_write(right_pin11, self.DIGITAL_OFF)
                self.digital_poll_list[right_pin11] = self.firmata.IGNORE
            elif command[1] == 'Backward':
                self.DC_FORWARD = False
                self.DC_REVERSE = True
                self.firmata.digital_write(left_pin3, self.DIGITAL_ON)
                self.firmata.digital_write(left_pin5, self.DIGITAL_OFF)
                self.digital_poll_list[left_pin5] = self.firmata.IGNORE

                self.firmata.digital_write(right_pin6, self.DIGITAL_OFF)
                self.digital_poll_list[right_pin6] = self.firmata.IGNORE
                self.firmata.digital_write(right_pin11, self.DIGITAL_ON)
            elif command[1] == 'Turn%20left':
                self.DC_FORWARD = False
                self.DC_REVERSE = False
                self.firmata.digital_write(left_pin3, self.DIGITAL_OFF)
                self.firmata.digital_write(left_pin5, self.DIGITAL_OFF)
                self.digital_poll_list[left_pin3] = self.firmata.IGNORE
                self.digital_poll_list[left_pin5] = self.firmata.IGNORE

                self.firmata.digital_write(right_pin6, self.DIGITAL_ON)
                self.firmata.digital_write(right_pin11, self.DIGITAL_OFF)
                self.digital_poll_list[right_pin11] = self.firmata.IGNORE
            elif command[1] == 'Turn%20right':
                self.DC_FORWARD = False
                self.DC_REVERSE = False
                self.firmata.digital_write(left_pin3, self.DIGITAL_OFF)
                self.digital_poll_list[left_pin3] = self.firmata.IGNORE
                self.firmata.digital_write(left_pin5, self.DIGITAL_ON)

                self.firmata.digital_write(right_pin6, self.DIGITAL_OFF)
                self.firmata.digital_write(right_pin11, self.DIGITAL_OFF)
                self.digital_poll_list[right_pin6] = self.firmata.IGNORE
                self.digital_poll_list[right_pin11] = self.firmata.IGNORE
            return 'okay'
        elif command[0] == 'robot_movement':
            if command[1] == 'Forward':
                self.DC_FORWARD = True
                self.DC_REVERSE = False
                self.firmata.digital_write(left_pin3, self.DIGITAL_OFF)
                self.digital_poll_list[left_pin3] = self.firmata.IGNORE
                self.firmata.digital_write(left_pin5, self.DIGITAL_ON)

                self.firmata.digital_write(right_pin6, self.DIGITAL_ON)
                self.firmata.digital_write(right_pin11, self.DIGITAL_OFF)
                self.digital_poll_list[right_pin11] = self.firmata.IGNORE
            elif command[1] == 'Backward':
                self.DC_FORWARD = False
                self.DC_REVERSE = True
                self.firmata.digital_write(left_pin3, self.DIGITAL_ON)
                self.firmata.digital_write(left_pin5, self.DIGITAL_OFF)
                self.digital_poll_list[left_pin5] = self.firmata.IGNORE

                self.firmata.digital_write(right_pin6, self.DIGITAL_OFF)
                self.digital_poll_list[right_pin6] = self.firmata.IGNORE
                self.firmata.digital_write(right_pin11, self.DIGITAL_ON)
            elif command[1] == 'Turn%20left':
                self.DC_FORWARD = False
                self.DC_REVERSE = False
                self.firmata.digital_write(left_pin3, self.DIGITAL_OFF)
                self.firmata.digital_write(left_pin5, self.DIGITAL_OFF)
                self.digital_poll_list[left_pin3] = self.firmata.IGNORE
                self.digital_poll_list[left_pin5] = self.firmata.IGNORE

                self.firmata.digital_write(right_pin6, self.DIGITAL_ON)
                self.firmata.digital_write(right_pin11, self.DIGITAL_OFF)
                self.digital_poll_list[right_pin11] = self.firmata.IGNORE
            elif command[1] == 'Turn%20right':
                self.DC_FORWARD = False
                self.DC_REVERSE = False
                self.firmata.digital_write(left_pin3, self.DIGITAL_OFF)
                self.digital_poll_list[left_pin3] = self.firmata.IGNORE
                self.firmata.digital_write(left_pin5, self.DIGITAL_ON)

                self.firmata.digital_write(right_pin6, self.DIGITAL_OFF)
                self.firmata.digital_write(right_pin11, self.DIGITAL_OFF)
                self.digital_poll_list[right_pin6] = self.firmata.IGNORE
                self.digital_poll_list[right_pin11] = self.firmata.IGNORE
            return 'okay'


    def robot_movement_timer(self, command):
        # command: ['robot_movement_timer', ID, time, moving]
        # command_en: ['robot_movement_timer_en', ID, moving, time]
        if command[0] == 'robot_movement_timer':
            report_entry = '_busy ID'
            report_entry = report_entry.replace("ID", command[1])
            self.WAITING += report_entry

            timer = float(command[2])
            command.remove(command[1])
            command.remove(command[1])
            self.robot_movement(command)
            self.robot_timer(timer)
            return 'okay'
        elif command[0] == 'robot_movement_timer_en':
            report_entry = '_busy ID'
            report_entry = report_entry.replace("ID", command[1])
            self.WAITING += report_entry

            timer = float(command[3])
            command.remove(command[1])
            command.remove(command[2])
            self.robot_movement(command)
            self.robot_timer(timer)
            return 'okay'

    def _robot_stop(self):
        left_pin3 = 3
        left_pin5 = 5
        right_pin6 = 6
        right_pin11 = 11

        self.firmata.digital_write(left_pin3, self.DIGITAL_OFF)
        self.firmata.digital_write(left_pin5, self.DIGITAL_OFF)
        self.firmata.digital_write(right_pin6, self.DIGITAL_OFF)
        self.firmata.digital_write(right_pin11, self.DIGITAL_OFF)
        # disable pin of any type by setting it to IGNORE in the table
        self.digital_poll_list[left_pin3] = self.firmata.IGNORE
        self.digital_poll_list[left_pin5] = self.firmata.IGNORE
        self.digital_poll_list[right_pin6] = self.firmata.IGNORE
        self.digital_poll_list[right_pin11] = self.firmata.IGNORE
        # this only applies to Input pins. For all other pins we leave the poll list as is
        # self.firmata.disable_digital_reporting(pin)

    def wheel_speed(self, command):
        left_pin3 = 3
        left_pin5 = 5
        right_pin6 = 6
        right_pin11 = 11

        # 아날로그 값 범위를 변경 블록을 사용할 경우 결과값이 URL 인코딩 문자로 입력되기 때문에 번역이 필요합니다.
        command[1] = self.command_translate(command[1])
        command[self.CMD_VALUE] = self.command_translate(command[self.CMD_VALUE])

        # Left
        self.digital_poll_list[left_pin3] = self.firmata.PWM
        self.firmata.set_pin_mode(left_pin3, self.firmata.PWM, self.firmata.DIGITAL)
        self.digital_poll_list[left_pin5] = self.firmata.PWM
        self.firmata.set_pin_mode(left_pin5, self.firmata.PWM, self.firmata.DIGITAL)
        # Right
        self.digital_poll_list[right_pin6] = self.firmata.PWM
        self.firmata.set_pin_mode(right_pin6, self.firmata.PWM, self.firmata.DIGITAL)
        self.digital_poll_list[right_pin11] = self.firmata.PWM
        self.firmata.set_pin_mode(right_pin11, self.firmata.PWM, self.firmata.DIGITAL)

        right_wheel_speed = int(float(command[1]))
        left_wheel_speed = int(float(command[2]))

        if command[1] and command[2] == 'VAL':
            logging.debug('analog_write: The value field must be set to a numerical value')
            print 'analog_write: The value field must be set to a numerical value'
            return 'okay'

        # check to make sure that the value is in the range of 0-255
        if 0 <= right_wheel_speed and left_wheel_speed <= 100:
            right_speed = int(right_wheel_speed * 2.55)
            left_speed = int(left_wheel_speed * 2.55)

            if left_speed >= 90:
                if self.DC_FORWARD is True:
                    self.firmata.analog_write(left_pin3, self.DIGITAL_OFF)
                    self.firmata.analog_write(left_pin5, left_speed)
                elif self.DC_REVERSE is True:
                    self.firmata.analog_write(left_pin3, left_speed)
                    self.firmata.analog_write(left_pin5, self.DIGITAL_OFF)
            if right_speed >= 90:
                if self.DC_FORWARD is True:
                    self.firmata.analog_write(right_pin6, right_speed)
                    self.firmata.analog_write(right_pin11, self.DIGITAL_OFF)
                elif self.DC_REVERSE is True:
                    self.firmata.analog_write(right_pin6, self.DIGITAL_OFF)
                    self.firmata.analog_write(right_pin11, right_speed)

            if 0 < left_speed < 90:
                if self.DC_FORWARD is True:
                    self.firmata.analog_write(left_pin3, self.DIGITAL_OFF)
                    self.firmata.analog_write(left_pin5, 90)
                elif self.DC_REVERSE is True:
                    self.firmata.analog_write(left_pin3, 90)
                    self.firmata.analog_write(left_pin5, self.DIGITAL_OFF)
            if 0 < right_speed < 90:
                if self.DC_FORWARD is True:
                    self.firmata.analog_write(right_pin6, 90)
                    self.firmata.analog_write(right_pin11, self.DIGITAL_OFF)
                elif self.DC_REVERSE is True:
                    self.firmata.analog_write(right_pin6, self.DIGITAL_OFF)
                    self.firmata.analog_write(right_pin11, 90)

            if left_speed == 0:
                self.firmata.digital_write(left_pin3, self.DIGITAL_OFF)
                self.firmata.digital_write(left_pin5, self.DIGITAL_OFF)
                # disable pin of any type by setting it to IGNORE in the table
                self.digital_poll_list[left_pin3] = self.firmata.IGNORE
                self.digital_poll_list[left_pin5] = self.firmata.IGNORE
            if right_speed == 0:
                self.firmata.digital_write(right_pin6, self.DIGITAL_OFF)
                self.firmata.digital_write(right_pin11, self.DIGITAL_OFF)
                # disable pin of any type by setting it to IGNORE in the table
                self.digital_poll_list[right_pin6] = self.firmata.IGNORE
                self.digital_poll_list[right_pin11] = self.firmata.IGNORE

        else:
            print 'analog_write data value %d is out of range. It should be between 0-255' % \
                int(command[self.CMD_VALUE])
            logging.debug('analog_write data value %d is out of range. It should be between 0-255' %
                          int(command[self.CMD_VALUE]))
            return '_problem analog_write data value %d is out of range. It should be between 0-255' % \
                   int(command[self.CMD_VALUE])
        return 'okay'

    def robot_stop(self, command):
        left_pin3 = 3
        left_pin5 = 5
        right_pin6 = 6
        right_pin11 = 11

        self.firmata.digital_write(left_pin3, self.DIGITAL_OFF)
        self.firmata.digital_write(left_pin5, self.DIGITAL_OFF)
        self.firmata.digital_write(right_pin6, self.DIGITAL_OFF)
        self.firmata.digital_write(right_pin11, self.DIGITAL_OFF)

        self.firmata.analog_write(left_pin3, self.DIGITAL_OFF)
        self.firmata.analog_write(left_pin5, self.DIGITAL_OFF)
        self.firmata.analog_write(right_pin6, self.DIGITAL_OFF)
        self.firmata.analog_write(right_pin11, self.DIGITAL_OFF)

        # disable pin of any type by setting it to IGNORE in the table
        self.digital_poll_list[left_pin3] = self.firmata.IGNORE
        self.digital_poll_list[left_pin5] = self.firmata.IGNORE
        self.digital_poll_list[right_pin6] = self.firmata.IGNORE
        self.digital_poll_list[right_pin11] = self.firmata.IGNORE
        return 'okay'

    def start_timer(self, wait_time):
        timer = threading.Timer(wait_time + 0.1, self.start_timer, args=[self.COUNT])
        timer.daemon = True

        self.COUNT += 1
        if self.COUNT == 2:
            self.WAITING = ''
            self.COUNT = 0
            timer.cancel()
        timer.start()

    def robot_timer(self, wait_time):
        timer = threading.Timer((float(wait_time)+0.1), self.robot_timer, args=[float(wait_time)])
        self.COUNT += 1

        if self.COUNT > 1:
            self.WAITING = ''
            self.COUNT = 0
            self._robot_stop()
            timer.cancel()

        timer.start()

    def wait_function(self, command):
        """
        이 메소드는 사용하지 않지만, wait 타입 블록을 정의할 때 참고하려고 만들어 놓았습니다.
        polling 에 _busy (command ID)가 있으면, 해당되는 ID의 명령어가 완료될 때 까지 다른 명령어는 대기합니다.
        _busy가 없으면 다시 다른 명령어들이 차례로 동작합니다.
        :param command: command[1]: command ID
        """
        func_id = command[1]
        wait_time = command[2]
        self.start_timer(wait_time)

        report_entry = '_busy ID'
        report_entry = report_entry.replace("ID", func_id)
        self.WAITING += report_entry

        if self.WAITING == '':
            return 'okay'

    def analog_value_change(self, command):
        """
        이 메소드는 아날로그 값 범위 변경하는 기능을 수행합니다.
        이 메소드를 활용해 새 블록을 정의할 때는 블록 타입을 "R" 로 해야합니다.
        :param command: command[1]: 아날로그 핀번호, command[2] ~ command[5]: 범위값
        :return: 계산 결과값(문자형) // 숫자형으로 return 하면 스크래치에서 결과값을 받을 수가 없습니다.
        """
        analog_response_table = self.firmata.get_analog_response_table()
        value = ''

        for pin in range(self.number_of_analog_pins_discovered):
            if pin == int(command[self.CMD_PIN]):
                pin_entry = analog_response_table[pin]

                analog_value_original = int(pin_entry[self.ENTRY_VALUE])
                analog_value_start = int(command[2])
                analog_value_end = int(command[3])
                analog_value_change_start = int(command[4])
                analog_value_change_end = int(command[5])
                first_value = float(analog_value_end - analog_value_start)
                second_value = float(analog_value_change_end - analog_value_change_start)
                rate = float(second_value / first_value)
                data = float(rate * (analog_value_original - analog_value_start))
                value += str(analog_value_change_start + data)
                return value

    # Dplay plus block
    def dplay_plus_rgb(self, command):
        CMD_RED_VALUE = 1
        CMD_GREEN_VALUE = 2
        CMD_BLUE_VALUE = 3

        red_pin = 11
        green_pin = 10
        blue_pin = 9

        red_value = int(float(command[CMD_RED_VALUE]))
        green_value = int(float(command[CMD_GREEN_VALUE]))
        blue_value = int(float(command[CMD_BLUE_VALUE]))

        red_ok = False
        green_ok = False
        blue_ok = False

        self.digital_poll_list[red_pin] = self.firmata.PWM
        self.firmata.set_pin_mode(red_pin, self.firmata.PWM, self.firmata.DIGITAL)
        self.digital_poll_list[green_pin] = self.firmata.PWM
        self.firmata.set_pin_mode(green_pin, self.firmata.PWM, self.firmata.DIGITAL)
        self.digital_poll_list[blue_pin] = self.firmata.PWM
        self.firmata.set_pin_mode(blue_pin, self.firmata.PWM, self.firmata.DIGITAL)

        if self.ON_OFF(command[4]) == 'On':
            # RED
            if self.digital_poll_list[red_pin] == self.firmata.PWM:
                if 0 <= red_value <= 255:
                    self.firmata.analog_write(red_pin, red_value)
                    red_ok = True
                else:
                    print 'analog_write data value %d is out of range. It should be between 0-255' % red_value
                    logging.debug('analog_write data value %d is out of range. It should be between 0-255' % red_value)
            # GREEN
            if self.digital_poll_list[green_pin] == self.firmata.PWM:
                if 0 <= green_pin <= 255:
                    self.firmata.analog_write(green_pin, green_value)
                    green_ok = True
                else:
                    print 'analog_write data value %d is out of range. It should be between 0-255' % green_value
                    logging.debug('analog_write data value %d is out of range. It should be between 0-255' % green_value)
            # BLUE
            if self.digital_poll_list[blue_pin] == self.firmata.PWM:
                if 0 <= blue_pin <= 255:
                    self.firmata.analog_write(blue_pin, blue_value)
                    blue_ok = True
                    if red_ok and green_ok and blue_ok is True:
                        return 'okay'
                else:
                    print 'analog_write data value %d is out of range. It should be between 0-255' % blue_value
                    logging.debug('analog_write data value %d is out of range. It should be between 0-255' % blue_value)
                    return '_problem analog_write data value %d is out of range. It should be between 0-255' % blue_value
        elif self.ON_OFF(command[4]) == 'Off':
            self.firmata.digital_write(red_pin, self.DIGITAL_OFF)
            self.firmata.digital_write(green_pin, self.DIGITAL_OFF)
            self.firmata.digital_write(blue_pin, self.DIGITAL_OFF)
        return 'okay'

    def dplay_plus_servo(self, command):
        pin = 4

        self.digital_poll_list[pin] = self.firmata.SERVO
        self.firmata.servo_config(pin)

        if self.digital_poll_list[pin] == self.firmata.SERVO:
            if 0 <= int(command[1]) <= 180:
                self.firmata.analog_write(pin, int(command[1]))
                self.digital_poll_list[pin] = self.firmata.IGNORE
                return 'okay'
            else:
                if int(command[1]) < 0:
                    self.firmata.analog_write(pin, 0)
                if int(command[1]) > 180:
                    self.firmata.analog_write(pin, 180)
                # print "set_servo_position: Request of %d degrees. Servo range is 0 to 180 degrees" % int(command[1])
                # # noinspection PyPep8
                # logging.debug(
                #     "set_servo_position: Request of %d degrees. Servo range is 0 to 180 degrees" % int(command[1]))
                return 'okay'
        else:
            print 'set_servo_position: Pin %d was not enabled for SERVO operations.' % pin
            logging.debug('set_servo_position: Pin %d was not enabled for SERVO operations.' % pin)
            return '_problem Pin was not enabled for SERVO operations.'

    def dplay_plus_play(self, command):
        pin = 19

        # if self.digital_poll_list[pin] != self.firmata.OUTPUT:
        #     self.digital_poll_list[pin] = self.firmata.OUTPUT
            # self.firmata.set_pin_mode(pin, self.firmata.OUTPUT, self.firmata.DIGITAL)

        if self.digital_poll_list[pin] == self.firmata.OUTPUT:
            self.firmata.digital_write(pin, self.DIGITAL_ON)
            self.firmata.digital_write(pin, self.DIGITAL_OFF)
            return 'okay'
        return 'okay'

    def dplay_plus_recording(self, command):
        pin = 18
        command_id = command[1]

        sec = int(float(command[2]) * 1000)
        sec2 = float(command[2])

        report_entry = '_busy ID'
        report_entry = report_entry.replace("ID", command_id)

        self.WAITING += report_entry
        self.WAITING += self.end_of_line

        self.start_timer(sec2)
        self.cancel_timer(sec2)

        if self.digital_poll_list[pin] != self.firmata.OUTPUT:
            self.digital_poll_list[pin+1] = self.firmata.OUTPUT
            self.digital_poll_list[pin] = self.firmata.OUTPUT

            self.firmata.set_pin_mode(pin+1, self.firmata.OUTPUT, self.firmata.DIGITAL)
            self.firmata.set_pin_mode(pin, self.firmata.OUTPUT, self.firmata.DIGITAL)

        if self.digital_poll_list[pin] == self.firmata.OUTPUT:
            self.firmata.digital_write(pin, self.DIGITAL_ON)
            return 'okay'

        print command

    def cancel_timer(self, sec):
        timer = threading.Timer(sec, self.cancel_timer, args=[self.CANCEL_COUNT])
        timer.daemon = True

        self.CANCEL_COUNT += 1
        if self.CANCEL_COUNT == 2:
            self.CANCEL_COUNT = 0
            self.firmata.digital_write(18, self.DIGITAL_OFF)
            # self.digital_poll_list[5] = self.firmata.IGNORE
            timer.cancel()
        timer.start()

    # This table must be at the bottom of the file because Python does not provide forward referencing for
    # the methods defined above.
    command_dict = {'crossdomain.xml': send_cross_domain_policy, 'reset_all': reset_arduino,
                    'analog_pin_mode': analog_pin_mode, 'analog_pin_mode_en': analog_pin_mode,
                    'digital_pin_mode': digital_pin_mode, 'digital_pin_mode_en': digital_pin_mode,
                    'digital_pin_mode_ja': digital_pin_mode_ja,
                    'analog_pin_mode_ja': analog_pin_mode_ja,
                    'digital_pin_on_off': digital_on_off, 'digital_pin_on_off_en': digital_on_off,
                    'LED_control': LED_control, 'LED_control_en': LED_control,
                    'digital_write': digital_write, 'analog_write': analog_write,
                    'play_tone': play_tone, 'tone_off': tone_off,
                    'set_servo_position': set_servo_position, 'poll': poll,
                    'debugger': debug_control,  'digital_read': digital_read, 'analog_read': analog_read,
                    'motor_direction': motor_direction, 'motor_direction_en': motor_direction,
                    'motor_speed_control': motor_speed_control,
                    'buzzer': buzzer, 'buzzer_en': buzzer,
                    'servo_motor_control': servo_motor_control, 'robot_movement': robot_movement,
                    'robot_movement_timer': robot_movement_timer, 'robot_movement_timer_en': robot_movement_timer,
                    'robot_stop': robot_stop,
                    'wheel_speed': wheel_speed,
                    'wait_function': wait_function,
                    'analog_value_change': analog_value_change,

                    'dplay_plus_rgb': dplay_plus_rgb, 'dplay_plus_servo': dplay_plus_servo,
                    'dplay_plus_play': dplay_plus_play, 'dplay_plus_recording': dplay_plus_recording,
                    }
