Bytesize
========

Bytesize is a module for handling parsing, display, and computation with
sizes expressed in bytes. Its principle feature is a Size class from
which can be constructed Size objects which represent a precise, whole
quantity of bytes. Size object can be displayed in a locale-specific manner.
Strings which correspond to the module's interpretation of a locale-specific
representation of a number of bytes can be parsed and used to construct
Size objects. Various arithmetic operations are defined for Size objects.

Practical Computing with Bytes
------------------------------

When computing with bytes, the numeric value can be viewed as a logical,
rather than a physical, quantity. That is, unlike, e.g., mass or length,
which are quantities which must be measured with a measuring instrument
which has some built-in imprecision, the number of bytes of memory in RAM,
or on a disk, is a quantity that is not measured, but is known precisely.
Consequently, computations such as addition of two Sizes, and conversion
between different magnitudes of bytes, i.e., from MiB to GiB, must be done
precisely. The underlying implementation must therefore use a precise
representation of the number of bytes. Floating point numbers, which are
frequently the preferred type for the representation of physical
quantities, are disallowed by this requirement.

This module does not accomodate multi-dimensionality of byte quantities.
Consequently, multiplying one Size object by another Size object will cause
an error to be raised, since bytes^2 is not representable by the module.
For most uses, and for all uses in blivet from which this module originates,
any operation which would yield a multi-dimensional quantity of bytes is not
useful. There are no plans to adapt this package so that it can accomodate
multi-dimensionality of bytes.

Numerous computations with bytes are nonsensical. For example, 2 raised to a
power which is some number of bytes, is a meaningless computation. All such
operations cause an error to be raised.

Displaying Sizes
----------------
Sizes are displayed using binary rather than SI prefixes or names, regardless
of the value. For example, 1000 bytes is not displayed as 1KB
(1 kilobyte), but as some number of bytes or KiB (kibibytes). The precise
form in which a Size is displayed is configurable by means of many parameters
of the humanReadable() method.

Representing Units
------------------
The size module supplies a set of named prefixes for both SI and binary units,
for all non-fractional prefixes. Fractional prefixes are not defined, since
fractional bytes are not of interest.

Parsing strings as Sizes
------------------------
Generally speaking, parsing a free form string as a specification of a number
of bytes in what may be a foreign locale is bound to be an error-prone process.
Whenever a number of bytes is known precisely at compile-time, it is much
better to avoid string parsing and make use of the units presented by the
Size module. Parsing should be reserved solely for user-input values when
no other alternative is available. A partial approach, where the user enters
a number, but the units are not user-input, is less error-prone than parsing
a user-entered string.

Constructing Sizes Programatically
----------------------------------
New Size objects can be constructed from Size objects, numeric values, e.g.,
ints, floats, or Decimal, or strings which represent such numeric values.
The constructor takes an optional units specifier, which defaults to bytes
for all numeric values, and to None for Size objects. The type of the
unit specifier is a named prefix supplied by the size module. Fractional
quantities are rounded down to whole numbers of bytes.

Errors
------
All errors raised by bytesize operations are subtypes of the SizeError class.

Alternative Packages
--------------------
If you are interested in computing in Python with physical, rather than
logical, quantities, you should consult the pint package:
http://pint.readthedocs.org.
