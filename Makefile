PKGNAME=bytesize
SPECFILE=python-bytesize.spec
VERSION=$(shell awk '/Version:/ { print $$2 }' $(SPECFILE))
RELEASE=$(shell awk '/Release:/ { print $$2 }' $(SPECFILE) | sed -e 's|%.*$$||g')
RELEASE_TAG=$(PKGNAME)-$(VERSION)-$(RELEASE)
VERSION_TAG=$(PKGNAME)-$(VERSION)

ChangeLog:
	(GIT_DIR=.git git log > .changelog.tmp && mv .changelog.tmp ChangeLog; rm -f .changelog.tmp) || (touch ChangeLog; echo 'git directory not found: installing possibly empty changelog.' >&2)

tag:
	@if test $(RELEASE) = "1" ; then \
          tags='$(VERSION_TAG) $(RELEASE_TAG)' ; \
        else \
          tags='$(RELEASE_TAG)' ; \
        fi ; \
        for tag in $$tags ; do \
          git tag -a -m "Tag as $$tag" -f $$tag ; \
          echo "Tagged as $$tag" ; \
        done

release: tag archive

archive:
	@rm -f ChangeLog
	@make ChangeLog
	git archive --format=tar --prefix=$(PKGNAME)-$(VERSION)/ $(VERSION_TAG) > $(PKGNAME)-$(VERSION).tar
	mkdir $(PKGNAME)-$(VERSION)
	cp -r po $(PKGNAME)-$(VERSION)
	cp ChangeLog $(PKGNAME)-$(VERSION)/
	tar -rf $(PKGNAME)-$(VERSION).tar $(PKGNAME)-$(VERSION)
	gzip -9 $(PKGNAME)-$(VERSION).tar
	rm -rf $(PKGNAME)-$(VERSION)
	@echo "The archive is in $(PKGNAME)-$(VERSION).tar.gz"

bumpver:
	@opts="-n $(PKGNAME) -v $(VERSION) -r $(RELEASE) -s $(SPECFILE)" ; \
        if [ ! -z "$(IGNORE)" ]; then \
                opts="$${opts} -i $(IGNORE)" ; \
        fi ; \
        if [ ! -z "$(MAP)" ]; then \
                opts="$${opts} -m $(MAP)" ; \
        fi ; \
        if [ ! -z "$(BZDEBUG)" ]; then \
                opts="$${opts} -d" ; \
        fi ; \
        ( scripts/makebumpver $${opts} ) || exit 1

potfile:
	make -C po $(PKGNAME).pot

install:
	python setup.py install --root=$(DESTDIR)

clean:
	-rm *.tar.gz
	-rm bytesize/*.pyc
	-rm ChangeLog
	-python setup.py -q clean --all

test:
	PYTHONPATH=.:tests/ python3 -m unittest discover -v -s tests/ -p '*_test.py'

check:
	pylint bytesize tests --disable=I --disable=bad-continuation --disable=invalid-name --reports=no

coverage:
	 PYTHONPATH=.:tests/ coverage run --timid --branch -m unittest discover -v -s tests/ -p '*_test.py'
	coverage report --include="bytesize/*"
	coverage html --include="bytesize/*"

