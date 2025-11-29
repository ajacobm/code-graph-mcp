# Documentation Location and Canonicalization

This file records the canonical location for human-facing documentation for the CodeNavigator (codenav) project and the detection/fallback rules used by the Documentation Agent.

Detection order (first match wins):

1. GitHub Pages
   - Use if repository has Pages enabled (docs/ or gh-pages branch or pages config in repo settings).
2. Repository Wiki
   - Use if Pages is not available and the project uses the Wiki as the primary docs location.
3. In-repo Markdown
   - Default fallback: /docs/, PLANNING.md, README.md, and /docs/sessions/

If the Documentation Agent chooses a canonical location it must record that choice and the rationale here. When multiple locations are used (site + in-repo snippets + wiki), list the sync strategy and which content lives where.

Notes:
- To change the canonical location, edit this file and explain the migration plan and any required automation.
- Do not store secrets or credentials in documentation or session logs.

---