TOX=tox

.PHONY: lint
lint:
	$(TOX) -c tox.ini -e lint

.PHONY: coverage
coverage:
	$(TOX) -c tox.ini -e coverage

.PHONY: test
test:
	$(TOX) -c tox.ini -e test

PYREVERSE_OPTS = --output=pdf
.PHONY: view
view:
	-rm -Rf _pyreverse
	mkdir _pyreverse
	PYTHONPATH=src pyreverse ${PYREVERSE_OPTS} --project="bytesize" src/bytesize
	mv classes_bytesize.pdf _pyreverse
	mv packages_bytesize.pdf _pyreverse

.PHONY: archive
archive:
	git archive --output=./bytesize.tar.gz HEAD
