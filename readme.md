# Natural Language Processing 
by Volodymyr Drobitko, KP "Algorithms in Application", 2026

## Prerequisites (Ubuntu 22.04)
```
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
```

## Run 
```
make

./pcfg_tool
```

## Base Tests
```
make -f tests.mk
```

## Unit and Integration Tests
```
make run_pcfg_tests

./run_pcfg_tests
```

## Grammar induction (Task 1)
Input (PTB) via stdin (multiline, press Enter one more time to finish the input)

Output: rules, lexicon and words in stdout
```
./pcfg_tool induce
```

Alterntive output: 'grammar.rules', 'grammar.lexicon' and 'grammar.words' (if the optional grammar name is set to grammar)
```
./pcfg_tool induce grammar
```
