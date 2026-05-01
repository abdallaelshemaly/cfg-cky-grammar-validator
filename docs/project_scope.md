# Project Scope

## Core Goal

Build a rule-based sentence validator that uses a small Context-Free Grammar and
the CKY algorithm to determine whether an input sentence belongs to the
supported grammar.

## In Scope

- simple declarative sentences
- sentence structure based on `S -> NP VP`
- noun phrases with determiners, adjectives, nouns, pronouns, and proper names
- verb phrases with either a single verb or a verb followed by a noun phrase
- manual evaluation on a small curated dataset

## Out of Scope

- full English grammar checking
- prepositional phrases
- questions and interrogative patterns
- conjunctions and coordinated phrases
- subordinate or relative clauses
- tense and aspect modeling
- grammar correction or rewrite generation

## Success Criteria

- The parser accepts supported Level 2 sentences.
- The parser rejects unsupported structures.
- The repository clearly documents its narrow scope and limitations.
