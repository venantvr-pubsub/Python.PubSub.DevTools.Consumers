# Defines the virtual environment directory
VENV_DIR = .venv
# Defines the Python interpreter from the virtual environment
PYTHON = $(VENV_DIR)/bin/python

# Prevents make from confusing the targets with files
.PHONY: setup-dev setup-prod test clean

# Default target
all: setup-dev

# Creates the virtual environment and installs development dependencies
setup-dev: $(VENV_DIR)/.setup-dev-complete

$(VENV_DIR)/.setup-dev-complete: pyproject.toml
	test -d $(VENV_DIR) || python3 -m venv $(VENV_DIR)
	$(PYTHON) -m pip install -e ".[dev]"
	touch $(VENV_DIR)/.setup-dev-complete

# Creates the virtual environment and installs production dependencies
setup-prod:
	test -d $(VENV_DIR) || python3 -m venv $(VENV_DIR)
	$(PYTHON) -m pip install .

# Runs tests
test: setup-dev
	$(PYTHON) -m pytest

# Removes the virtual environment and temporary files
clean:
	rm -rf $(VENV_DIR)
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
