"""Command-line interface for the dossier demonstrator."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import DossierError, build_dossier, verify_dossier


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Build and verify immutable dossier archives")
    commands = root.add_subparsers(dest="command", required=True)

    build = commands.add_parser("build", help="build an audience-scoped dossier")
    build.add_argument("--source", type=Path, required=True)
    build.add_argument("--output", type=Path, required=True)
    build.add_argument("--audience", choices=("client", "internal"), required=True)

    verify = commands.add_parser("verify", help="verify a dossier manifest and contents")
    verify.add_argument("archive", type=Path)
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "build":
            result = build_dossier(args.source, args.output, args.audience)
        else:
            result = verify_dossier(args.archive)
    except DossierError as exc:
        print(json.dumps({"status": "FAILED", "error": str(exc)}))
        return 1
    print(
        json.dumps(
            {
                "status": "VERIFIED" if args.command == "verify" else "BUILT",
                "audience": result["audience"],
                "input_fingerprint": result["input_fingerprint"],
                "file_count": len(result["files"]),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
