# CFG-Based Sentence Grammar Validator Using the CKY Algorithm

## Project Overview

This project is a rule-based NLP system that checks whether a sentence fits a small, controlled Context-Free Grammar (CFG). The grammar is expressed in a CKY-friendly Chomsky Normal Form style and parsed with the CKY algorithm to produce a `VALID` or `INVALID` result.

This is not a full English grammar checker. It is a scoped educational and engineering project for sentence validation within a narrow subset of English.

## Scope

The project supports Level 2 grammar only:

- simple declarative sentences
- noun phrase (`NP`) and verb phrase (`VP`) structures
- determiners
- nouns
- verbs
- adjectives
- pronouns
- proper names

Out of scope:

- prepositional phrases
- questions
- conjunctions
- clauses
- tense systems
- broad English grammar correction

## Supported Grammar Patterns

The starter grammar focuses on patterns such as:

- `S -> NP VP`
- `NP -> Det N`
- `NP -> Det Adj N`
- `NP -> Pronoun`
- `NP -> ProperNoun`
- `VP -> Verb`
- `VP -> Verb NP`

Example supported sentences:

- `the cat runs`
- `john sees mary`
- `she eats apple`
- `the big dog likes mary`
- `a small cat eats fish`

## Features

- rule-based CFG validation with a tightly scoped grammar
- CKY chart parsing for sentence recognition
- simple tokenization for controlled English input
- parse tree reconstruction for valid sentences
- lightweight explanations for valid and invalid results
- dataset evaluation utilities for manual experiments
- a small Streamlit interface for demos
- no machine learning training
- no API keys required

## Dataset Strategy

The dataset workflow keeps the task aligned with the supported grammar instead of over-claiming broad English coverage.

- `data/manual_level2_dataset.csv` is the curated manual source dataset.
- `data/jfleg_raw.csv` is optional downloaded external raw data from Hugging Face.
- `data/final_dataset.csv` is the actual evaluation input used by `evaluate.py`.
- `data/evaluation_results.csv` is the generated evaluation output.

The repository also includes two helper scripts for JFLEG-related workflow:

- `scripts/download_jfleg.py` downloads raw JFLEG examples for optional inspection
- `scripts/prepare_level2_dataset.py` prepares a filtered Level 2 evaluation dataset

JFLEG is not treated as a direct gold-standard grammar dataset for this project. Any external examples should be manually reviewed before being added to the Level 2 evaluation set.

## How to Run

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the command-line validator:

```bash
python run.py
```

Then enter a sentence when prompted, such as `the cat runs`.

Run dataset evaluation:

```bash
python evaluate.py
```

Run the Streamlit app:

```bash
streamlit run streamlit_app/app.py
```

## Limitations

- The lexicon is intentionally small and hand-crafted.
- A sentence may be valid in real English but still be rejected here if it falls outside the supported grammar.
- The parser is a validator, not a full grammar correction engine.
- Unsupported constructions are rejected even when they are grammatical English.
- Agreement, rich morphology, and tense variation are not modeled.

## Future Work

- expand the manual dataset with more balanced positive and negative examples
- improve explanation heuristics for invalid parses
- add optional grammar loading from external rule files
- compare multiple scoped grammars for classroom or research demos
- add visualization enhancements for parse charts and trees
