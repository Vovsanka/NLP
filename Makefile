TARGET = pcfg_tool
ENTRY  = src/main.py
VENV   = venv
PYTHON = $(VENV)/bin/python
PIP    = $(VENV)/bin/pip

all: venv $(TARGET)

# Create virtual environment and install requirements
venv: requirements.txt
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

# Build the executable wrapper
$(TARGET): $(ENTRY)
	echo "#!/usr/bin/env bash" > $(TARGET)
	echo "$(PYTHON) $(ENTRY) \"\$$@\"" >> $(TARGET)
	chmod +x $(TARGET)

clean:
	rm -f $(TARGET)
	rm -rf $(VENV)
