# __init__.py
# Python module for sizes in bytes.
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

""" The public interface of the bytesize package.

    Contents:

    * Unit constants in SI and binary units
       - Universal:
          * B

       - SI:
          * KB
          * MB
          * GB
          * TB
          * PB
          * EB
          * ZB
          * YB

       - Binary:
          * KiB
          * MiB
          * GiB
          * TiB
          * PiB
          * EiB
          * ZiB
          * YiB

    * Rounding constants, with meaning as for the Python decimal module:
       - ROUND_DOWN
       - ROUND_HALF_DOWN
       - ROUND_HALF_UP
       - ROUND_UP

    * Configuration classes:
       - :class:`.config.StrConfig`

    * Exception classes:
       - :class:`.errors.SizeError`

    * Size classes:
       - :class:`.size.Size`

    All parts of the public interface of bytesize must be imported directly
    from the top-level bytesize module, as::

        from bytesize import Size
        from bytesize import KiB
        from bytesize import SizeError

        s = Size(24, KiB)
        try:
            s + 32
        except SizeError as e:
            raise e
"""

# UNIT CONSTANTS
from .constants import B
from .constants import KB
from .constants import MB
from .constants import GB
from .constants import TB
from .constants import PB
from .constants import EB
from .constants import ZB
from .constants import YB
from .constants import KiB
from .constants import MiB
from .constants import GiB
from .constants import TiB
from .constants import PiB
from .constants import EiB
from .constants import ZiB
from .constants import YiB

# ROUNDING CONSTANTS
from .constants import ROUND_DOWN
from .constants import ROUND_HALF_DOWN
from .constants import ROUND_HALF_UP
from .constants import ROUND_UP

# CONFIGURATION
from .config import StrConfig

# EXCEPTIONS
from .errors import SizeError

# SIZE
from .size import Size
