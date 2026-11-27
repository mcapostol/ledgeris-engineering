# Ledgeris Engineering Showcase

A public, runnable engineering sample for **Ledgeris**, a financial-close workflow product designed by Cristian Marius Apostol. It contains one small reviewed excerpt from the actual product source and one clean-room demonstrator of a broader workflow pattern.

Ledgeris uses Django for the application, openpyxl for spreadsheets and ReportLab for PDF generation. The private product supports balance imports, monthly controls, reconciliations, inventory and management reporting, role-scoped workspaces, and persistent internal/client closing dossiers. This repository focuses on **building reproducible delivery archives and verifying their contents against an embedded manifest**. A checksum detects inconsistency; it is not a signature and cannot authenticate a maliciously replaced manifest.

## Actual Ledgeris source excerpt

`ledgeris_source_excerpt/romanian_numbers.py` contains the product's deterministic numeric parser and Romanian display formatter. The two functions are copied verbatim from the private repository's `accounting/reports.py`; only the required standard-library imports and shared zero constant accompany them. The package-level `format_romanian_number` alias is specific to this public showcase.

The excerpt demonstrates several practical boundary decisions:

- represent monetary input with `Decimal`, without leaking a float's binary expansion;
- accept both ordinary decimal strings and Romanian-formatted input;
- handle parenthesized negative values used in financial documents;
- produce stable Romanian thousands and decimal separators;
- reject malformed values explicitly instead of silently coercing them.

It is intentionally small: no customer data, accounting classifications, report templates, authentication, billing, or production configuration is included.

## Clean-room dossier demonstrator

The separate `ledgeris_dossier_demo` package is a reconstructed public sample, not production source. It demonstrates:

- deterministic ZIP generation from synthetic source documents;
- separate `internal` and `client` disclosure scopes;
- SHA-256 for every included file;
- one canonical input fingerprint for stale-package detection;
- a machine-readable manifest embedded in every archive;
- verification that rejects modified, duplicated, unsafe, or wrongly scoped entries;
- targeted tests for disclosure boundaries and integrity failures.

This is useful whenever a workflow must prove which exact inputs produced a client delivery without exposing internal working papers.

## Run it

Python 3.11+ is sufficient; the demonstration has no third-party dependencies.

```bash
python -m ledgeris_dossier_demo build \
  --source fixtures/monthly-close \
  --audience client \
  --output build/client-dossier.zip

python -m ledgeris_dossier_demo verify build/client-dossier.zip
python -m unittest discover -s tests -v
```

Build an internal dossier by replacing `--audience client` with `--audience internal`.

## Repository map

```text
ledgeris_dossier_demo/   Standard-library implementation and CLI
ledgeris_source_excerpt/ Reviewed excerpt from actual Ledgeris source
fixtures/monthly-close/  Synthetic input documents only
tests/                   Integrity and disclosure-boundary tests
docs/architecture.md     Design, threat boundaries, and trade-offs
```

## Product context

The production system is a private multi-workflow application. Its broader architecture includes a server-rendered web application, persistence, spreadsheet/PDF generation, containerized deployment, organization-scoped authorization, external identity, billing integration, and controlled release operations. Those implementation details, customer data, credentials, and production source are intentionally excluded here.

## Scope and authorship

Cristian Marius Apostol is the product owner and solution architect behind Ledgeris. The numeric utility is a reviewed source excerpt identified above. The dossier package is a **clean-room public demonstrator**, not a production source-code export. Neither component is a claim that this compact repository is the complete product.

All fixtures are fictional. Do not use this sample as accounting advice or as a substitute for an accountant's review.

