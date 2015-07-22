# errors.py
# Exception classes for bytesize module.
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

""" Exception types used by the bytesize class. """

class SizeError(Exception):
    """ Generic Size error. """
    pass

class SizeConstructionError(SizeError):
    """ Error that occurs while constructing a Size object. """
    pass

class SizeDisplayError(SizeError):
    """ Error while displaying Size object. """
    pass

class SizeRoundingError(SizeError):
    """ Error while rounding Size object. """
    pass

class SizeUnsupportedOpError(SizeError):
    """ Error when executing unsupported operation on Size. """
    pass

class SizeNonsensicalOpError(SizeUnsupportedOpError):
    """ Error when requesting an operation that doesn't make sense. """
    pass

class SizeNonsensicalBinOpError(SizeNonsensicalOpError):
    """ Error when requesting a binary operation that doesn't make sense. """
    _FMT_STR = "unsupported operand type(s) for %s: 'Size' and '%s'"

    def __init__(self, operator, other):
        """ Initializer.

            :param str operator: the operator
            :param object other: the other argument
        """
        # pylint: disable=super-init-not-called
        self._operator = operator
        self._other = other

    def __str__(self):
        return self._FMT_STR % (self._operator, type(self._other).__name__)

class SizeUnrepresentableOpError(SizeUnsupportedOpError):
    """ Error when requesting an operation that yields units that cannot
        be represented with Size, e.g., when multiplying a Size by a Size.
    """
    pass
