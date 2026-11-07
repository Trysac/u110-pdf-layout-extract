# Use recursive XY-cut with table detection and hyphenation healing for reading-order extraction

Status: accepted (generated, pending human review)

## Context

Standard PDF text extraction frequently interleaves columns, degrades tables into unreadable strings, and separates hyphenated words across lines, disrupting downstream retrieval and chunking. We need a deterministic, zero-dependency algorithm that operates directly on positioned word bounding boxes.

## Decision

Implement the recursive XY-cut algorithm (Nagy & Seth 1984) prioritizing vertical cuts before horizontal cuts, capped at depth 32. Augment vertical cuts with table detection for 3+ aligned columns, heal line-break hyphens for lowercase continuations, and enforce strict input validation with typed errors.

## Consequences

Produces deterministic reading order for multi-column documents and aligned tables. Rotated text and right-to-left scripts remain out of scope as documented.
