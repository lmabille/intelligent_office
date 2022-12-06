import unittest
from unittest.mock import patch
import mock.GPIO as GPIO
from mock.RTC import RTC
from IntelligentOffice import IntelligentOffice
from IntelligentOfficeError import IntelligentOfficeError


class IntelligentOfficeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.intelOff = IntelligentOffice()

    @patch.object(GPIO, 'input')
    def test_occupancy_quadrant1(self, mock_input):
        mock_input.return_value = 52
        occ = self.intelOff.check_quadrant_occupancy(IntelligentOffice.INFRARED_PIN_1)
        self.assertTrue(occ)


    @patch.object(GPIO, 'input')
    def test_occupancy_quadrant1_not_present(self, mock_input):
        mock_input.return_value = 0
        occ = self.intelOff.check_quadrant_occupancy(IntelligentOffice.INFRARED_PIN_1)
        self.assertFalse(occ)

    def test_occupancy_invalid_pin(self):
        self.assertRaises(IntelligentOfficeError, self.intelOff.check_quadrant_occupancy, -1)

    @patch.object(RTC, 'get_current_day')
    @patch.object(RTC, 'get_current_time_string')
    def test_open_garage_door(self, mock_rtc_time, mock_rtc_day):
        mock_rtc_time.return_value = '11:20:28'
        mock_rtc_day.return_value = 'MONDAY'
        self.intelOff.manage_blinds_based_on_time()
        self.assertEqual(self.intelOff.blinds_open, 'OPENED')

    @patch.object(RTC, 'get_current_day')
    @patch.object(RTC, 'get_current_time_string')
    def test_closed_garage_door(self, mock_rtc_time, mock_rtc_day):
        mock_rtc_time.return_value = '11:20:28'
        mock_rtc_day.return_value = 'SUNDAY'
        self.intelOff.manage_blinds_based_on_time()
        self.assertEqual(self.intelOff.blinds_open, 'CLOSED')

