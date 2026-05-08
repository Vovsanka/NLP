TARGET = pcfg_tool
ENTRY  = src/main.py
VENV   = venv
PYTHON = $(VENV)/bin/python
PIP    = $(VENV)/bin/pip

all: $(TARGET)

$(VENV): requirements.txt
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

$(TARGET): $(VENV) $(ENTRY)
	echo "#!/usr/bin/env bash" > $(TARGET)
	echo "$(CURDIR)/$(PYTHON) $(CURDIR)/$(ENTRY) \"\$$@\"" >> $(TARGET)
	chmod +x $(TARGET)

clean:
	rm -f $(TARGET)
	rm -rf $(VENV)
