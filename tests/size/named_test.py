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

""" Tests for named methods of Size objects. """

import unittest

from fractions import Fraction

from bytesize import Size
from bytesize import B
from bytesize import KiB
from bytesize import MiB
from bytesize import GiB
from bytesize import TiB
from bytesize import ROUND_DOWN
from bytesize import ROUND_HALF_UP
from bytesize import ROUND_UP

from bytesize._constants import BinaryUnits

from bytesize._errors import SizeValueError

class ConversionTestCase(unittest.TestCase):
    """ Test conversion methods. """

    def testConvertToPrecision(self):
        """ Test convertTo method. """
        s = Size(1835008)
        self.assertEqual(s.convertTo(None), Fraction(1835008))
        self.assertEqual(s.convertTo(B), Fraction(1835008))
        self.assertEqual(s.convertTo(KiB), Fraction(1792))
        self.assertEqual(s.convertTo(MiB), Fraction(7, 4))

    def testConvertToWithSize(self):
        """ Test convertTo method when conversion target is a Size. """
        s = Size(1835008)
        self.assertEqual(s.convertTo(Size(1)), s.convertTo(B))
        self.assertEqual(s.convertTo(Size(1024)), s.convertTo(KiB))
        self.assertEqual(Size(512).convertTo(Size(1024)), Fraction(1, 2))
        self.assertEqual(Size(1024).convertTo(Size(512)), Fraction(2, 1))

        with self.assertRaises(SizeValueError):
            s.convertTo(Size(0))

    def testConvertToLargeSize(self):
        """ Test that conversion maintains precision for large sizes. """
        s = Size(0xfffffffffffff)
        value = int(s)
        for u in BinaryUnits.UNITS():
            self.assertEqual(s.convertTo(u) * u.factor, value)

class RoundingTestCase(unittest.TestCase):
    """ Test rounding methods. """

    def testRoundTo(self):
        """ Test roundTo method. """

        s = Size("10.3", GiB)
        self.assertEqual(s.roundTo(GiB, rounding=ROUND_HALF_UP), Size(10, GiB))
        self.assertEqual(s.roundTo(GiB, rounding=ROUND_HALF_UP),
                         Size(10, GiB))
        self.assertEqual(s.roundTo(GiB, rounding=ROUND_DOWN),
                         Size(10, GiB))
        self.assertEqual(s.roundTo(GiB, rounding=ROUND_UP),
                         Size(11, GiB))
        # >>> Size("10.3 GiB").convertTo(MiB)
        # Decimal('10547.19999980926513671875')
        self.assertEqual(s.roundTo(MiB, rounding=ROUND_HALF_UP), Size(10547, MiB))
        self.assertEqual(s.roundTo(MiB, rounding=ROUND_UP),
                         Size(10548, MiB))
        self.assertIsInstance(s.roundTo(MiB, rounding=ROUND_HALF_UP), Size)
        with self.assertRaises(SizeValueError):
            s.roundTo(MiB, rounding='abc')

        # arbitrary decimal rounding constants are not allowed
        from decimal import ROUND_HALF_DOWN
        with self.assertRaises(SizeValueError):
            s.roundTo(MiB, rounding=ROUND_HALF_DOWN)

        s = Size("10.51", GiB)
        self.assertEqual(s.roundTo(GiB, rounding=ROUND_HALF_UP), Size(11, GiB))
        self.assertEqual(s.roundTo(GiB, rounding=ROUND_HALF_UP),
                         Size(11, GiB))
        self.assertEqual(s.roundTo(GiB, rounding=ROUND_DOWN),
                         Size(10, GiB))
        self.assertEqual(s.roundTo(GiB, rounding=ROUND_UP),
                         Size(11, GiB))

        s = Size(513, GiB)
        self.assertEqual(s.roundTo(GiB, rounding=ROUND_HALF_UP), s)
        self.assertEqual(s.roundTo(TiB, rounding=ROUND_HALF_UP), Size(1, TiB))
        self.assertEqual(s.roundTo(TiB, rounding=ROUND_DOWN),
                         Size(0))

    def testSizeParams(self):
        """ Test rounding with Size parameters. """
        s = Size(513, GiB)
        self.assertEqual(s.roundTo(Size(128, GiB), rounding=ROUND_HALF_UP), Size(512, GiB))
        self.assertEqual(s.roundTo(Size(1, KiB), rounding=ROUND_HALF_UP), Size(513, GiB))
        self.assertEqual(s.roundTo(Size(1, TiB), rounding=ROUND_HALF_UP), Size(1, TiB))
        self.assertEqual(s.roundTo(Size(1, TiB), rounding=ROUND_DOWN), Size(0))
        self.assertEqual(s.roundTo(Size(0), rounding=ROUND_HALF_UP), Size(0))
        self.assertEqual(s.roundTo(Size(13, GiB), rounding=ROUND_HALF_UP), Size(507, GiB))

    def testExceptions(self):
        """ Test raising exceptions when rounding. """
        s = Size(513, GiB)
        with self.assertRaises(SizeValueError):
            s.roundTo(Size(-1, B), rounding=ROUND_HALF_UP)
