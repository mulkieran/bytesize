# size.py
# Python module to represent sizes in bytes.
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

""" Size class, for creating instances of Size objects.

    Contains a few documented methods and a number of __*__ methods
    implementing arithmetic operations. Precise numeric types
    such as int and Decimal may also occur in some arithmetic expressions,
    but all occurrances of floating point numbers in arithmetic expressions
    will cause an exception to be raised.
"""

import decimal
from decimal import Decimal
from decimal import InvalidOperation

import six

from .config import StrConfig

from .errors import SizeConstructionError
from .errors import SizeDisplayError
from .errors import SizeNonsensicalBinOpError
from .errors import SizeNonsensicalOpError
from .errors import SizePowerResultError
from .errors import SizeRoundingError

from .constants import B
from .constants import BinaryUnits
from .constants import RoundingMethods

_BYTES_SYMBOL = "B"

class Size(object):
    """ Class for instantiating Size objects. """

    _NUMERIC_TYPES = (six.integer_types, Decimal)
    _STR_CONFIG = StrConfig()
    _rounding_map = {
        RoundingMethods.ROUND_DOWN: decimal.ROUND_DOWN,
        RoundingMethods.ROUND_HALF_DOWN: decimal.ROUND_HALF_DOWN,
        RoundingMethods.ROUND_HALF_UP: decimal.ROUND_HALF_UP,
        RoundingMethods.ROUND_UP: decimal.ROUND_UP
    }

    @classmethod
    def set_str_config(cls, config):
        """ Set the configuration for __str__ method for all Size objects.

            :param :class:`.config.StrConfig` config: a configuration object
        """
        cls._STR_CONFIG = StrConfig(
            max_places=config.max_places,
            strip=config.strip,
            min_value=config.min_value
        )

    def __init__(self, value=0, units=None):
        """ Initialize a new Size object.

            :param value: a size value, default is 0
            :type value: Size, or any numeric type (possibly as str)
            :param units: the units of the size, default is None
            :type units: any of the publicly defined units constants

            Must pass None as units argument if value has type Size.
        """
        if isinstance(value, (six.integer_types, six.string_types, Decimal)):
            factor = (units or B).factor

            if isinstance(value, six.integer_types):
                magnitude = value * factor
            else:
                try:
                    magnitude = Decimal(value)
                except InvalidOperation:
                    raise SizeConstructionError(
                       "invalid value %s for size magnitude" % value
                    )
                magnitude = (magnitude * factor).to_integral_value(
                   rounding=decimal.ROUND_DOWN
                )

        elif isinstance(value, Size):
            if units is not None:
                raise SizeConstructionError(
                   "units parameter is meaningless when Size value is passed"
                )
            magnitude = value
        else:
            raise SizeConstructionError("invalid value for size")

        self._magnitude = int(magnitude)

    def __str__(self):
        res = self.humanReadableComponents(
           max_places=self._STR_CONFIG.max_places,
           strip=self._STR_CONFIG.strip,
           min_value=self._STR_CONFIG.min_value
        )
        return " ".join(res) + _BYTES_SYMBOL

    def __repr__(self):
        return "Size('%s')" % self._magnitude

    def __deepcopy__(self, memo):
        # pylint: disable=unused-argument
        return Size(self.convertTo())

    def __nonzero__(self):
        return self._magnitude != 0

    def __int__(self):
        return self._magnitude
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
        return Size(self._magnitude + int(other))
    __radd__ = __add__

    def __divmod__(self, other):
        # other * div + rem = self
        # Therefore, T(rem) = T(self) = Size
        #            T(div) = Size, if T(other) is numeric
        #                   = int, if T(other) is Size
        if isinstance(other, Size):
            (div, rem) = divmod(self._magnitude, int(other))
            return (div, Size(rem))
        if isinstance(other, self._NUMERIC_TYPES):
            (div, rem) = divmod(self._magnitude, other)
            return (Size(div), Size(rem))
        raise SizeNonsensicalBinOpError("divmod", other)

    def __rdivmod__(self, other):
        # self * div + rem = other
        # Therefore, T(rem) = T(other)
        #            T(div) = int
        # and T(other) is Size
        if not isinstance(other, Size):
            raise SizeNonsensicalBinOpError("rdivmod", other)
        (div, rem) = divmod(int(other), self._magnitude)
        return (div, Size(rem))

    def __eq__(self, other):
        return isinstance(other, Size) and self._magnitude == int(other)

    def __floordiv__(self, other):
        # other * floor + rem = self
        # Therefore, T(floor) = Size, if T(other) is numeric
        #                     = int, if T(other) is Size
        if isinstance(other, Size):
            return self._magnitude.__floordiv__(int(other))
        if isinstance(other, self._NUMERIC_TYPES):
            return Size(Decimal(self._magnitude).__floordiv__(other))
        raise SizeNonsensicalBinOpError("floordiv", other)

    def __rfloordiv__(self, other):
        # self * floor + rem = other
        # Therefore, T(floor) = int and T(other) is Size
        if not isinstance(other, Size):
            raise SizeNonsensicalBinOpError("rfloordiv", other)
        return int(other).__floordiv__(self._magnitude)

    def __ge__(self, other):
        if not isinstance(other, Size):
            raise SizeNonsensicalBinOpError(">=", other)
        return self._magnitude >= int(other)

    def __gt__(self, other):
        if not isinstance(other, Size):
            raise SizeNonsensicalBinOpError(">", other)
        return self._magnitude > int(other)

    def __le__(self, other):
        if not isinstance(other, Size):
            raise SizeNonsensicalBinOpError("<=", other)
        return self._magnitude <= int(other)

    def __lt__(self, other):
        if not isinstance(other, Size):
            raise SizeNonsensicalBinOpError("<", other)
        return self._magnitude < int(other)

    def __mod__(self, other):
        # other * div + mod = self
        # Therefore, T(mod) = Size
        if isinstance(other, Size):
            return Size(self._magnitude % int(other))
        if isinstance(other, self._NUMERIC_TYPES):
            return Size(self._magnitude % other)
        raise SizeNonsensicalBinOpError("%", other)

    def __rmod__(self, other):
        # self * div + mod = other
        # Therefore, T(mod) = T(other) and T(other) = Size.
        if not isinstance(other, Size):
            raise SizeNonsensicalBinOpError("rmod", other)
        return Size(int(other) % self._magnitude)

    def __mul__(self, other):
        # self * other = mul
        # Therefore, T(mul) = Size and T(other) is a numeric type.
        if isinstance(other, self._NUMERIC_TYPES):
            return Size(self._magnitude * other)
        if isinstance(other, Size):
            raise SizePowerResultError()
        raise SizeNonsensicalBinOpError("*", other)
    __rmul__ = __mul__

    def __pow__(self, other):
        # Cannot represent multiples of Sizes.
        if not isinstance(other, self._NUMERIC_TYPES):
            raise SizeNonsensicalBinOpError("**", other)
        raise SizePowerResultError()

    def __rpow__(self, other):
        # A Size exponent is meaningless.
        raise SizeNonsensicalBinOpError("rpow", other)

    def __ne__(self, other):
        return not isinstance(other, Size) or self._magnitude != int(other)

    def __sub__(self, other):
        # self - other = sub
        # Therefore, T(sub) = T(self) = Size and T(other) = Size.
        if not isinstance(other, Size):
            raise SizeNonsensicalBinOpError("-", other)
        return Size(self._magnitude - int(other))

    def __rsub__(self, other):
        # other - self = sub
        # Therefore, T(sub) = T(self) = Size and T(other) = Size.
        if not isinstance(other, Size):
            raise SizeNonsensicalBinOpError("rsub", other)
        return Size(int(other) - self._magnitude)

    def __truediv__(self, other):
        # other * truediv = self
        # Therefore, T(truediv) = Size, if T(other) is numeric
        #                       = Decimal, if T(other) is Size
        if isinstance(other, Size):
            return Decimal(self._magnitude).__truediv__(Decimal(int(other)))
        if isinstance(other, self._NUMERIC_TYPES):
            return Size(Decimal(self._magnitude).__truediv__(other))
        raise SizeNonsensicalBinOpError("truediv", other)

    __div__ = __truediv__

    def __rtruediv__(self, other):
        # self * truediv = other
        # Therefore, T(truediv) = Decimal and T(other) = Size.
        if not isinstance(other, Size):
            raise SizeNonsensicalBinOpError("rtruediv", other)
        return Decimal(int(other)).__truediv__(Decimal(self._magnitude))

    __rdiv__ = __rtruediv__

    def convertTo(self, spec=None):
        """ Return the size in the units indicated by the specifier.

            :param spec: a units specifier
            :type spec: a units specifier or :class:`Size`
            :returns: a numeric value in the units indicated by the specifier
            :rtype: Decimal
            :raises SizeNonsensicalOpError: if unit specifier is non-positive
        """
        spec = B if spec is None else spec
        factor = Decimal(int(getattr(spec, "factor", spec)))

        if factor <= 0:
            raise SizeNonsensicalOpError("can not convert to non-positive unit %s" % factor)

        return self._magnitude / factor

    def components(self, min_value=1):
        """ Return a representation of this size, decomposed into a
            Decimal value and a unit specifier tuple.

            :param min_value: Lower bound for value, default is 1.
            :type min_value: A precise numeric type: int, long, or Decimal
            :returns: a pair of a decimal value and a unit
            :rtype: tuple of Decimal and unit
            :raises SizeDisplayError: if min_value is not usable
        """
        if min_value < 0 or not isinstance(min_value, self._NUMERIC_TYPES):
            raise SizeDisplayError("min_value must be a precise positive numeric value.")

        # Find the smallest prefix which will allow a number less than
        # FACTOR * min_value to the left of the decimal point.
        # If the number is so large that no prefix will satisfy this
        # requirement use the largest prefix.
        limit = BinaryUnits.FACTOR * min_value
        for unit in [B] + BinaryUnits.UNITS:
            newcheck = self.convertTo(unit)

            if abs(newcheck) < limit:
                break

        # pylint: disable=undefined-loop-variable
        return (newcheck, unit)

    def humanReadableComponents(self, max_places=2, strip=True, min_value=1):
        """ Return a string representation of components with appropriate
            size specifier and in the specified number of decimal places.
            Values are always represented using binary not decimal units.
            For example, if the number of bytes represented by this size
            is 65531, expect the representation to be something like
            64.00 KiB, not 65.53 KB.

            :param max_places: number of decimal places to use, default is 2
            :type max_places: an integer type or NoneType
            :param bool strip: True if trailing zeros are to be stripped.
            :param min_value: Lower bound for value, default is 1.
            :type min_value: A precise numeric type: int, long, or Decimal
            :returns: a representation of the size as a pair of strings
            :rtype: tuple of str * str

            The meaning of the parameters is the same as for
            :class:`.config.StrConfig`.

            humanReadable() is a function that evaluates to a number which
            represents a range of values. For a constant choice of max_places,
            all ranges are of equal size, and are bisected by the result. So,
            if n.humanReadable() == x U and b is the number of bytes in 1 U,
            and e = 1/2 * 1/(10^max_places) * b, then x - e < n < x + e.

            The second part of the tuple is the unit prefix, e.g., "M", "Gi".
            The B (for bytes) is implicit.
        """
        if max_places is not None and \
           (max_places < 0 or not isinstance(max_places, six.integer_types)):
            raise SizeDisplayError(
               "max_places must be None or an non-negative integer value"
            )

        (magnitude, unit) = self.components(min_value)

        if max_places is not None:
            magnitude = magnitude.quantize(Decimal(10) ** -max_places)

        retval_str = str(magnitude)

        if '.' in retval_str and strip:
            retval_str = retval_str.rstrip("0").rstrip(".")

        return (retval_str, unit.abbr)

    def roundToNearest(self, unit, rounding):
        """ Rounds to nearest unit specified as a named constant or a Size.

            :param unit: a unit specifier
            :type unit: a named constant like KiB, or any non-negative Size
            :keyword rounding: which direction to round
            :type rounding: :class:`constants.RoundingMethod`
            :returns: Size rounded to nearest whole specified unit
            :rtype: :class:`Size`
            :raises SizeRoundingError: on unusable input

            If unit is Size(0), returns Size(0).
        """
        factor = Decimal(int(getattr(unit, "factor", unit)))

        if factor < 0:
            raise SizeRoundingError("invalid rounding unit: %s" % factor)

        if factor == 0:
            return Size(0)

        magnitude = (self._magnitude / factor)
        try:
            rounding = self._rounding_map[rounding]
        except KeyError:
            raise SizeRoundingError("invalid rounding method: %s" % rounding)

        rounded = magnitude.to_integral_value(rounding=rounding)
        return Size(rounded * factor)
