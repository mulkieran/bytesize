# util.py
# Python module with some string related utilities.
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
# Red Hat Author(s): David Shea <davidshea@redhat.com>
#                    Anne Mulhern <amulhern@redhat.com>

import six

# Most Python 2/3 compatibility code equates python 2 str with python 3 bytes,
# but the equivalence that we actually need to avoid return type surprises is
# str/str.
def stringize(inputstr):
    """ Convert strings to a format compatible with Python 2's str.

        :param str inputstr: the string to convert

        :returns: a string with the correct type
        :rtype: str

        This method is for use in __str__ calls to ensure that they always
        return a str. In Python 3, this method simply inputstr as a string. In
        Python 2, it converts unicode into str. The returned str in python 2 is
        encoded using utf-8.
    """
    if six.PY2:
        if isinstance(inputstr, unicode):
            inputstr = inputstr.encode('utf-8')

    return str(inputstr)

# Like six.u, but without the part where it raises an exception on unicode
# objects
def unicodeize(inputstr):
    """ Convert strings to a format compatible with Python 2's unicode.

        :param str inputstr: the string to convert

        :returns: a string with the correct type
        :rtype: unicode

        This method is for use in __unicode__ calls to ensure that they always
        return a unicode. This method does not handle non-ASCII characters
        in str parameters, but non-ASCII characters in unicode parameters will
        be correctly passed through.
    """
    if six.PY2:
        return unicode(inputstr)
    else:
        return str(inputstr)
