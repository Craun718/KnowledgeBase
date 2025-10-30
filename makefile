configure:
	pip install uv
	uv sync

build:
	uv run load_pdf.py
	docker build -t knowledge-base .
	docker save knowledge-base -o knowledge-base.tar

all: configure build