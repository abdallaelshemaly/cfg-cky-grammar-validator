# Methodology

## 1. Tokenization

The sentence is first normalized using a lightweight tokenizer:

- lowercase text
- strip punctuation and non-alphabetic characters
- normalize whitespace
- split into individual word tokens

This simple tokenization is sufficient for the controlled Level 2 grammar and
avoids the complexity of full English preprocessing.

## 2. Controlled CFG Design

The project uses a small, hand-crafted Context-Free Grammar (CFG) focused on
Level 2 sentence structures:

- `S -> NP VP`
- noun phrases with determiners, adjectives, nouns, pronouns, and proper names
- verb phrases with either a single verb or a verb followed by a noun phrase

The grammar is intentionally narrow so the system remains interpretable and
aligned with the supported sentence patterns.

## 3. CNF-Compatible Grammar Representation

Grammar rules are stored in a CKY-friendly, CNF-compatible representation:

- lexical rules map tokens to part-of-speech categories
- binary rules combine two non-terminals into a parent constituent
- unary rules lift categories where needed to support the CFG

This structure keeps parsing compatible with the CKY dynamic programming
algorithm while still representing the supported grammar patterns.

## 4. CKY Parsing

The parser builds a chart bottom-up using the CKY algorithm:

- assign lexical categories to single-token spans
- apply unary closure so chained category derivations are captured
- combine adjacent spans with binary rules
- fill each chart cell with all categories that derive that span

A sentence is accepted only if the full sentence span derives the start symbol
`S`.

## 5. VALID / INVALID Classification

After parsing, the sentence is classified as:

- `VALID` when the chart derives `S` over the entire sentence span
- `INVALID` when `S` is not present for the full sentence span

Unknown tokens are also tracked and contribute to invalid classification when
they prevent lexical assignment.

## 6. Explanation System

The explanation logic is kept concise and diagnostic:

- valid sentences are reported as accepted by the grammar
- invalid sentences are explained by missing phrase structure, unsupported
  token order, or unknown tokens

This provides lightweight feedback without attempting full grammatical
correction.

## 7. Dataset Filtering and Evaluation

Evaluation is based on a small, manually curated Level 2 dataset. The workflow
is:

- use manual examples that match the supported grammar
- optionally mine external sources such as JFLEG for candidate sentences
- apply dataset filtering to select short, relevant examples for manual review
- label examples according to the narrow project scope before including them

This process ensures evaluation stays aligned with the controlled grammar and
avoids overclaiming broad English coverage.