null    :=
space   := $(null) #
comma   := ,

PYTHON := python2

COVERAGE := coverage
PYLINT := pylint
PYREVERSE := pyreverse
ifeq ($(PYTHON),python3)
   COVERAGE := coverage3
   PYLINT := python3-pylint
   PYREVERSE := python3-pyreverse
endif

check:
	$(PYLINT) bytesize \
		--reports=no \
		--disable=I \
		--disable=bad-continuation \
		--disable=invalid-name
	$(PYLINT) tests \
		--reports=no \
		--disable=I \
		--disable=bad-continuation \
		--disable=duplicate-code \
		--disable=invalid-name \
		--disable=too-many-public-methods

PYREVERSE_OPTS = --output=pdf
view:
	-rm -Rf _pyreverse
	mkdir _pyreverse
	PYTHONPATH=. $(PYREVERSE) ${PYREVERSE_OPTS} --project="bytesize" bytesize
	mv classes_bytesize.pdf _pyreverse
	mv packages_bytesize.pdf _pyreverse

doc-html:
	cd doc; $(MAKE) clean html

clean:
	-rm -Rf _pyreverse

test:
	PYTHONPATH=.:tests/ $(PYTHON) -m unittest discover -v -s tests/ -p '*_test.py'

pytest:
	py.test -p no:doctest --durations=10

OMIT_PATHS = 
OMIT = $(subst $(space),$(comma),$(strip $(OMIT_PATHS)))
coverage:
	PYTHONPATH=.:tests/ $(COVERAGE) run --timid --branch --omit="$(OMIT)" -m unittest discover -v -s tests/ -p '*_test.py'
	$(COVERAGE) report --include="bytesize/*"
	$(COVERAGE) html --include="bytesize/*"

archive:
	git archive --format tar.gz HEAD > bytesize.tar.gz
