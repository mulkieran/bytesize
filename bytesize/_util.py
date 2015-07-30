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

import six

from ._errors import SizeValueError

def format_magnitude(value, max_places=2, strip=False):
    """ Format a numeric value.

        :param value: any value
        :type value: a numeric value, convertible to Decimal, not a float
        :param max_places: number of decimal places to use, default is 2
        :type max_place: an integer type or NoneType
        :param bool strip: True if trailing zeros are to be stripped

        :returns: the formatted value
        :rtype: str
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

    value = Decimal(value)

    if max_places is not None:
        value = value.quantize(Decimal(10) ** -max_places)

    retval_str = str(value)

    if '.' in retval_str and strip:
        retval_str = retval_str.rstrip("0").rstrip(".")

    return retval_str
