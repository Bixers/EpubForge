# Product

## Register

product

## Users

Windows users who organize novels, documents, and archived text into EPUB files. They often work with local Chinese paths, mixed encodings, long TXT files, and batches of source files that must be checked before conversion.

## Product Purpose

EpubForge converts TXT, Markdown, HTML, MOBI, and AZW3 sources into EPUB files while making the conversion process inspectable. Success means users can import files, verify chapter splitting, edit detected content when needed, and produce EPUB output without losing text.

## Brand Personality

Practical, trustworthy, precise. The interface should feel like a capable desktop workshop for book production, not a marketing page or a decorative reader.

## Anti-references

Do not use a sparse demo-like layout with unclear state, tiny metadata panels, or conversion controls that hide what will happen. Avoid decorative dashboards, card-heavy landing-page composition, oversized headings, and any UI that makes editing or verification feel secondary.

## Design Principles

- Preserve content first: every parser and editor path must make text loss visible and avoid silently dropping source material.
- Inspect before converting: chapter detection, metadata, logs, and output paths should be reviewable from the main workflow.
- Edit in place: users should be able to correct titles and chapter content without leaving the conversion task.
- Dense but calm: prioritize tables, panels, tabs, and clear controls over decorative layout.
- Fail visibly: conversion errors and unsupported paths should produce actionable logs.

## Accessibility & Inclusion

Target WCAG AA contrast for text and controls. Preserve keyboard-friendly standard Qt widgets, visible focus states, readable Chinese labels, reduced decorative motion, and clear status text for success, failure, and cancellation.
