# Canonical Code and Documentation Language Standard

## Canonical technical language: English
MUBA source code is to use English as the canonical technical language.

Use English for:
- file/module/class/function/variable names;
- code comments and docstrings;
- commit messages;
- pull-request technical descriptions;
- schemas and machine-readable keys;
- architecture documents;
- recovery documents;
- build/deployment documentation;
- test names and engineering notes.

## Why
English is the canonical engineering language so a future developer, AI agent, GitHub collaborator or recovery operator can understand and maintain MUBA without depending on Turkish-only implementation details.

## What may be multilingual
User-facing product content is intentionally multilingual where required:
- Assistant responses;
- buttons;
- Guardian user/DEV report text;
- localized labels;
- community-facing content.

Current product languages are English, Turkish, Chinese, Arabic and Hindi.

Localized strings do not change the English-first code standard.

## Operator communication
The DEV may communicate in Turkish. A future AI/operator should normally answer the DEV in Turkish unless another language is requested.

Therefore:
- code and canonical technical docs = English;
- DEV conversation = Turkish by default;
- product UI/content = supported localized language.

## Rule for future code
Do not convert canonical source identifiers/comments into Turkish during maintenance. Add localization through explicit locale/catalog layers instead of mixing languages into control logic.
