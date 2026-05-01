# Report Outline

## 1. Introduction

- problem statement
- motivation for a rule-based CFG validator
- why CKY is a suitable parsing algorithm

## 2. Scope Definition

- supported Level 2 grammar
- excluded constructions
- rationale for keeping the task narrow

## 3. Grammar Design

- non-terminals and terminals
- lexicon design
- supported production patterns

## 4. CKY Parsing Approach

- chart structure
- lexical initialization
- binary combination
- unary closure

## 5. System Components

- tokenizer
- grammar module
- parser
- parse tree builder
- explainer
- evaluator

## 6. Dataset Strategy

- manual dataset construction
- positive and negative examples
- optional JFLEG candidate harvesting and manual review

## 7. Results

- sample parses
- evaluation accuracy on the manual dataset
- analysis of common failure cases

## 8. Limitations

- restricted lexicon
- lack of agreement or tense modeling
- inability to cover broad English grammar

## 9. Future Work

- richer scoped grammars
- better explanation quality
- larger curated datasets
