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

""" Utilities for base conversions. """

from .._errors import SizeValueError

def to_int(number, base):
    """ Convert number to an int.

        :param number: the number to be converted
        :type number: list of int (>= 0)
        :param int base: the base of the number

        :returns: the number as an int
        :rtype: int
    """
    value = 0
    multiplier = 1
    for i in range(0, len(number)):
        value += multiplier * number[i]
        multiplier *= base
    return value

def from_int(number, base):
    """ Convert a number to a list of ints in a designated base.

        :param int number: the number to be converted
        :param int base: the designated base

        :returns: the number in the specified base
        :rtype: list of int
    """
    result = []
    quotient = number
    while quotient != 0:
        (quotient, remainder) = divmod(quotient, base)
        result.append(remainder)

    result.reverse()
    return result

def convert_to(number, from_base, to_base):
    """ Convert a number from from_base to to_base.

        :param number: the number to be converted
        :type number: list of int (>= 0)
        :param int from_base: the base of the number
        :param int to_base: the base to convert to
        :returns: a converted number
        :rtype: list of int
    """
    value = to_int(number, from_base)
    return from_int(value, to_base)

def long_decimal_division(divisor, dividend):
    """ Precise division of two integer quantities.

        :param divisor: the divisor
        :type divisor: any precise numeric quantity
        :param dividend: the dividend
        :type dividend: any precise numeric quantity
        :returns: the result of long division
        :rtype: a tuple of int * list * integer
        :raises :class:`SizeValueError`: on bad input

        The result is the number to the left of the decimal
        point, a list of the digits to the right of the decimal point,
        and the length of the repeating part. A zero indicates that the
        decimal is non-repeating, or equivalently, that its one
        repeating digit is 0.
    """
    if isinstance(divisor, float):
        raise SizeValueError("divisor must not be a float")

    if isinstance(divisor, float):
        raise SizeValueError("dividend must not be a float")

    # pylint: disable=unidiomatic-typecheck
    if type(divisor) != type(dividend):
        raise SizeValueError("divisor and dividend must have the same type")

    (left, rem) = divmod(dividend, divisor)

    dividends = []
    right = []
    while not dividend in dividends:
        quotient = dividend / rem
        right.append(quotient)
        dividend = dividend - quotient * rem
        dividend = dividend * 10

    start = dividends.index(dividend)
    return (left, right, len(dividends) - start)
