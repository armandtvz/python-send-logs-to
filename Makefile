coverage:
	pytest --cov=log_to --cov-report html

build:
	python3 -m build && \
	pip install twine --upgrade && \
	twine upload dist/*
