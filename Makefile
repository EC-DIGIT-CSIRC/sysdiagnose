
PY_FILES := $(shell git ls-files '*.py')


test: $(PY_FILES)
	python -m pytest --verbose tests
	# or: nosetests -v


lint: $(PY_FILES)
	@pycodestyle --exclude=venv --ignore=errors=E221,E225,E251,E501,E266,E302 \
		--max-line-length=128 \
		$(PY_FILES)
