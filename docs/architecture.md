# Architecture note

## Problem

A monthly close may produce two outputs from the same reviewed inputs:

1. an internal dossier with working notes and evidence;
2. a client dossier containing only explicitly releasable material.

An archive that merely exists is not enough. The system needs to prove its contents are complete, unchanged, and appropriate for its audience.

## Flow

```text
classified source files
        |
        v
path and size validation
        |
        v
canonical SHA-256 input fingerprint
        |
        +---- internal policy ----> internal archive
        |
        +---- client policy ------> client archive
                                      |
                                      v
                         embedded manifest + verifier
```

Source files are classified by directory: `public/` or `internal/`. A client build rejects internal content by policy; an internal build may contain both. Paths are normalized and symbolic links are rejected before data is read.

The input fingerprint is computed over canonical JSON describing each source path, classification, byte length, and digest. Changing an input changes the fingerprint, which allows a caller to mark an earlier dossier as stale.

The embedded manifest makes verification portable. A recipient can validate the archive without access to the build machine.

## Important invariant

The client boundary is enforced twice:

- during archive construction, where internal files are omitted;
- during verification, where an internal-classified member in a client archive is rejected.

This is intentional defense in depth rather than a user-interface convention.

## Deliberate trade-off

The ZIP timestamp is fixed and entries are sorted to make builds reproducible. That improves auditability but removes file modification times from the delivery artifact. If timestamps carry evidentiary value, they should be recorded as explicit signed metadata rather than inherited from the build filesystem.

## Production considerations not implemented here

- organization and role authorization;
- transactional persistence and concurrent generation;
- encryption, key management, and confidential storage;
- signed manifests or timestamp authority;
- malware scanning and format-specific document validation;
- billing, download receipts, retention, and legal-hold rules;
- deployment, monitoring, backup, and disaster recovery.

The sample is intentionally small enough to inspect in an interview while preserving the core integrity and disclosure ideas.
