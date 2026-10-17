# Decision records

Architecture Decision Records (ADRs) capture Raicho's notable design choices,
conventions, and trade-offs. The [working agreement](../contributing/working-agreement.md#durable-decisions)
defines why these are the durable project record.

## Conventions

- One file per decision, using the acceptance date and filename convention in
  [documentation organisation](../contributing/documentation-organisation.md#naming).
- Copy [template.md](template.md) to start a record.
- Accepted records are immutable except for their status. To change a decision,
  write a new ADR and mark the old one `superseded by YYYYMMDD-slug`.
- Keep context, decision, and consequences short and factual. Name the actual
  deciders and distinguish proposals from accepted decisions.

## Records

The dated files in this directory are the index. Use `ls docs/decisions/` to
find them. There is no hand-maintained list for every PR to append to.
