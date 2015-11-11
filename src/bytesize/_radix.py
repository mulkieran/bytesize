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

""" Class for handling numbers in various bases. """

from ._util.bases import convert_to

class BaseInteger(object):
    # pylint: disable=too-few-public-methods
    """ An integer encoded as a list of ints and a base. """

    def __init__(self, sign, value, base):
        """ Initializer.

            :param bool sign: True if positive, otherwise False
            :param value: the absolute value
            :type value: list of int
            :param int base: the base
        """
        self._sign = sign
        self._value = value
        self._base = base

    def __str__(self):
        sign = "+" if self._sign else "-"
        value = ",".join(self._value)
        base = "base %s" % self._base
        return sign + "(%s)" % value + "[%s]" % base

    def convertTo(self, base):
        """ Convert to designated base.

            :param int base: the designated base (> than 1)
            :returns: converted value
            :rtype: :class:`BaseInt`
        """
        value = convert_to(self._value, self._base, base)
        return BaseInteger(self._sign, value, base)

class RadixNumber(object):
    # pylint: disable=too-few-public-methods
    """ Class for instantiating RadixNumber objects.

        This class is just another way of representing rationl numbers
        and should be interconvertible with Fraction.
    """

    def __init__(self, left, right, repeat_length, base, sign=True):
        # pylint: disable=too-many-arguments
        """ Initialize a new RadixNumber object.

            :param left: digits to the left of the radix
            :type left: list of int
            :param right: digits to the right of the radix
            :type right: list of int
            :param int repeat_length: the length of the repeating part
            :param int base: the base of the number
            :param bool sign: True if positive, otherwise False

            If repeat_length is 0, the number is non-repeating.

            base must be greater than 1.
        """
        self._left = left
        self._right = right
        self._repeat_length = repeat_length
        self._base = base
        self._sign = sign
