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
# Red Hat Author(s): David Cantrell <dcantrell@redhat.com>
#                    Anne Mulhern <amulhern@redhat.com>

import locale
import re
import string

from collections import namedtuple
from decimal import Decimal
from decimal import InvalidOperation
from decimal import ROUND_DOWN, ROUND_UP, ROUND_HALF_UP

import six

from .errors import SizeConstructionError, SizeDisplayError
from .errors import SizeNonsensicalOpError, SizeParseError
from .errors import SizeRoundingError, SizeUnrepresentableOpError
from .i18n import _, N_
from .util import stringize, unicodeize

ROUND_DEFAULT = ROUND_HALF_UP

# Container for size unit prefix information
_Prefix = namedtuple("Prefix", ["factor", "prefix", "abbr"])

_DECIMAL_FACTOR = 10 ** 3
_BINARY_FACTOR = 2 ** 10

_BYTES_SYMBOL = N_(b"B")
_BYTES_WORDS = (N_(b"bytes"), N_(b"byte"))

# Symbolic constants for units
B = _Prefix(1, b"", b"")

KB = _Prefix(_DECIMAL_FACTOR ** 1, N_(b"kilo"), N_(b"k"))
MB = _Prefix(_DECIMAL_FACTOR ** 2, N_(b"mega"), N_(b"M"))
GB = _Prefix(_DECIMAL_FACTOR ** 3, N_(b"giga"), N_(b"G"))
TB = _Prefix(_DECIMAL_FACTOR ** 4, N_(b"tera"), N_(b"T"))
PB = _Prefix(_DECIMAL_FACTOR ** 5, N_(b"peta"), N_(b"P"))
EB = _Prefix(_DECIMAL_FACTOR ** 6, N_(b"exa"), N_(b"E"))
ZB = _Prefix(_DECIMAL_FACTOR ** 7, N_(b"zetta"), N_(b"Z"))
YB = _Prefix(_DECIMAL_FACTOR ** 8, N_(b"yotta"), N_(b"Y"))

KiB = _Prefix(_BINARY_FACTOR ** 1, N_(b"kibi"), N_(b"Ki"))
MiB = _Prefix(_BINARY_FACTOR ** 2, N_(b"mebi"), N_(b"Mi"))
GiB = _Prefix(_BINARY_FACTOR ** 3, N_(b"gibi"), N_(b"Gi"))
TiB = _Prefix(_BINARY_FACTOR ** 4, N_(b"tebi"), N_(b"Ti"))
PiB = _Prefix(_BINARY_FACTOR ** 5, N_(b"pebi"), N_(b"Pi"))
EiB = _Prefix(_BINARY_FACTOR ** 6, N_(b"exbi"), N_(b"Ei"))
ZiB = _Prefix(_BINARY_FACTOR ** 7, N_(b"zebi"), N_(b"Zi"))
YiB = _Prefix(_BINARY_FACTOR ** 8, N_(b"yobi"), N_(b"Yi"))

# Categories of symbolic constants
_DECIMAL_PREFIXES = [KB, MB, GB, TB, PB, EB, ZB, YB]
_BINARY_PREFIXES = [KiB, MiB, GiB, TiB, PiB, EiB, ZiB, YiB]
_EMPTY_PREFIX = B

if six.PY2:
    _ASCIIlower_table = string.maketrans(string.ascii_uppercase, string.ascii_lowercase) # pylint: disable=no-member
else:
    _ASCIIlower_table = str.maketrans(string.ascii_uppercase, string.ascii_lowercase) # pylint: disable=no-member

def _lowerASCII(s):
    """Convert a string to lowercase using only ASCII character definitions.

       :param str s: string to convert
       :returns: lower-cased string
       :rtype: str
    """
    if six.PY2:
        return string.translate(s, _ASCIIlower_table) # pylint: disable=no-member
    else:
        return str.translate(s, _ASCIIlower_table) # pylint: disable=no-member

def _makeSpec(prefix, suffix, xlate, lowercase=True):
    """ Synthesizes a whole word from prefix and suffix.

        :param str prefix: a prefix
        :param str suffixes: a suffix
        :param bool xlate: if True, treat as locale specific
        :param bool lowercase: if True, make all lowercase

        :returns:  whole word
        :rtype: str
    """
    if xlate:
        word = (_(prefix) + _(suffix))
        return word.lower() if lowercase else word
    else:
        word = prefix + suffix
        return _lowerASCII(word) if lowercase else word

def unitStr(unit, xlate=False):
    """ Return a string representation of unit.

        :param unit: a named unit, e.g., KiB
        :param bool xlate: if True, translate to current locale
        :rtype: some kind of string type
        :returns: string representation of unit
    """
    return _makeSpec(unit.abbr, _BYTES_SYMBOL, xlate, lowercase=False)

def parseUnits(spec, xlate):
    """ Parse a unit specification and return corresponding factor.

        :param spec: a units specifier
        :type spec: any type of string like object
        :param bool xlate: if True, assume locale specific

        :returns: a named constant corresponding to spec, if found
        :rtype: _Prefix or NoneType

        Looks first for exact matches for a specifier, but, failing that,
        searches for partial matches for abbreviations.

        Normalizes units to lowercase, e.g., MiB and mib are treated the same.
    """
    if spec == "":
        return B

    if xlate:
        spec = spec.lower()
    else:
        spec = _lowerASCII(spec)

    # Search for complete matches
    for unit in [_EMPTY_PREFIX] + _BINARY_PREFIXES + _DECIMAL_PREFIXES:
        if spec == _makeSpec(unit.abbr, _BYTES_SYMBOL, xlate) or \
           spec in (_makeSpec(unit.prefix, s, xlate) for s in _BYTES_WORDS):
            return unit

    # Search for unambiguous partial match among binary abbreviations
    matches = [p for p in _BINARY_PREFIXES if _makeSpec(p.abbr, "", xlate).startswith(spec)]
    if len(matches) == 1:
        return matches[0]

    return None

def parseSpec(spec):
    """ Parse string representation of size.

        :param spec: the specification of a size with, optionally, units
        :type spec: any type of string like object
        :returns: numeric value of the specification in bytes
        :rtype: Decimal

        :raises SizeParseError: if spec is unparseable

        Tries to parse the spec first as English, if that fails, as
        a locale specific string.
    """

    if not spec:
        raise SizeParseError("invalid size specification: %s" % spec)

    # Replace the localized radix character with a .
    radix = locale.nl_langinfo(locale.RADIXCHAR)
    if radix != '.':
        spec = spec.replace(radix, '.')

    m = re.match(r'(?P<numeric>(-|\+)?\s*(?P<base>([0-9]+)|([0-9]*\.[0-9]+)|([0-9]+\.[0-9]*))(?P<exp>(e|E)(-|\+)[0-9]+)?)\s*(?P<rest>[^\s]*)$', spec.strip())
    if not m:
        raise SizeParseError("invalid size specification: %s" % spec)

    try:
        size = Decimal(m.group('numeric'))
    except InvalidOperation:
        raise SizeParseError("invalid size specification: %s" % spec)

    specifier = m.group('rest')

    # First try to parse as English.
    try:
        if six.PY2:
            spec_ascii = str(specifier.decode("ascii"))
        else:
            spec_ascii = bytes(specifier, 'ascii')
    except (UnicodeDecodeError, UnicodeEncodeError):
        # String contains non-ascii characters, so can not be English.
        pass
    else:
        unit = parseUnits(spec_ascii, False)
        if unit is not None:
            return size * unit.factor

    # No English match found, try localized size specs.
    if six.PY2:
        if isinstance(specifier, unicode):
            spec_local = specifier
        else:
            spec_local = specifier.decode("utf-8")
    else:
        spec_local = specifier

    unit = parseUnits(spec_local, True)
    if unit is not None:
        return size * unit.factor

    raise SizeParseError("invalid size specification: %s" % spec)

class Size(object):

    def __init__(self, value=0, units=None):
        """ Initialize a new Size object.

            :param value: a size value, default is 0
            :type value: Size, or any numeric type (possibly as str)
            :param units: the units of the size, default is None
            :type units: any of the publicly defined units constants

            Must pass None as units argument if value has type Size.
        """
        if isinstance(value, six.integer_types):
            self.magnitude = value * (units or B).factor
        elif isinstance(value, (Decimal, float, six.string_types)):
            try:
                self.magnitude = int((Decimal(value) * (units or B).factor).to_integral_value(rounding=ROUND_DOWN))
            except InvalidOperation:
                raise SizeConstructionError("invalid value %s for size magnitude" % value)
        elif isinstance(value, Size):
            if units is not None:
                raise SizeConstructionError("units parameter is meaningless when Size value is passed")
            self.magnitude = value.magnitude
        else:
            raise SizeConstructionError("invalid value for size")

    # Force str and unicode types since the translated sizespec may be unicode
    def _toString(self):
        return self.humanReadable()

    def __str__(self, eng=False, context=None):
        return stringize(self._toString())

    def __unicode__(self):
        return unicodeize(self._toString())

    def __repr__(self):
        return "Size('%s')" % self.magnitude

    def __deepcopy__(self, memo):
        # pylint: disable=unused-argument
        return Size(self.convertTo())

    def __nonzero__(self):
        return self.magnitude != 0

    def __complex__(self):
        return complex(self.magnitude)

    def __int__(self):
        return self.magnitude
    __trunc__ = __int__

    def __float__(self):
        return float(self.magnitude)

    def __long__(self):
        return self.magnitude

    def __hash__(self):
        return hash(self.magnitude)

    # UNARY OPERATIONS

    def __abs__(self):
        return Size(abs(self.magnitude))

    def __neg__(self):
        return Size(-(self.magnitude))

    def __pos__(self):
        return Size(self.magnitude)

    # BINARY OPERATIONS

    def __add__(self, other):
        if not isinstance(other, Size):
            raise SizeNonsensicalOpError("unsupported operand type(s) for +: '%s' and '%s'" % (type(self).__name__, type(other).__name__))
        return Size(self.magnitude + other.magnitude)
    __radd__ = __add__

    def __divmod__(self, other):
        # other * div + rem = self
        # Therefore, T(rem) = T(self) = Size
        #            T(div) = Size, if T(other) is numeric
        #                   = int, if T(other) is Size
        if isinstance(other, Size):
            (div, rem) = divmod(self.magnitude, other.magnitude)
            return (div, Size(rem))
        if isinstance(other, (six.integer_types, float, Decimal)):
            (div, rem) = divmod(self.magnitude, other)
            return (Size(div), Size(rem))
        raise SizeNonsensicalOpError("unsupported operand type(s) for divmod '%s' and '%s'" % (type(self).__name__, type(other).__name__))

    def __rdivmod__(self, other):
        # self * div + rem = other
        # Therefore, T(rem) = T(other)
        #            T(div) = int
        # and T(other) is Size
        if not isinstance(other, Size):
            raise SizeNonsensicalOpError("unsupported operand type(s) for divmod '%s' and '%s'" % (type(self).__name__, type(other).__name__))
        (div, rem) = divmod(other.magnitude, self.magnitude)
        return (div, Size(rem))

    def __eq__(self, other):
        return isinstance(other, Size) and self.magnitude == other.magnitude

    def __floordiv__(self, other):
        # other * floor + rem = self
        # Therefore, T(floor) = Size, if T(other) is numeric
        #                     = int, if T(other) is Size
        if isinstance(other, Size):
            return self.magnitude // other.magnitude
        if isinstance(other, (six.integer_types, float, Decimal)):
            return Size(self.magnitude // other)
        raise SizeNonsensicalOpError("unsupported operand type(s) for floordiv: '%s' and '%s'" % (type(self).__name__, type(other).__name__))

    def __rfloordiv__(self, other):
        # self * floor + rem = other
        # Therefore, T(floor) = int and T(other) is Size
        if not isinstance(other, Size):
            raise SizeNonsensicalOpError("unsupported operand type(s) for floordiv: '%s' and '%s'" % (type(self).__name__, type(other).__name__))
        return other.magnitude // self.magnitude

    def __ge__(self, other):
        if not isinstance(other, Size):
            raise SizeNonsensicalOpError("unsupported operand type(s) for >: '%s' and '%s'" % (type(self).__name__, type(other).__name__))
        return self.magnitude >= other.magnitude

    def __gt__(self, other):
        if not isinstance(other, Size):
            raise SizeNonsensicalOpError("unsupported operand type(s) for >=: '%s' and '%s'" % (type(self).__name__, type(other).__name__))
        return self.magnitude > other.magnitude

    def __le__(self, other):
        if not isinstance(other, Size):
            raise SizeNonsensicalOpError("unsupported operand type(s) for <=: '%s' and '%s'" % (type(self).__name__, type(other).__name__))
        return self.magnitude <= other.magnitude

    def __lt__(self, other):
        if not isinstance(other, Size):
            raise SizeNonsensicalOpError("unsupported operand type(s) for <: '%s' and '%s'" % (type(self).__name__, type(other).__name__))
        return self.magnitude < other.magnitude

    def __mod__(self, other):
        # other * div + mod = self
        # Therefore, T(mod) = Size
        if isinstance(other, Size):
            return Size(self.magnitude % other.magnitude)
        if isinstance(other, (six.integer_types, float, Decimal)):
            return Size(self.magnitude % other)
        raise SizeNonsensicalOpError("unsupported operand type(s) for mod: '%s' and '%s'" % (type(self).__name__, type(other).__name__))

    def __rmod__(self, other):
        # self * div + mod = other
        # Therefore, T(mod) = T(other) and T(other) = Size.
        if not isinstance(other, Size):
            raise SizeNonsensicalOpError("unsupported operand type(s) for mod: '%s' and '%s'" % (type(self).__name__, type(other).__name__))
        return Size(other.magnitude % self.magnitude)

    def __mul__(self, other):
        # self * other = mul
        # Therefore, T(mul) = Size and T(other) is a numeric type.
        if isinstance(other, (six.integer_types, float, Decimal)):
            return Size(self.magnitude * other)
        if isinstance(other, Size):
            raise SizeUnrepresentableOpError("unsupported operand type(s) for *: '%s' and '%s'" % (type(self).__name__, type(other).__name__))
        raise SizeNonsensicalOpError("unsupported operand type(s) for *: '%s' and '%s'" % (type(self).__name__, type(other).__name__))
    __rmul__ = __mul__

    def __pow__(self, other):
        # Cannot represent multiples of Sizes.
        if not isinstance(other, (six.integer_types, float, Decimal)):
            raise SizeNonsensicalOpError("unsupported operand type(s) for **: '%s' and '%s'" % (type(self).__name__, type(other).__name__))
        raise SizeUnrepresentableOpError("unsupported operand type(s) for **: '%s' and '%s'" % (type(self).__name__, type(other).__name__))

    def __rpow__(self, other):
        # A Size exponent is meaningless.
        raise SizeNonsensicalOpError("unsupported operand type(s) for **: '%s' and '%s'" % (type(self).__name__, type(other).__name__))

    def __ne__(self, other):
        return not isinstance(other, Size) or self.magnitude != other.magnitude

    def __sub__(self, other):
        # self - other = sub
        # Therefore, T(sub) = T(self) = Size and T(other) = Size.
        if not isinstance(other, Size):
            raise SizeNonsensicalOpError("unsupported operand type(s) for /: '%s' and '%s'" % (type(self).__name__, type(other).__name__))
        return Size(self.magnitude - other.magnitude)

    def __rsub__(self, other):
        # other - self = sub
        # Therefore, T(sub) = T(self) = Size and T(other) = Size.
        if not isinstance(other, Size):
            raise SizeNonsensicalOpError("unsupported operand type(s) for /: '%s' and '%s'" % (type(self).__name__, type(other).__name__))
        return Size(other.magnitude - self.magnitude)

    def __truediv__(self, other):
        # other * truediv = self
        # Therefore, T(truediv) = Size, if T(other) is numeric
        #                       = Decimal, if T(other) is Size
        if isinstance(other, Size):
            return Decimal(self.magnitude) / Decimal(other.magnitude)
        if isinstance(other, (six.integer_types, float, Decimal)):
            return Size(Decimal(self.magnitude) / other)
        raise SizeNonsensicalOpError("unsupported operand type(s) for /: '%s' and '%s'" % (type(self).__name__, type(other).__name__))

    __div__ = __truediv__

    def __rtruediv__(self, other):
        # self * truediv = other
        # Therefore, T(truediv) = Decimal and T(other) = Size.
        if not isinstance(other, Size):
            raise SizeNonsensicalOpError("unsupported operand type(s) for /: '%s' and '%s'" % (type(self).__name__, type(other).__name__))
        return Decimal(other.magnitude) / Decimal(self.magnitude)

    __rdiv__ = __rtruediv__

    def convertTo(self, spec=None):
        """ Return the size in the units indicated by the specifier.

            :param spec: a units specifier
            :returns: a numeric value in the units indicated by the specifier
            :rtype: Decimal
        """
        return self.magnitude / Decimal((spec or B).factor)

    def humanReadable(self, max_places=2, strip=True, min_value=1, xlate=True):
        """ Return a string representation of this size with appropriate
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
            :param bool xlate: If True, translate for current locale
            :returns: a representation of the size
            :rtype: str

            If max_places is set to None, all non-zero digits will be shown.
            Otherwise, max_places digits will be shown.

            If strip is True and there is a fractional quantity, trailing
            zeros are removed up to the decimal point.

            min_value sets the smallest value allowed.
            If min_value is 10, then single digits on the lhs of
            the decimal will be avoided if possible. In that case,
            9216 KiB is preferred to 9 MiB. However, 1 B has no alternative.
            If min_value is 1, however, 9 MiB is preferred.
            If min_value is 0.1, then 0.75 GiB is preferred to 768 MiB,
            but 0.05 GiB is still displayed as 51.2 MiB.

            humanReadable() is a function that evaluates to a number which
            represents a range of values. For a constant choice of max_places,
            all ranges are of equal size, and are bisected by the result. So,
            if n.humanReadable() == x U and b is the number of bytes in 1 U,
            and e = 1/2 * 1/(10^max_places) * b, then x - e < n < x + e.
        """
        if max_places is not None and (max_places < 0 or not isinstance(max_places, six.integer_types)):
            raise SizeDisplayError("max_places must be None or an non-negative integer value")

        if min_value < 0 or not isinstance(min_value, (six.integer_types, Decimal)):
            raise SizeDisplayError("min_value must be a precise positive numeric value.")

        # Find the smallest prefix which will allow a number less than
        # _BINARY_FACTOR * min_value to the left of the decimal point.
        # If the number is so large that no prefix will satisfy this
        # requirement use the largest prefix.
        limit = _BINARY_FACTOR * min_value
        for unit in [_EMPTY_PREFIX] + _BINARY_PREFIXES:
            newcheck = self.convertTo(unit)

            if abs(newcheck) < limit:
                break

        if max_places is not None:
            newcheck = newcheck.quantize(Decimal(10) ** -max_places)

        retval_str = str(newcheck)

        if '.' in retval_str and strip:
            retval_str = retval_str.rstrip("0").rstrip(".")

        if xlate:
            radix = locale.nl_langinfo(locale.RADIXCHAR)
            if radix != '.':
                retval_str = retval_str.replace('.', radix)

        # pylint: disable=undefined-loop-variable
        return retval_str + " " + _makeSpec(unit.abbr, _BYTES_SYMBOL, xlate, lowercase=False)

    def roundToNearest(self, unit, rounding=ROUND_DEFAULT):
        """
            :param unit: a unit specifier, a named constant like KiB
            :keyword rounding: which direction to round
            :type rounding: one of ROUND_UP, ROUND_DOWN, or ROUND_DEFAULT
            :returns: Size rounded to nearest whole specified unit
            :rtype: :class:`Size`
        """
        if rounding not in (ROUND_UP, ROUND_DOWN, ROUND_DEFAULT):
            raise SizeRoundingError("invalid rounding specifier")

        rounded = self.convertTo(unit).to_integral_value(rounding=rounding)
        return Size(rounded * unit.factor)
