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

""" Miscellaneous utilities. """

from fractions import Fraction

import six

from .._constants import RoundingMethods
from .._constants import PRECISE_NUMERIC_TYPES

from .._errors import SizeValueError


def get_repeating_fraction(numerator, denominator):
    """
    Get the repeating decimal number corresponding to the ratio of
    ``numerator`` and ``denominator``.

    :param int numerator: the numerator
    :param int denominator: the denominator

    :returns: a list of decimal digits and a number indicating length of repeat
    :rtype: tuple of (list of int) * int

    Prereq: numerator < denominator, denominator > 0, numerator >= 0
    """

    if numerator < 0:
        raise SizeValueError(numerator, "numerator", "must be at least 0")

    if denominator <= 0:
        raise SizeValueError(
           denominator,
           "denominator",
           "must be greater than 0"
        )

    if denominator < numerator:
        raise SizeValueError(
           denominator,
           "denominator",
           "must be greater than numerator"
        )

    rem = numerator

    quotients = []
    remainders = []
    while rem != 0 and rem not in remainders:
        remainders.append(rem)
        (quot, rem) = divmod(rem * 10, denominator)
        quotients.append(quot)

    # if rem is not 0 this is a repeating decimal
    repeat_len = 0 if rem == 0 else len(remainders) - remainders.index(rem)
    return (quotients, repeat_len)

def long_decimal_division(divisor, dividend):
    """ Precise division of two precise quantities.

        :param divisor: the divisor
        :type divisor: any precise numeric quantity
        :param dividend: the dividend
        :type dividend: any precise numeric quantity
        :returns: the result of long division
        :rtype: a tuple of int * list * list
        :raises :class:`SizeValueError`: on bad input

        The result is the number to the left of the decimal
        point, a list of the non-repeating digits to the right of the
        decimal point, and a list of the repeating digits.
    """
    if not isinstance(divisor, PRECISE_NUMERIC_TYPES):
        raise SizeValueError(
           divisor,
           "divisor",
           "divisor must be a precise numeric type"
       )

    if not isinstance(dividend, PRECISE_NUMERIC_TYPES):
        raise SizeValueError(
           dividend,
           "dividend",
           "dividend must be a precise numeric type"
       )

    if divisor == 0:
        raise SizeValueError(divisor, "divisor")

    sign = 1

    (dividend, divisor) = (Fraction(dividend), Fraction(divisor))

    (left, rem) = divmod(dividend, divisor)

    if left < 0:
        sign = -1
        if rem != 0:
            left = left + 1
            rem = rem - divisor

    fractional_part = abs(rem / divisor)
    (right, num_repeating) = get_repeating_fraction(
       fractional_part.numerator,
       fractional_part.denominator
    )

    return (
       sign,
       abs(left),
       right[:len(right) - num_repeating],
       right[-num_repeating:] if num_repeating != 0 else []
    )

def decimal_magnitude(value):
    """
    Get ``value`` as a possibly repeating decimal.

    :param value: the value
    :type value: any precise numerical quantity
    :returns: a precise decimal representation of the number
    :rtype: tuple of int * list of int * int

    The parts represent the non-fractional part, the fractional part
    including the first repeating part, the length of the repeating part.
    """
    value = Fraction(value)
    (sign, left, non_repeating, repeating) = long_decimal_division(
       value.denominator,
       value.numerator
    )

    sign_str = "-" if sign == -1 else ""

    if non_repeating == []:
        return "%s%s" % (sign_str, left)

    non_repeating_str = "".join(str(x) for x in non_repeating)
    if repeating == []:
        return "%s%s.%s" % (sign_str, left, non_repeating_str)

    repeating_str = "".join(str(x) for x in repeating)
    return "%s%s.%s(%s)" % (sign_str, left, non_repeating_str, repeating_str)

def convert_magnitude(value, places=2):
    """ Convert magnitude to a decimal string.

        :param value: any value
        :type value: a numeric value, not a float
        :param places: number of decimal places to use, default is 2
        :type places: an integer type or NoneType

        :returns: a string representation of value
        :rtype: str

        Since a rational number may be a non-terminating decimal
        quantity, this representation is not guaranteed to be exact, regardless
        of the value of places.

        Even in the case of a terminating decimal representation, the
        representation may be inexact if the number of significant digits
        is too large for the precision of the Decimal operations as
        specified by the context.
    """
    if places is not None and \
       (places < 0 or not isinstance(places, six.integer_types)):
        raise SizeValueError(
           places,
           "places",
           "must be None or a non-negative integer value"
        )

    if isinstance(value, float):
        raise SizeValueError(
           value,
           "value",
           "must not be a float"
        )

    value = Fraction(value)
    (sign, left, non_repeating, repeating) = long_decimal_division(
       value.denominator,
       value.numerator
    )

    places = len(non_repeating) + len(repeating) if places is None else places

    right_side = non_repeating[:]
    if len(repeating) > 0:
        while len(right_side) <= places:
            right_side += repeating

    if len(right_side) > places:
        right = right_side[:places]
        next_digits = right_side[places:]
        decider = next((d for d in next_digits if d != 5), None)
        if decider is not None:
            if decider > 5:
                right = str(int("".join(str(x) for x in right)) + 1)
                right = [l for l in right]
        if len(right) > places:
            left = left + int(right[0])
            right = right[1:]
        elif len(right) < places:
            right = [0 for _ in range(places - len(right))] + right
    else:
        right = right_side[:] + [0 for _ in range(places - len(right_side))]

    sign_str = '-' if sign == -1 else ""
    if len(right) > 0:
        return "%s%s.%s" % (sign_str, left, "".join(str(x) for x in right))
    else:
        return "%s%s" % (sign_str, left)


def format_magnitude(value, max_places=2, strip=False):
    """ Format a numeric value.

        :param value: any value
        :type value: a numeric value, not a float
        :param max_places: number of decimal places to use, default is 2
        :type max_place: an integer type or NoneType
        :param bool strip: True if trailing zeros are to be stripped

        :returns: the formatted value
        :rtype: str
    """
    ret = convert_magnitude(value, max_places)

    if '.' in ret and strip:
        ret = ret.rstrip("0").rstrip(".")

    return ret

def round_fraction(value, rounding):
    """ Round a fraction to an integer according to rounding method.

        :param Fraction value: value to round
        :param rounding: rounding method
        :type rounding: a member of RoundingMethods
        :return: a rounded integer
        :rtype: int
    """
    # pylint: disable=too-many-return-statements
    (base, rest) = divmod(value.numerator, value.denominator)
    if rest == 0:
        return base

    if rounding == RoundingMethods.ROUND_UP:
        return base + 1

    if rounding == RoundingMethods.ROUND_DOWN:
        return base

    half_methods = (
       RoundingMethods.ROUND_HALF_UP,
       RoundingMethods.ROUND_HALF_DOWN
    )
    if rounding in half_methods:
        fraction = Fraction(rest, value.denominator)
        half = Fraction(1, 2)

        if fraction < half:
            return base
        elif fraction > half:
            return base + 1
        else:
            if rounding == RoundingMethods.ROUND_HALF_UP:
                return base + 1
            else:
                return base

    raise SizeValueError(rounding, "rounding")
