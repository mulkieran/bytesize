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

""" Utilities for bytesize package. """

from decimal import Decimal
from decimal import DefaultContext
from decimal import InvalidOperation
from decimal import localcontext
from fractions import Fraction

import six

from ._constants import B
from ._constants import RoundingMethods
from ._constants import PRECISE_NUMERIC_TYPES
from ._errors import SizeValueError

def convert_magnitude(value, max_places=2, context=DefaultContext):
    """ Convert magnitude to a decimal string.

        :param value: any value
        :type value: a numeric value, not a float
        :param max_places: number of decimal places to use, default is 2
        :type max_place: an integer type or NoneType
        :param :class:`decimal.DefaultContext` context: a decimal context

        :returns: a string representation of value
        :rtype: str

        Since a rational number may be a non-terminating decimal
        quantity, this representation is not guaranteed to be exact, regardless
        of the value of max_places.

        Even in the case of a terminating decimal representation, the
        representation may be inexact if the number of significant digits
        is too large for the precision of the Decimal operations as
        specified by the context.
    """
    if max_places is not None and \
       (max_places < 0 or not isinstance(max_places, six.integer_types)):
        raise SizeValueError(
           max_places,
           "max_places",
           "must be None or a non-negative integer value"
        )

    if isinstance(value, float):
        raise SizeValueError(
           value,
           "value",
           "must not be a float"
        )

    with localcontext(context) as ctx:
        if isinstance(value, Fraction):
            value = Decimal(value.numerator)/Decimal(value.denominator)

        value = Decimal(value)

        if max_places is not None:
            while True:
                try:
                    value = value.quantize(Decimal(10) ** -max_places)
                    break
                except InvalidOperation:
                    ctx.prec += 2

        return str(value)

def format_magnitude(value, max_places=2, strip=False, context=DefaultContext):
    """ Format a numeric value.

        :param value: any value
        :type value: a numeric value, not a float
        :param max_places: number of decimal places to use, default is 2
        :type max_place: an integer type or NoneType
        :param bool strip: True if trailing zeros are to be stripped
        :param :class:`decimal.DefaultContext` context: a decimal context

        :returns: the formatted value
        :rtype: str
    """
    ret = convert_magnitude(value, max_places, context=context)

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

def get_bytes(value=0, units=None):
    """ Get number of bytes corresponding to value and units.

        :param value: a size value, default is 0
        :type value: any finite numeric type (possibly as str)
        :param units: the units of the size, default is None
        :type units: any elements in UNITS() or NoneType
        :raises SizeValueError: on bad parameters
        :returns: number of bytes
        :rtype: Fraction
    """
    if isinstance(value, six.string_types) or \
       isinstance(value, PRECISE_NUMERIC_TYPES):
        try:
            return Fraction(value) * int(units or B)
        except (ValueError, TypeError):
            raise SizeValueError(value, "value")
    else:
        raise SizeValueError(value, "value")
