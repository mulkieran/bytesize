#!/usr/bin/python
#
# size_tests.py
# Size test cases for bytesize package.
#
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

""" Tests for behavior of Size objects. """

import copy
import unittest

from decimal import Decimal

from bytesize import Size
from bytesize import B
from bytesize import KiB
from bytesize import MiB
from bytesize import GiB
from bytesize import TiB
from bytesize import ROUND_DOWN
from bytesize import ROUND_HALF_UP
from bytesize import ROUND_UP
from bytesize import StrConfig

from bytesize.config import Defaults

from bytesize.errors import SizeNonsensicalBinOpError
from bytesize.errors import SizeNonsensicalOpError
from bytesize.errors import SizePowerResultError
from bytesize.errors import SizeValueError

class ConstructionTestCase(unittest.TestCase):
    """ Test construction of Size objects. """

    def testZero(self):
        """ Test construction with 0 as decimal. """
        zero = Size(0)
        self.assertEqual(zero, Size("0.0"))


    def testNegative(self):
        """ Test construction of negative sizes. """
        s = Size(-500, MiB)
        self.assertEqual(s.humanReadableComponents(), ("-500", "Mi"))
        self.assertEqual(s.convertTo(B), -524288000)

    def testPartialBytes(self):
        """ Test rounding of partial bytes in constructor. """
        self.assertEqual(Size("1024.6"), Size(1024))
        self.assertEqual(Size(1/Decimal(1025), KiB), Size(0))
        self.assertEqual(Size(1/Decimal(1023), KiB), Size(1))

    def testConstructor(self):
        """ Test error checking in constructo. """
        with self.assertRaises(SizeValueError):
            Size("1.1.1", KiB)
        self.assertEqual(Size(Size(0)), Size(0))
        with self.assertRaises(SizeValueError):
            Size(Size(0), KiB)
        with self.assertRaises(SizeValueError):
            Size(B)

    def testNoUnitsInString(self):
        """ Test construction w/ no units specified. """
        self.assertEqual(Size("1024"), Size(1, KiB))

class DisplayTestCase(unittest.TestCase):
    """ Test formatting Size for display. """

    def testHumanReadable(self):
        """ Test construction of display components. """
        s = Size(58929971)
        self.assertEqual(s.humanReadableComponents(), ("56.2", "Mi"))

        s = Size(478360371)
        self.assertEqual(s.humanReadableComponents(), ("456.2", "Mi"))

        # humanReable output should be the same as input for big enough sizes
        # and enough places and integer values
        s = Size("12.68", TiB)
        self.assertEqual(s.humanReadableComponents(max_places=2), ("12.68", "Ti"))
        s = Size("26.55", MiB)
        self.assertEqual(s.humanReadableComponents(max_places=2), ("26.55", "Mi"))
        s = Size(300, MiB)
        self.assertEqual(s.humanReadableComponents(max_places=2), ("300", "Mi"))

        # when min_value is 10 and single digit on left of decimal, display
        # with smaller unit.
        s = Size('9.68', TiB)
        self.assertEqual(s.humanReadableComponents(max_places=2, min_value=10), ("9912.32", "Gi"))
        s = Size('4.29', MiB)
        self.assertEqual(s.humanReadableComponents(max_places=2, min_value=10), ("4392.96", "Ki"))
        s = Size('7.18', KiB)
        self.assertEqual(s.humanReadableComponents(max_places=2, min_value=10), ("7352", ""))

        # rounding should work with max_places limitted
        s = Size('12.687', TiB)
        self.assertEqual(s.humanReadableComponents(max_places=2), ("12.69", "Ti"))
        s = Size('23.7874', TiB)
        self.assertEqual(s.humanReadableComponents(max_places=3), ("23.787", "Ti"))
        s = Size('12.6998', TiB)
        self.assertEqual(s.humanReadableComponents(max_places=2), ("12.7", "Ti"))

        # byte values close to multiples of 2 are shown without trailing zeros
        s = Size(0xff)
        self.assertEqual(s.humanReadableComponents(max_places=2), ("255", ""))
        s = Size(8193)
        self.assertEqual(s.humanReadableComponents(max_places=2, min_value=10), ("8193", ""))

        # a fractional quantity is shown if the value deviates
        # from the whole number of units by more than 1%
        s = Size(16384 - (Decimal(1024)/100 + 1))
        self.assertEqual(s.humanReadableComponents(max_places=2), ("15.99", "Ki"))

        # if max_places is set to None, all digits are displayed
        s = Size(0xfffffffffffff)
        self.assertEqual(
           s.humanReadableComponents(max_places=None),
           ("3.9999999999999991118215803", "Pi")
        )
        s = Size(0x10000)
        self.assertEqual(s.humanReadableComponents(max_places=None), ("64", "Ki"))
        s = Size(0x10001)
        self.assertEqual(s.humanReadableComponents(max_places=None), ("64.0009765625", "Ki"))

        # test a very large quantity with no associated abbreviation or prefix
        s = Size(1024**9)
        self.assertEqual(s.humanReadableComponents(max_places=2), ("1024", "Yi"))
        s = Size(1024**9 - 1)
        self.assertEqual(s.humanReadableComponents(max_places=2), ("1024", "Yi"))
        s = Size(1024**9 + 1)
        self.assertEqual(s.humanReadableComponents(max_places=2, strip=False), ("1024.00", "Yi"))
        s = Size(1024**10)
        self.assertEqual(s.humanReadableComponents(max_places=2), ("1048576", "Yi"))

    def testHumanReadableFractionalQuantities(self):
        """ Test behavior when the displayed value is a fraction of units. """
        s = Size(0xfffffffffffff)
        self.assertEqual(s.humanReadableComponents(max_places=2), ("4", "Pi"))
        s = Size(0xfffff)
        self.assertEqual(s.humanReadableComponents(max_places=2, strip=False), ("1024.00", "Ki"))
        s = Size(0xffff)
        # value is not exactly 64 KiB, but w/ 2 places, value is 64.00 KiB
        # so the trailing 0s are stripped.
        self.assertEqual(s.humanReadableComponents(max_places=2), ("64", "Ki"))
        # since all significant digits are shown, there are no trailing 0s.
        self.assertEqual(s.humanReadableComponents(max_places=None), ("63.9990234375", "Ki"))

        eps = Decimal(1024)/100/2 # 1/2 of 1% of 1024

        # deviation is less than 1/2 of 1% of 1024
        s = Size(16384 - (eps - 1))
        self.assertEqual(s.humanReadableComponents(max_places=2), ("16", "Ki"))

        # deviation is greater than 1/2 of 1% of 1024
        s = Size(16384 - (eps + 1))
        self.assertEqual(s.humanReadableComponents(max_places=2), ("15.99", "Ki"))
        # deviation is greater than 1/2 of 1% of 1024
        s = Size(16384 + (eps + 1))
        self.assertEqual(s.humanReadableComponents(max_places=2), ("16.01", "Ki"))

        # deviation is less than 1/2 of 1% of 1024
        s = Size(16384 + (eps - 1))
        self.assertEqual(s.humanReadableComponents(max_places=2), ("16", "Ki"))

        s = Size(0x10000000000000)
        self.assertEqual(s.humanReadableComponents(max_places=2), ("4", "Pi"))

    def testMinValue(self):
        """ Test behavior on min_value parameter. """
        s = Size(9, MiB)
        self.assertEqual(s.humanReadableComponents(), ("9", "Mi"))
        self.assertEqual(s.humanReadableComponents(min_value=10), ("9216", "Ki"))

        s = Size("0.5", GiB)
        self.assertEqual(
           s.humanReadableComponents(max_places=2, min_value=1),
           ("512", "Mi")
        )
        self.assertEqual(s.humanReadableComponents(
           max_places=2, min_value=Decimal("0.1")),
           ("0.5", "Gi")
        )
        self.assertEqual(
           s.humanReadableComponents(max_places=2, min_value=Decimal(1)),
           ("512", "Mi")
        )

    def testExceptionValues(self):
        """ Test that exceptions are properly raised on bad params. """
        s = Size(500)
        with self.assertRaises(SizeValueError):
            s.humanReadableComponents(max_places=-1)
        with self.assertRaises(SizeValueError):
            s.humanReadableComponents(min_value=-1)

    def testRoundingToBytes(self):
        """ Test that second part is empty when units is bytes. """
        s = Size(500)
        self.assertEqual(s.humanReadableComponents(max_places=0), ("500", ""))

class SpecialMethodsTestCase(unittest.TestCase):
    """ Test specially named, non-operator methods. """

    def testConvertToPrecision(self):
        """ Test convertTo method. """
        s = Size(1835008)
        self.assertEqual(s.convertTo(None), 1835008)
        self.assertEqual(s.convertTo(B), 1835008)
        self.assertEqual(s.convertTo(KiB), 1792)
        self.assertEqual(s.convertTo(MiB), 1.75)

    def testConvertToWithSize(self):
        """ Test convertTo method when conversion target is a Size. """
        s = Size(1835008)
        self.assertEqual(s.convertTo(Size(1)), s.convertTo(B))
        self.assertEqual(s.convertTo(Size(1024)), s.convertTo(KiB))
        self.assertEqual(Size(512).convertTo(Size(1024)), Decimal("0.5"))
        self.assertEqual(Size(1024).convertTo(Size(512)), Decimal(2))

        with self.assertRaises(SizeValueError):
            s.convertTo(Size(0))

    def testRoundToNearest(self):
        """ Test roundToNearest method. """

        s = Size("10.3", GiB)
        self.assertEqual(s.roundToNearest(GiB, rounding=ROUND_HALF_UP), Size(10, GiB))
        self.assertEqual(s.roundToNearest(GiB, rounding=ROUND_HALF_UP),
                         Size(10, GiB))
        self.assertEqual(s.roundToNearest(GiB, rounding=ROUND_DOWN),
                         Size(10, GiB))
        self.assertEqual(s.roundToNearest(GiB, rounding=ROUND_UP),
                         Size(11, GiB))
        # >>> Size("10.3 GiB").convertTo(MiB)
        # Decimal('10547.19999980926513671875')
        self.assertEqual(s.roundToNearest(MiB, rounding=ROUND_HALF_UP), Size(10547, MiB))
        self.assertEqual(s.roundToNearest(MiB, rounding=ROUND_UP),
                         Size(10548, MiB))
        self.assertIsInstance(s.roundToNearest(MiB, rounding=ROUND_HALF_UP), Size)
        with self.assertRaises(SizeValueError):
            s.roundToNearest(MiB, rounding='abc')

        # arbitrary decimal rounding constants are not allowed
        from decimal import ROUND_HALF_DOWN
        with self.assertRaises(SizeValueError):
            s.roundToNearest(MiB, rounding=ROUND_HALF_DOWN)

        s = Size("10.51", GiB)
        self.assertEqual(s.roundToNearest(GiB, rounding=ROUND_HALF_UP), Size(11, GiB))
        self.assertEqual(s.roundToNearest(GiB, rounding=ROUND_HALF_UP),
                         Size(11, GiB))
        self.assertEqual(s.roundToNearest(GiB, rounding=ROUND_DOWN),
                         Size(10, GiB))
        self.assertEqual(s.roundToNearest(GiB, rounding=ROUND_UP),
                         Size(11, GiB))

        s = Size(513, GiB)
        self.assertEqual(s.roundToNearest(GiB, rounding=ROUND_HALF_UP), s)
        self.assertEqual(s.roundToNearest(TiB, rounding=ROUND_HALF_UP), Size(1, TiB))
        self.assertEqual(s.roundToNearest(TiB, rounding=ROUND_DOWN),
                         Size(0))

        # test Size parameters
        self.assertEqual(s.roundToNearest(Size(128, GiB), rounding=ROUND_HALF_UP), Size(512, GiB))
        self.assertEqual(s.roundToNearest(Size(1, KiB), rounding=ROUND_HALF_UP), Size(513, GiB))
        self.assertEqual(s.roundToNearest(Size(1, TiB), rounding=ROUND_HALF_UP), Size(1, TiB))
        self.assertEqual(s.roundToNearest(Size(1, TiB), rounding=ROUND_DOWN), Size(0))
        self.assertEqual(s.roundToNearest(Size(0), rounding=ROUND_HALF_UP), Size(0))
        self.assertEqual(s.roundToNearest(Size(13, GiB), rounding=ROUND_HALF_UP), Size(507, GiB))

        with self.assertRaises(SizeValueError):
            s.roundToNearest(Size(-1, B), rounding=ROUND_HALF_UP)


class UtilityMethodsTestCase(unittest.TestCase):
    """ Test operator methods and other methods with an '_'. """

    def testBinaryOperatorsSize(self):
        """ Test binary operators with a possible Size result. """
        s = Size(2, GiB)

        # +
        self.assertEqual(s + s, Size(4, GiB))
        with self.assertRaises(SizeNonsensicalBinOpError):
            s + 2 # pylint: disable=pointless-statement
        with self.assertRaises(SizeNonsensicalBinOpError):
            2 + s # pylint: disable=pointless-statement

        # -
        self.assertEqual(s - s, Size(0))
        with self.assertRaises(SizeNonsensicalBinOpError):
            s - 2 # pylint: disable=pointless-statement
        with self.assertRaises(SizeNonsensicalBinOpError):
            2 - s # pylint: disable=pointless-statement

        # *
        self.assertEqual(s * 2, Size(4, GiB))
        self.assertEqual(2 * s, Size(4, GiB))
        with self.assertRaises(SizePowerResultError):
            s * s # pylint: disable=pointless-statement
        with self.assertRaises(SizeNonsensicalBinOpError):
            s * "str" # pylint: disable=pointless-statement

        # / truediv, retains fractional quantities
        self.assertEqual(s / s, Decimal(1))
        self.assertEqual(s / 2, Size(1, GiB))
        with self.assertRaises(SizeNonsensicalBinOpError):
            2 / s # pylint: disable=pointless-statement
        with self.assertRaises(SizeNonsensicalBinOpError):
            s / "str" # pylint: disable=pointless-statement
        with self.assertRaises(SizeNonsensicalBinOpError):
            "str" / s # pylint: disable=pointless-statement

        # // floordiv
        self.assertEqual(s // s, 1)
        self.assertEqual(s // 2, Size(1, GiB))
        with self.assertRaises(SizeNonsensicalBinOpError):
            2 // s # pylint: disable=pointless-statement
        with self.assertRaises(SizeNonsensicalBinOpError):
            s // "str" # pylint: disable=pointless-statement

        # %
        self.assertEqual(s % s, Size(0))
        self.assertEqual(s % 2, Size(0))
        with self.assertRaises(SizeNonsensicalBinOpError):
            1024 % Size(127) # pylint: disable=expression-not-assigned, pointless-statement
        with self.assertRaises(SizeNonsensicalBinOpError):
            s % "str" # pylint: disable=expression-not-assigned, pointless-statement

        # **
        with self.assertRaises(SizeNonsensicalBinOpError):
            s ** Size(2) # pylint: disable=expression-not-assigned, pointless-statement
        with self.assertRaises(SizePowerResultError):
            s ** 2 # pylint: disable=pointless-statement
        with self.assertRaises(SizeNonsensicalBinOpError):
            2 ** Size(0) # pylint: disable=expression-not-assigned, pointless-statement

        # divmod
        self.assertEqual(divmod(Size(32, MiB), 2), (Size(16, MiB), Size(0)))
        self.assertEqual(divmod(Size(24, MiB), Size(16, MiB)), (1, Size(8, MiB)))
        with self.assertRaises(SizeNonsensicalBinOpError):
            divmod(2048, Size(12, B))
        with self.assertRaises(SizeNonsensicalBinOpError):
            divmod(s, "str")

    def testBinaryOperatorsBoolean(self):
        """ Test binary operators with a boolean result. """

        # <
        self.assertTrue(Size(0, MiB) < Size(32))
        with self.assertRaises(SizeNonsensicalBinOpError):
            Size(0) < 1 # pylint: disable=expression-not-assigned
        with self.assertRaises(SizeNonsensicalBinOpError):
            1 < Size(32, TiB) # pylint: disable=expression-not-assigned

        # <=
        self.assertTrue(Size(0, MiB) <= Size(32))
        with self.assertRaises(SizeNonsensicalBinOpError):
            Size(0) <= 1 # pylint: disable=expression-not-assigned
        with self.assertRaises(SizeNonsensicalBinOpError):
            1 <= Size(32, TiB) # pylint: disable=expression-not-assigned

        # >
        self.assertTrue(Size(32, MiB) > Size(32))
        with self.assertRaises(SizeNonsensicalBinOpError):
            Size(32) > 1 # pylint: disable=expression-not-assigned
        with self.assertRaises(SizeNonsensicalBinOpError):
            1 > Size(0, TiB) # pylint: disable=expression-not-assigned

        # >=
        self.assertTrue(Size(32, MiB) >= Size(32))
        with self.assertRaises(SizeNonsensicalBinOpError):
            Size(32) >= 1 # pylint: disable=expression-not-assigned
        with self.assertRaises(SizeNonsensicalBinOpError):
            1 >= Size(0, TiB) # pylint: disable=expression-not-assigned

        # !=
        self.assertTrue(Size(32, MiB) != Size(32, GiB))

        # boolean properties
        self.assertEqual(Size(0) and True, Size(0))
        self.assertEqual(True and Size(0), Size(0))
        self.assertEqual(Size(1) or True, Size(1))
        self.assertEqual(False or Size(5, MiB), Size(5, MiB))

    def testUnaryOperators(self):
        """ Test unary operators. """
        s = Size(2, GiB)

        # unary +/-
        self.assertEqual(-(Size(32)), Size(-32))
        self.assertEqual(+(Size(32)), Size(32))
        self.assertEqual(+(Size(-32)), Size(-32))

        # abs
        self.assertEqual(abs(s), s)
        self.assertEqual(abs(Size(-32, TiB)), Size(32, TiB))

    def testOtherMethods(self):
        """ Test miscellaneous non-operator methods. """

        # conversions
        self.assertIsInstance(int(Size(32, MiB)), int)
        self.assertFalse(bool(Size(0)))
        self.assertTrue(bool(Size(1)))

        self.assertEqual(str(Size(0)), "0.00 B")
        self.assertEqual(str(Size(1024)), "1.00 KiB")

        self.assertEqual(repr(Size(0)), "Size('0')")
        self.assertEqual(repr(Size(1024)), "Size('1024')")
        self.assertEqual(repr(Size("1024.1")), "Size('1024')")

        self.assertEqual(hash(Size(1024)), hash(1024))

        s = Size(1024)
        z = copy.deepcopy(s)
        self.assertIsNot(s._magnitude, z._magnitude) # pylint: disable=protected-access

    def testRMethods(self):
        """ Test certain r* methods. These methods must be invoked
            explicitly, rather than by means of an operator, in order
            to be executed. Otherwise, their companion non-R method
            will be invoked instead.
        """
        s = Size(2, GiB)

        # rtruediv, retains fractional quantities
        self.assertEqual(s.__rtruediv__(s), Decimal(1))
        with self.assertRaises(SizeNonsensicalOpError):
            s.__rtruediv__("str") # pylint: disable=pointless-statement

        # rdivmod
        self.assertEqual(Size(16, MiB).__rdivmod__(Size(24, MiB)), (1, Size(8, MiB)))
        with self.assertRaises(SizeNonsensicalOpError):
            divmod(s.__rdivmod__("str"))

        # // rfloordiv
        self.assertEqual(s.__rfloordiv__(s), 1)
        with self.assertRaises(SizeNonsensicalOpError):
            s.__rfloordiv__("str") # pylint: disable=pointless-statement

        # rmod
        self.assertEqual(s.__rmod__(s), Size(0))
        with self.assertRaises(SizeNonsensicalOpError):
            s.__rmod__("str") # pylint: disable=expression-not-assigned, pointless-statement

        # rsub
        self.assertEqual(s.__rsub__(s), Size(0))
        with self.assertRaises(SizeNonsensicalOpError):
            s.__rsub__(2) # pylint: disable=pointless-statement

class ConfigurationTestCase(unittest.TestCase):
    """ Test setting configuration for display. """

    def tearDown(self):
        """ Reset configuration to default. """
        Size.set_str_config(Defaults.STR_CONFIG)

    def testSettingConfiguration(self):
        """ Test that setting configuration to different values has effect. """
        s = Size(64, GiB)
        s.set_str_config(StrConfig(strip=False))
        prev = str(s)
        s.set_str_config(StrConfig(strip=True))
        subs = str(s)
        self.assertTrue(subs != prev)
