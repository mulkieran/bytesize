# Copyright (C) 2015  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# the GNU General Public License v.2, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.  You should have received a copy of the
# GNU General Public License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.  Any Red Hat trademarks that are incorporated in the
# source code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission of
# Red Hat, Inc.
#
# Red Hat Author(s): Anne Mulhern <amulhern@redhat.com>

""" Test for configuration classes. """
import unittest

from decimal import Decimal
from fractions import Fraction

from bytesize._constants import RoundingMethods
from bytesize._errors import SizeValueError
from bytesize._util import format_magnitude
from bytesize._util import round_fraction

class FormatTestCase(unittest.TestCase):
    """ Test formatting. """
    # pylint: disable=too-few-public-methods

    def testException(self):
        """ Raises exception on bad input. """
        with self.assertRaises(SizeValueError):
            format_magnitude(Decimal(200), max_places=-1)
        with self.assertRaises(SizeValueError):
            format_magnitude(0.1)

class RoundingTestCase(unittest.TestCase):
    """ Test rounding of fraction. """
    # pylint: disable=too-few-public-methods

    def testExceptions(self):
        """ Raises exception on bad input. """
        with self.assertRaises(SizeValueError):
            round_fraction(Fraction(13, 32), "a string")
        with self.assertRaises(SizeValueError):
            round_fraction(Fraction(16, 32), "a string")

    def testRounding(self):
        """ Rounding various values according to various methods. """
        for i in range(1, 10):
            f = Fraction(i, 10)
            self.assertEqual(round_fraction(f, RoundingMethods.ROUND_DOWN), 0)
            self.assertEqual(round_fraction(f, RoundingMethods.ROUND_UP), 1)

            r = round_fraction(f, RoundingMethods.ROUND_HALF_UP)
            if i < 5:
                self.assertEqual(r, 0)
            else:
                self.assertEqual(r, 1)

            r = round_fraction(f, RoundingMethods.ROUND_HALF_DOWN)
            if i > 5:
                self.assertEqual(r, 1)
            else:
                self.assertEqual(r, 0)
