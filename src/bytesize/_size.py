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

""" Size class, for creating instances of Size objects.

    Contains a few documented methods and a number of __*__ methods
    implementing arithmetic operations. Precise numeric types
    such as int and Decimal may also occur in some arithmetic expressions,
    but all occurrances of floating point numbers in arithmetic expressions
    will cause an exception to be raised.
"""

from fractions import Fraction

import six

from ._config import SizeConfig

from ._errors import SizeFractionalResultError
from ._errors import SizeNonsensicalBinOpError
from ._errors import SizeNonsensicalBinOpValueError
from ._errors import SizePowerResultError
from ._errors import SizeValueError

from ._constants import B
from ._constants import BinaryUnits
from ._constants import DecimalUnits
from ._constants import PRECISE_NUMERIC_TYPES

from ._util.math_util import round_fraction

from ._util.misc import get_decimal_info
from ._util.misc import get_string_info

_BYTES_SYMBOL = "B"

class Size(object):
    """ Class for instantiating Size objects. """

    _FMT_STR = "".join([
       "%(approx)s",
       "%(sign)s",
       "%(left)s",
       "%(radix)s",
       "%(right)s",
       " ",
       "%(units)s",
       "%(bytes)s"
    ])


    def __init__(self, value=0, units=None):
        """ Initialize a new Size object.

            :param value: a size value, default is 0
            :type value: Size, or any finite numeric type (possibly as str)
            :param units: the units of the size, default is None
            :type units: any of the publicly defined units constants or a Size
            :raises SizeValueError: on bad parameters

            Must pass None as units argument if value has type Size.

            The units number must be a precise numeric type.
        """
        if isinstance(value, six.string_types) or \
           isinstance(value, PRECISE_NUMERIC_TYPES):
            try:
                units = B if units is None else units
                factor = getattr(units, 'magnitude', None) or int(units)
                magnitude = Fraction(value) * factor
            except (ValueError, TypeError):
                raise SizeValueError(value, "value")

        elif isinstance(value, Size):
            if units is not None:
                raise SizeValueError(
                   units,
                   "units",
                   "meaningless when Size value is passed"
                )
            magnitude = value.magnitude # pylint: disable=no-member
        else:
            raise SizeValueError(value, "value")

        if SizeConfig.STRICT is True and magnitude.denominator != 1:
            raise SizeFractionalResultError()
        self._magnitude = magnitude

    @property
    def magnitude(self):
        """
        :returns: the number of bytes
        :rtype: Fraction
        """
        return self._magnitude

    def getDecimalInfo(self, config):
        """
        Get information for the decimal representation of ``self``.

        :param StrConfig config: the display configuration
        :returns: a tuple representing the value
        :rtype: tuple of int * int * list of int * list of int

        Components:
        1. sign, -1 if negative else 1
        2. portion on the left of the decimal point
        3. non-repeating portion to the right of the decimal point
        4. repeating portion to the right of the decimal point
        5. units specifier
        """
        (magnitude, units) = self.components(config)
        radix_num = get_decimal_info(magnitude)
        return (
           radix_num.sign,
           radix_num.left,
           radix_num.non_repeating,
           radix_num.repeating,
           units
        )

    def getStringInfo(self, config):
        """
        Return a representation of the size.

        :param :class:`StrConfig` config: representation configuration
        :returns: a tuple representing the string to display
        :rtype: tuple of bool * int * str * str * unit

        Components are:
        1. If true, the value is approximate
        2. -1 for a negative number, 1 for a positive
        3. a string with the decimal digits to the left of the decimal point
        4. a string with the decimal digits to the right of the decimal point
        5. a unit specifier

        """
        (magnitude, units) = self.components(config)
        (exact, sign, left, right) = get_string_info(
           magnitude,
           places=config.max_places
        )

        return (not exact, sign, left, right, units)

    def getString(self, config, display):
        """ Return a string representation of the size.

            :param :class:`StrConfig` config: representation configuration
            :param DisplayConfig display: configuration for display
            :returns: a string representation
            :rtype: str
        """
        (approx, sign, left, right, units) = self.getStringInfo(config)
        approx_str = display.approx_symbol \
           if approx and display.show_approx_str else ""

        if display.strip:
            right = right.rstrip('0')

        result = {
           'approx' : approx_str,
           'sign': "-" if sign == -1 else "",
           'left': left,
           'radix': '.' if right else "",
           'right' : right,
           'units' : units.abbr,
           'bytes' : _BYTES_SYMBOL
        }

        return self._FMT_STR % result

    def __str__(self):
        return self.getString(SizeConfig.STR_CONFIG, SizeConfig.DISPLAY_CONFIG)

    def __repr__(self):
        radix_num = get_decimal_info(self._magnitude)

        sign = "-" if radix_num.sign == -1 else ""

        if radix_num.non_repeating == [] and radix_num.repeating == []:
            return "Size(%s%s)" % (sign, radix_num.left)

        non_repeating = "".join(str(x) for x in radix_num.non_repeating)
        if radix_num.repeating == []:
            return "Size(%s%s.%s)" % (sign, radix_num.left, non_repeating)

        repeating = "".join(str(x) for x in radix_num.repeating)
        return "Size(%s%s.%s(%s))" % \
           (sign, radix_num.left, non_repeating, repeating)

    def __deepcopy__(self, memo):
        # pylint: disable=unused-argument
        return Size(self._magnitude)

    def __nonzero__(self):
        return self._magnitude != 0

    def __int__(self):
        return int(self._magnitude)
    __trunc__ = __int__

    def __hash__(self):
        return hash(self._magnitude)

    def __bool__(self):
        return self.__nonzero__()

    # UNARY OPERATIONS

    def __abs__(self):
        return Size(abs(self._magnitude))

    def __neg__(self):
        return Size(-(self._magnitude))

    def __pos__(self):
        return Size(self._magnitude)

    # BINARY OPERATIONS
    def __add__(self, other):
        if not isinstance(other, Size):
            raise SizeNonsensicalBinOpError("+", other)
        return Size(self._magnitude + other.magnitude)
    __radd__ = __add__

    def __divmod__(self, other):
        # other * div + rem = self
        # Therefore, T(rem) = T(self) = Size
        #            T(div) = Size, if T(other) is numeric
        #                   = Fraction, if T(other) is Size
        if isinstance(other, Size):
            try:
                (div, rem) = divmod(self._magnitude, other.magnitude)
                return (div, Size(rem))
            except ZeroDivisionError:
                raise SizeNonsensicalBinOpValueError("divmod", other)
        if isinstance(other, PRECISE_NUMERIC_TYPES):
            try:
                (div, rem) = divmod(self._magnitude, Fraction(other))
                return (Size(div), Size(rem))
            except (TypeError, ValueError, ZeroDivisionError):
                raise SizeNonsensicalBinOpValueError("divmod", other)
        raise SizeNonsensicalBinOpError("divmod", other)

    def __rdivmod__(self, other):
        # self * div + rem = other
        # Therefore, T(rem) = T(other)
        #            T(div) = Fraction
        # and T(other) is Size
        if not isinstance(other, Size):
            raise SizeNonsensicalBinOpError("rdivmod", other)
        try:
            (div, rem) = divmod(other.magnitude, self._magnitude)
            return (div, Size(rem))
        except ZeroDivisionError:
            raise SizeNonsensicalBinOpValueError("rdivmod", other)

    def __eq__(self, other):
        return isinstance(other, Size) and \
           self._magnitude == other.magnitude

    def __floordiv__(self, other):
        # other * floor + rem = self
        # Therefore, T(floor) = Size, if T(other) is numeric
        #                     = int, if T(other) is Size
        if isinstance(other, Size):
            try:
                return self._magnitude.__floordiv__(other.magnitude)
            except ZeroDivisionError:
                raise SizeNonsensicalBinOpValueError("floordiv", other)
        if isinstance(other, PRECISE_NUMERIC_TYPES):
            try:
                return Size(self._magnitude.__floordiv__(Fraction(other)))
            except (TypeError, ValueError, ZeroDivisionError):
                raise SizeNonsensicalBinOpValueError("floordiv", other)
        raise SizeNonsensicalBinOpError("floordiv", other)

    def __rfloordiv__(self, other):
        # self * floor + rem = other
        # Therefore, T(floor) = int and T(other) is Size
        if not isinstance(other, Size):
            raise SizeNonsensicalBinOpError("rfloordiv", other)
        try:
            return other.magnitude.__floordiv__(self._magnitude)
        except ZeroDivisionError:
            raise SizeNonsensicalBinOpValueError("rfloordiv", other)

    def __ge__(self, other):
        if not isinstance(other, Size):
            raise SizeNonsensicalBinOpError(">=", other)
        return self._magnitude >= other.magnitude

    def __gt__(self, other):
        if not isinstance(other, Size):
            raise SizeNonsensicalBinOpError(">", other)
        return self._magnitude > other.magnitude

    def __le__(self, other):
        if not isinstance(other, Size):
            raise SizeNonsensicalBinOpError("<=", other)
        return self._magnitude <= other.magnitude

    def __lt__(self, other):
        if not isinstance(other, Size):
            raise SizeNonsensicalBinOpError("<", other)
        return self._magnitude < other.magnitude

    def __mod__(self, other):
        # other * div + mod = self
        # Therefore, T(mod) = Size
        if isinstance(other, Size):
            try:
                return Size(self._magnitude % other.magnitude)
            except ZeroDivisionError:
                raise SizeNonsensicalBinOpValueError('%', other)
        if isinstance(other, PRECISE_NUMERIC_TYPES):
            try:
                return Size(self._magnitude % Fraction(other))
            except (TypeError, ValueError, ZeroDivisionError):
                raise SizeNonsensicalBinOpValueError('%', other)
        raise SizeNonsensicalBinOpError("%", other)

    def __rmod__(self, other):
        # self * div + mod = other
        # Therefore, T(mod) = T(other) and T(other) = Size.
        if not isinstance(other, Size):
            raise SizeNonsensicalBinOpError("rmod", other)
        try:
            return Size(other.magnitude % Fraction(self._magnitude))
        except (TypeError, ValueError, ZeroDivisionError):
            raise SizeNonsensicalBinOpValueError("rmod", other)

    def __mul__(self, other):
        # self * other = mul
        # Therefore, T(mul) = Size and T(other) is a numeric type.
        if isinstance(other, PRECISE_NUMERIC_TYPES):
            try:
                return Size(self._magnitude * Fraction(other))
            except (TypeError, ValueError):
                raise SizeNonsensicalBinOpError("*", other)
        if isinstance(other, Size):
            raise SizePowerResultError()
        raise SizeNonsensicalBinOpError("*", other)
    __rmul__ = __mul__

    def __pow__(self, other):
        # pylint: disable=no-self-use
        # Cannot represent multiples of Sizes.
        if not isinstance(other, PRECISE_NUMERIC_TYPES):
            raise SizeNonsensicalBinOpError("**", other)
        raise SizePowerResultError()

    def __rpow__(self, other):
        # A Size exponent is meaningless.
        raise SizeNonsensicalBinOpError("rpow", other)

    def __ne__(self, other):
        return not isinstance(other, Size) or \
           self._magnitude != other.magnitude

    def __sub__(self, other):
        # self - other = sub
        # Therefore, T(sub) = T(self) = Size and T(other) = Size.
        if not isinstance(other, Size):
            raise SizeNonsensicalBinOpError("-", other)
        return Size(self._magnitude - other.magnitude)

    def __rsub__(self, other):
        # other - self = sub
        # Therefore, T(sub) = T(self) = Size and T(other) = Size.
        if not isinstance(other, Size):
            raise SizeNonsensicalBinOpError("rsub", other)
        return Size(other.magnitude - self._magnitude)

    def __truediv__(self, other):
        # other * truediv = self
        # Therefore, T(truediv) = Fraction, if T(other) is Size
        if isinstance(other, Size):
            try:
                return self._magnitude.__truediv__(other.magnitude)
            except ZeroDivisionError:
                raise SizeNonsensicalBinOpValueError("truediv", other)
        elif isinstance(other, PRECISE_NUMERIC_TYPES):
            try:
                return Size(self._magnitude.__truediv__(Fraction(other)))
            except (TypeError, ValueError, ZeroDivisionError):
                raise SizeNonsensicalBinOpValueError("truediv", other)
        raise SizeNonsensicalBinOpError("truediv", other)

    __div__ = __truediv__

    def __rtruediv__(self, other):
        # self * truediv = other
        # Therefore, T(truediv) = Fraction and T(other) = Size.
        if not isinstance(other, Size):
            raise SizeNonsensicalBinOpError("rtruediv", other)
        try:
            return other.magnitude.__truediv__(self._magnitude)
        except ZeroDivisionError:
            raise SizeNonsensicalBinOpValueError("rtruediv", self)

    __rdiv__ = __rtruediv__

    def convertTo(self, spec=None):
        """ Return the size in the units indicated by the specifier.

            :param spec: a units specifier
            :type spec: a units specifier or :class:`Size`
            :returns: a numeric value in the units indicated by the specifier
            :rtype: :class:`fractions.Fraction`
            :raises SizeValueError: if unit specifier is non-positive
        """
        spec = B if spec is None else spec
        factor = getattr(spec, 'magnitude', None) or int(spec)

        if factor <= 0:
            raise SizeValueError(
               factor,
               "factor",
               "can not convert to non-positive unit %s"
            )

        return self._magnitude / factor

    def componentsList(self, binary_units=True):
        """ Yield a representation of this size for every unit,
            decomposed into a Fraction value and a unit specifier
            tuple.

            :param bool binary_units: binary units if True, else SI
        """
        units = BinaryUnits if binary_units else DecimalUnits

        for unit in [B] + units.UNITS():
            yield (self.convertTo(unit), unit)

    def components(self, config=SizeConfig.STR_CONFIG):
        """ Return a representation of this size, decomposed into a
            Fraction value and a unit specifier tuple.

            :param StrConfig config: configuration

            :returns: a pair of a decimal value and a unit
            :rtype: tuple of Fraction and unit
            :raises SizeValueError: if min_value is not usable

            The meaning of the parameters is the same as for
            :class:`._config.StrConfig`.
        """
        units = BinaryUnits if config.binary_units else DecimalUnits

        if config.unit is not None:
            return (self.convertTo(config.unit), config.unit)

        # Find the smallest prefix which will allow a number less than
        # FACTOR * min_value to the left of the decimal point.
        # If the number is so large that no prefix will satisfy this
        # requirement use the largest prefix.
        limit = units.FACTOR * Fraction(config.min_value)
        tried = []
        for (value, unit) in self.componentsList(
           binary_units=config.binary_units
        ):
            tried.append((value, unit))
            if abs(value) < limit:
                break

        if config.exact_value:
            for (value, unit) in reversed(tried):
                (exact, _, _, _) = get_string_info(value, config.max_places)
                if exact is True:
                    break

        # pylint: disable=undefined-loop-variable
        return (value, unit)

    def roundTo(self, unit, rounding):
        # pylint: disable=line-too-long
        """ Rounds to unit specified as a named constant or a Size.

            :param unit: a unit specifier
            :type unit: any non-negative :class:`Size` or element in :func:`._constants.UNITS`
            :keyword rounding: rounding mode to use
            :type rounding: a field of :class:`._constants.RoundingMethods`
            :returns: appropriately rounded Size
            :rtype: :class:`Size`
            :raises SizeValueError: on unusable arguments

            If unit is Size(0), returns Size(0).
        """
        factor = getattr(unit, 'magnitude', None) or int(unit)

        if factor < 0:
            raise SizeValueError(factor, "factor")

        if factor == 0:
            return Size(0)

        magnitude = self._magnitude / factor
        rounded = round_fraction(magnitude, rounding)
        return Size(rounded * factor)
