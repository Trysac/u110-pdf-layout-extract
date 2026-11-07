# Architecture

`pdf_layout_extract` implements a recursive XY-cut layout analysis algorithm for reconstructing reading order from positioned words without external PDF parsing dependencies.

## Pipeline

1. **Input Normalization & Validation**:
   `words_from_dicts` or direct instantiation of `Word` validates coordinate finiteness, ordering ($x_1 \ge x_0$, $\text{bottom} \ge \text{top}$), and non-empty text strings.

2. **Recursive XY-cut Decomposition**:
   - **Vertical Cut First**: Words are projected onto the horizontal axis ($x$-intervals). Empty gaps $\ge \text{column\_gap}$ partition words into left-to-right columns.
   - **Table Detection Rule**: If a vertical cut produces 3 or more children, all of which are leaf nodes having the same number of lines ($\\ge 2$) with matching line tops within $2.0\,\text{pt}$, the partition is constructed as a structured `table` block.
   - **Horizontal Cut Second**: When no vertical cut applies, empty vertical gaps $\ge \text{row\_gap}$ (defaulting to median word height) partition words from top to bottom.
   - **Leaf Nodes & Paragraph Formation**: When neither cut applies or `max_depth` (default 32) is reached, words are clustered into lines based on vertical center overlap, sorted horizontally, and processed for hyphen continuation joins.

3. **Deterministic Rendering**:
   `to_text` joins paragraphs with newlines, table cells with ` | `, blocks with `\n\n`, and pages with `\n\f\n`.
