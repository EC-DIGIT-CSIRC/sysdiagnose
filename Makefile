


test: *.py tests/* parsers/* analyzers/*
	python -m pytest --verbose tests
	# or: nosetests -v
