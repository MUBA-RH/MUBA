#!/usr/bin/env python3
"""Fail-closed permission gate for protected MUBA Vault reuse.

This gate is intentionally standard-library only. It does not store a secret.
An authorization file is accepted only when its canonical SHA-256 fingerprint
is present as an active grant in the official MUBA authorization registry.

The mechanism is an operational/audit control. It does not make public source
tamper-proof and it does not replace the repository license.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = REPO_ROOT / "muba_authorizations.json"
REQUIRED_SCOPE = "create-new-project-from-architecture"
REQUIRED_ISSUER = "MUBA Developer"
DENIED_EXIT = 73


class PermissionDenied(ValueError):
    pass


def canonical_payload(grant: dict[str, Any]) -> bytes:
    return json.dumps(
        grant,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def fingerprint(grant: dict[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(canonical_payload(grant)).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PermissionDenied(f"Required file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PermissionDenied(f"Invalid JSON: {path}") from exc
    if not isinstance(value, dict):
        raise PermissionDenied(f"Expected a JSON object: {path}")
    return value


def validate_grant_shape(grant: dict[str, Any]) -> None:
    required = {
        "schema_version",
        "grant_id",
        "project_name",
        "grantee",
        "scope",
        "issued_at",
        "expires_at",
        "issuer",
        "approval_reference",
    }
    missing = sorted(required - set(grant))
    if missing:
        raise PermissionDenied("Permission grant is incomplete: " + ", ".join(missing))
    if grant.get("schema_version") != 1:
        raise PermissionDenied("Unsupported permission grant schema.")
    if grant.get("issuer") != REQUIRED_ISSUER:
        raise PermissionDenied("Permission issuer is not the canonical MUBA issuer.")
    scope = grant.get("scope")
    if not isinstance(scope, list) or REQUIRED_SCOPE not in scope:
        raise PermissionDenied("Permission does not include the protected new-project scope.")
    for key in ("grant_id", "project_name", "grantee", "issued_at", "approval_reference"):
        if not isinstance(grant.get(key), str) or not grant[key].strip():
            raise PermissionDenied(f"Permission field must be non-empty: {key}")
    try:
        issued = date.fromisoformat(grant["issued_at"])
    except ValueError as exc:
        raise PermissionDenied("issued_at must use YYYY-MM-DD.") from exc
    if issued > date.today():
        raise PermissionDenied("Permission grant has a future issue date.")
    expires = grant.get("expires_at")
    if expires is not None:
        if not isinstance(expires, str):
            raise PermissionDenied("expires_at must be null or YYYY-MM-DD.")
        try:
            expiry = date.fromisoformat(expires)
        except ValueError as exc:
            raise PermissionDenied("expires_at must use YYYY-MM-DD.") from exc
        if expiry < date.today():
            raise PermissionDenied("Permission grant has expired.")


def validate_registry(registry: dict[str, Any]) -> None:
    if registry.get("schema_version") != 1:
        raise PermissionDenied("Unsupported authorization registry schema.")
    if registry.get("policy") != "permission-required":
        raise PermissionDenied("Authorization registry policy is not permission-required.")
    if registry.get("default_decision") != "deny":
        raise PermissionDenied("Authorization registry must be deny-by-default.")
    if registry.get("official_repository") != "MUBA-RH/MUBA":
        raise PermissionDenied("Authorization registry is not bound to the official MUBA repository.")
    if registry.get("issuer") != REQUIRED_ISSUER:
        raise PermissionDenied("Authorization registry issuer mismatch.")
    if registry.get("protected_scope") != REQUIRED_SCOPE:
        raise PermissionDenied("Authorization registry protected scope mismatch.")
    if not isinstance(registry.get("authorized_grants"), list):
        raise PermissionDenied("Authorization registry grants must be a list.")


def verify_permission(permission_path: Path, registry_path: Path = DEFAULT_REGISTRY) -> dict[str, Any]:
    grant = load_json(permission_path)
    registry = load_json(registry_path)
    validate_grant_shape(grant)
    validate_registry(registry)

    digest = fingerprint(grant)
    grant_id = grant["grant_id"]

    for record in registry["authorized_grants"]:
        if not isinstance(record, dict):
            continue
        if record.get("grant_id") != grant_id:
            continue
        if record.get("status") != "active":
            raise PermissionDenied("Permission grant exists but is not active.")
        if record.get("fingerprint") != digest:
            raise PermissionDenied("Permission file does not match the approved SHA-256 fingerprint.")
        return {
            "authorized": True,
            "grant_id": grant_id,
            "project_name": grant["project_name"],
            "grantee": grant["grantee"],
            "scope": REQUIRED_SCOPE,
            "fingerprint": digest,
        }

    raise PermissionDenied(
        "No active approval for this permission grant exists in the official MUBA authorization registry."
    )


def deny(message: str) -> int:
    print("MUBA VAULT — PERMISSION REQUIRED", file=sys.stderr)
    print(message, file=sys.stderr)
    print(
        "Installation stopped. Prior written authorization from the MUBA Developer is required.",
        file=sys.stderr,
    )
    return DENIED_EXIT


def cmd_verify(args: argparse.Namespace) -> int:
    if not args.permission:
        return deny("No MUBA permission file was supplied.")
    try:
        result = verify_permission(Path(args.permission), Path(args.registry))
    except PermissionDenied as exc:
        return deny(str(exc))
    print("MUBA VAULT — AUTHORIZATION VERIFIED")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_fingerprint(args: argparse.Namespace) -> int:
    try:
        grant = load_json(Path(args.permission))
        validate_grant_shape(grant)
    except PermissionDenied as exc:
        return deny(str(exc))
    print(fingerprint(grant))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify explicit MUBA authorization before protected Vault reuse."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    verify = sub.add_parser("verify", help="Verify permission and fail closed when it is absent or unapproved.")
    verify.add_argument("--permission", help="Path to an approved MUBA_PERMISSION.json file.")
    verify.add_argument("--registry", default=str(DEFAULT_REGISTRY), help="Authorization registry path.")
    verify.set_defaults(func=cmd_verify)

    fp = sub.add_parser("fingerprint", help="Print the canonical SHA-256 fingerprint of a permission file.")
    fp.add_argument("--permission", required=True, help="Path to a permission JSON file.")
    fp.set_defaults(func=cmd_fingerprint)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
