TARGET = pcfg_tool
ENTRY  = src/main.py
VENV   = venv
PYTHON = $(VENV)/bin/python
PIP    = $(VENV)/bin/pip
TESTS  = run_pcfg_tests

all: $(TARGET)

$(VENV): requirements.txt
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

$(TARGET): $(VENV) $(ENTRY)
	echo "#!/usr/bin/env bash" > $(TARGET)
	echo "$(CURDIR)/$(PYTHON) $(CURDIR)/$(ENTRY) \"\$$@\"" >> $(TARGET)
	chmod +x $(TARGET)

$(TESTS): $(VENV)
	echo "#!/usr/bin/env bash" > $(TESTS)
	echo "PYTHONPATH=$(CURDIR)/src:$$PYTHONPATH $(CURDIR)/$(PYTHON) -m pytest -q" >> $(TESTS)
	chmod +x $(TESTS)

clean:
	rm -f $(TARGET) $(TESTS)
	rm -rf $(VENV)
