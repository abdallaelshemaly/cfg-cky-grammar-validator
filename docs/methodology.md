# Methodology

## 1. Controlled Grammar Design

Define a small CFG for Level 2 grammar coverage only. Keep the lexicon
hand-crafted so the project remains interpretable and aligned with the supported
sentence patterns.

## 2. CKY-Friendly Rule Representation

Store the grammar in a CNF-style representation:

- binary rules for phrase composition
- unary rules for category lifting
- lexical rules for token-to-category assignment

This keeps parsing compatible with standard CKY dynamic programming.

## 3. Tokenization

Apply a lightweight tokenizer that lowercases text and extracts alphabetic word
tokens. The tokenizer is intentionally simple because the project does not aim
to handle broad punctuation or rich morphology.

## 4. Parsing

Use CKY chart parsing to fill spans bottom-up:

- assign lexical categories
- apply unary closure
- combine constituents with binary rules
- accept the sentence only if the full span derives `S`

## 5. Explanation

After parsing, generate a short explanation:

- valid sentence if the chart derives `S`
- invalid because of unknown tokens, missing phrase structure, or unsupported
  token order otherwise

## 6. Evaluation

Evaluate first on a manual dataset tailored to the grammar. Optional external
datasets such as JFLEG can be mined for candidate sentences, but only after
manual review and relabeling for this project's limited scope.
