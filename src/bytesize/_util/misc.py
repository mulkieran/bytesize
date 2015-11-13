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

from .._errors import SizeValueError

from .math_util import long_decimal_division


def decimal_magnitude(value):
    """
    Get ``value`` as a possibly repeating decimal.

    :param value: the value
    :type value: any precise numerical quantity
    :returns: a precise decimal representation of the number
    :rtype: str

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
                right = str(int("".join(str(x) for x in right) or "0") + 1)
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

def get_string_info(magnitude, places):
    """
    Get information about the string that represents this magnitude.

    :param Fraction magnitude: the magnitude
    :param int places: the number of places after the decimal pt
    :returns: a pair, indicating whether the value is exact and the value
    :rtypes: tuple of bool * str
    """
    res = convert_magnitude(magnitude, places=places)
    if Fraction(res) == magnitude:
        return (True, res)
    else:
        return (False, res)
