# Project Scope

## Core Goal

Build a rule-based sentence validator that uses a small Context-Free Grammar and
the CKY algorithm to determine whether an input sentence belongs to the
supported grammar.

This repository does not train any machine learning model and does not require
API keys. It is a deterministic, rule-based NLP project.

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

## Why is the Scope Limited

The scope of this project is intentionally limited to maintain focus and feasibility. Full English grammar encompasses thousands of rules, exceptions, and contextual nuances that would make the system computationally expensive and error-prone and too big for a small university project. By restricting to Level 2 grammar, we can:

- Demonstrate core NLP concepts like CFG parsing and CKY algorithm effectively.
- Ensure high accuracy within the supported domain.
- Keep the project manageable for educational purposes.
- Avoid the errors of over-generalization in grammar checking.

This approach aligns with the project's goal as a scoped educational tool.

## Success Criteria

- The parser accepts supported Level 2 sentences.
- The parser rejects unsupported structures.
- The repository clearly documents its narrow scope and limitations.
