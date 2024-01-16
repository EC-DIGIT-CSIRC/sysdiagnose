
test: *.py parsers/* analysers/*
	python -m pytest --verbose tests
	# or: nosetests -v


lint: *.py parsers/* analysers/*
	pycodestyle --exclude=venv --ignore=errors=E221,E225,E251,E501,E266,E302 --max-line-length=128 $(git ls-files '*.py')
