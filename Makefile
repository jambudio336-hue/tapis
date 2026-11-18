.PHONY: install init serve test lint verify clean

install:
	./install.sh

init:
	python -m tapis init

serve:
	python -m tapis serve

test:
	pytest -q

lint:
	ruff check tapis

verify:
	@read -p "target id: " t; python -m tapis verify $$t

clean:
	rm -rf .venv data/tapis.db data/audio
