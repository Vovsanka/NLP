# Natural Language Processing 
by Volodymyr Drobitko, KP "Algorithms in Application", 2026

## Prerequisites (Linux Ubuntu)
Python, pip and virtual environment creation
```
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
```

## Run 
```
make

./pcfg_tool
```

### Base Tests
```
make -f tests.mk
```

### Unit and Integration Tests
```
make run_pcfg_tests

./run_pcfg_tests
```

## Grammar induction (Task 1)
The normalized grammar PCFG is obtained on-the-fly by processing the PTB trees one by one.
Each tree is converted to a special 'SymbolicExpression' representation,
which contributes to the accumulation structures for non-terminal node labels, syntactic rules, lexical rules and words.
The accumulation structures are used to construct the final PCFG.

Input: (PTB) via stdin (multiline, press Enter one more time to finish the input)
Output: rules, lexicon and words (stdout or 'GRAMMAR.rules',GRAMMAR.lexicon' and GRAMMAR.words') 
```
./pcfg_tool induce [GRAMMAR]
```

## Sentence Parsing (Task 2)
Sentences are parsed one by one using the deductive parsing (Knuth's algorithm).
Non-terminals as well as rules are encoded as integers to improve the overall perfomance. 

Input: preprocessed sentences via stdin (multiline, press Enter one more time to finish the input)
Output: derivation trees in PTB format
```
./pcfg_tool parse [OPTIONS] GRAMMAR.rules GRAMMAR.lexicon
```

## Binarisation and Debinarisation (Tasks 3c and 3a)
1. The training corpus is binarized (Task 3c)
2. A binarized grammar is induced 
3. The test sentences are parsed into binarized derivation trees 
4. The derivation trees are debinarized (Task 3a)

Input: (PTB) via stdin (multiline, press Enter one more time to finish the input)
Output: (PTB) via stdout
```
./pcfg_tool binarise
```
```
./pcfg_tool debinarise
```

## Unking and Smoothing (Tasks 3b and 3d)
1. Rare words in the training corpus are replaced with UNK
2. A grammar with the rules for UNK is induced
3. Unknown words in the test sentences are replaced by UNK before parsing
4. After parsing, the original words are restored in the derivation trees

Smoothing is unking that distinguishes between different types of rare/unknown words by generating a signature UNK\[suffix1\]\[suffix2\]...

Input: (PTB) via stdin (multiline, press Enter one more time to finish the input)
Output: (PTB) via stdout
```
.pcfg_tool unk
```
```
.pcfg_tool smooth
```
```
./pcfg_tool parse -u [OPTIONS] GRAMMAR.rules GRAMMAR.lexicon
```
```
./pcfg_tool parse -u -s [OPTIONS] GRAMMAR.rules GRAMMAR.lexicon
```

## Pruning (Task 4a)
Pruning optimizes the deductive parsing by internally omitting the worst options: (may miss the optimal solution)
1. that do not satisfy a probability threshold T
2. that do not belong to the best R probabilities
```
./pcfg_tool parse -t  T [OPTIONS] GRAMMAR.rules GRAMMAR.lexicon
```
```
./pcfg_tool parse -r  R [OPTIONS] GRAMMAR.rules GRAMMAR.lexicon
```

## A* (Task 4b)
A*-search optimizes the deductive parsing by prioritizing the larger spans using the outside weights for the nonterminals (heuristic).
1. The outside weights for the nonterminals are precomputed
2. The outside weights are used the parsing with the A*-search
```
pcfg_tool outside [OPTIONS] RULES LEXICON [GRAMMAR]
```
```
./pcfg_tool parse -a PATH [OPTIONS] GRAMMAR.rules GRAMMAR.lexicon
```