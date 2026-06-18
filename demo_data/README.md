# IRIP Demo And Evaluation Data

This directory contains synthetic, non-PII data for demonstrating and regression-testing IRIP.

## Contents

- `meeting_transcripts/`: finance-flavored meeting notes for extraction tests.
- `expected_outputs/`: labelled expected companies, contacts, actions, CRM fields, and duplicate expectations.
- `crm_seed.csv`: CRM records with intentional duplicate-like and missing-field examples.
- `research_docs/`: source documents for RAG and research memo demos.
- `prompt_tests.csv`: verbose prompts for token-optimization scoring.

## Evaluation Goals

- Meeting extraction: company, people, action-item recall, and CRM required-field completeness.
- CRM preflight: missing required fields and duplicate-warning behavior.
- RAG/research: source retrieval for target company questions.
- Token optimizer: prompt token reduction and cost savings.

All people and organizations are synthetic.
