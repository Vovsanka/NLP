# Executable name
TARGET = pcfg_tool

# Python entry point inside src/
ENTRY = src/main.py

# Default target
all: $(TARGET)

# Build the executable wrapper
$(TARGET): $(ENTRY)
	# (TAB) create wrapper script
	echo "#!/usr/bin/env bash" > $(TARGET)
	echo "python3 $(ENTRY) \"\$$@\"" >> $(TARGET)
	chmod +x $(TARGET)

# Clean generated files
clean:
	rm -f $(TARGET)
