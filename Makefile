
PY_FILES := $(shell git ls-files '*.py')


test: $(PY_FILES)
	python -m pytest --verbose tests
	# or: nosetests -v
