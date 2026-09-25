# Note format

One markdown file per note under `notes/`.

- The first line is the title, written as `# Title`.
- Everything after the first line is the body, rendered verbatim inside a
  `<pre>` block.
- The filename stem becomes the output slug: lowercased, with every run of
  non-alphanumeric characters collapsed to a single `-` (`notewall/slug.py`).

The renderer writes one `out/<slug>.html` per note and prints how many it wrote.
