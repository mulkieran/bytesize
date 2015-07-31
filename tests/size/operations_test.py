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

""" Tests for operations on Size objects. """

import copy
import unittest

from fractions import Fraction

from bytesize import Size
from bytesize import B
from bytesize import MiB
from bytesize import GiB
from bytesize import TiB

from bytesize._errors import SizeNonsensicalBinOpError
from bytesize._errors import SizeNonsensicalOpError
from bytesize._errors import SizePowerResultError

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
        self.assertEqual(s.__rtruediv__(s), Fraction(1))
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

class DivisionTestCase(unittest.TestCase):
    """ Test division operations. """
    # pylint: disable=too-few-public-methods

    def testTrueDiv(self):
        """ __truediv__ retains fractional quantities """
        s = Size(2, TiB)

        # unity
        self.assertEqual(s / s, Fraction(1))

        # fractional quantities
        div = Size(37)
        res = s / div
        self.assertEqual(res * div, s)

        # exceptions
        with self.assertRaises(SizeNonsensicalBinOpError):
            s / 2 # pylint: disable=pointless-statement
        with self.assertRaises(SizeNonsensicalBinOpError):
            2 / s # pylint: disable=pointless-statement
        with self.assertRaises(SizeNonsensicalBinOpError):
            s / "str" # pylint: disable=pointless-statement
        with self.assertRaises(SizeNonsensicalBinOpError):
            "str" / s # pylint: disable=pointless-statement
