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

""" Test for utility functions. """
from hypothesis import given
from hypothesis import strategies
import unittest

from decimal import Decimal
from decimal import DefaultContext
from fractions import Fraction

from bytesize._constants import RoundingMethods
from bytesize._constants import UNITS
from bytesize._errors import SizeValueError
from bytesize._util.misc import convert_magnitude
from bytesize._util.misc import format_magnitude
from bytesize._util.misc import get_bytes
from bytesize._util.misc import round_fraction

from tests.utils import NUMBERS_STRATEGY

class FormatTestCase(unittest.TestCase):
    """ Test formatting. """

    def testException(self):
        """ Raises exception on bad input. """
        with self.assertRaises(SizeValueError):
            format_magnitude(Decimal(200), max_places=-1)
        with self.assertRaises(SizeValueError):
            format_magnitude(0.1)

    _max_exponent = DefaultContext.prec
    @given(
       strategies.integers(
           min_value=-(10**_max_exponent - 1),
           max_value=10**_max_exponent - 1
       ),
       strategies.integers(min_value=0),
       strategies.integers(min_value=0)
    )
    def testExactness(self, n, m, e):
        """ When max_places is not specified, the denominator of
            the value is a power of 10, and the number of significant digits
            in the numerator is no more than the default precision of the
            decimal operations, the string result is exact.
        """
        x = Fraction(n * 10**m, 10**e)
        if x.denominator == 1:
            x = int(x)
        converted = convert_magnitude(
           x,
           max_places=None,
           context=DefaultContext
        )
        self.assertEqual(Fraction(converted), x)

    def testInexactness(self):
        """ If the number of digits in the numerator exceeds the
            available precision, and the lowest order digit is non-zero,
            the result is not exact.
        """
        x = Fraction(10**DefaultContext.prec + 1)
        converted = convert_magnitude(
           x,
           max_places=None,
           context=DefaultContext
        )
        self.assertNotEqual(Fraction(converted), x)

class RoundingTestCase(unittest.TestCase):
    """ Test rounding of fraction. """
    # pylint: disable=too-few-public-methods

    def testExceptions(self):
        """ Raises exception on bad input. """
        with self.assertRaises(SizeValueError):
            round_fraction(Fraction(13, 32), "a string")
        with self.assertRaises(SizeValueError):
            round_fraction(Fraction(16, 32), "a string")

    @given(
       strategies.integers(min_value=1, max_value=9)
    )
    def testRounding(self, i):
        """ Rounding various values according to various methods. """
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

class GetBytesTestCase(unittest.TestCase):
    """ Test get_bytes method. """

    def testExceptions(self):
        """ Test exceptions. """
        with self.assertRaises(SizeValueError):
            get_bytes(Decimal('Nan'), None)
        with self.assertRaises(SizeValueError):
            get_bytes(1.2, None)

    @given(NUMBERS_STRATEGY, strategies.sampled_from(UNITS()))
    def testGetBytes(self, n, u):
        """ Test correctness. """
        self.assertEqual(get_bytes(n, u), Fraction(n) * int(u))
