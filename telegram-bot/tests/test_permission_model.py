from __future__ import annotations

import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

REPO=pathlib.Path(__file__).resolve().parents[2]
GATE_PATH=REPO/"scripts"/"muba_permission_gate.py"
REGISTRY_PATH=REPO/"muba_authorizations.json"
LICENSE_PATH=REPO/"LICENSE.md"

spec=importlib.util.spec_from_file_location("muba_permission_gate",GATE_PATH)
gate=importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(gate)


class MubaPermissionModelTests(unittest.TestCase):
    def test_repository_is_deny_by_default(self):
        registry=json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        self.assertEqual(registry["policy"],"permission-required")
        self.assertEqual(registry["default_decision"],"deny")
        self.assertEqual(registry["official_repository"],"MUBA-RH/MUBA")
        self.assertEqual(registry["authorized_grants"],[])

    def test_license_is_source_available_not_free_reuse(self):
        text=LICENSE_PATH.read_text(encoding="utf-8")
        self.assertIn("MUBA SOURCE-AVAILABLE LICENSE",text)
        self.assertIn("Public visibility does **not** mean",text)
        self.assertIn("prior written authorization",text)
        self.assertIn("create a new project from the MUBA System Vault",text)

    def test_cli_denies_when_permission_is_missing(self):
        result=subprocess.run(
            [sys.executable,str(GATE_PATH),"verify"],
            cwd=REPO,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode,gate.DENIED_EXIT)
        self.assertIn("PERMISSION REQUIRED",result.stderr)
        self.assertIn("Installation stopped",result.stderr)

    def _grant(self):
        return {
            "schema_version":1,
            "grant_id":"test-grant-001",
            "project_name":"AUTHORIZED-TEST-PROJECT",
            "grantee":"Authorized Test Grantee",
            "scope":["create-new-project-from-architecture"],
            "issued_at":"2026-09-21",
            "expires_at":None,
            "issuer":"MUBA Developer",
            "approval_reference":"TEST-ONLY-APPROVAL",
        }

    def test_exact_active_fingerprint_is_accepted(self):
        grant=self._grant()
        digest=gate.fingerprint(grant)
        registry={
            "schema_version":1,
            "policy":"permission-required",
            "default_decision":"deny",
            "official_repository":"MUBA-RH/MUBA",
            "issuer":"MUBA Developer",
            "protected_scope":"create-new-project-from-architecture",
            "authorized_grants":[
                {"grant_id":grant["grant_id"],"fingerprint":digest,"status":"active"}
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp)
            permission=root/"MUBA_PERMISSION.json"
            registry_path=root/"muba_authorizations.json"
            permission.write_text(json.dumps(grant),encoding="utf-8")
            registry_path.write_text(json.dumps(registry),encoding="utf-8")
            result=gate.verify_permission(permission,registry_path)
        self.assertTrue(result["authorized"])
        self.assertEqual(result["fingerprint"],digest)

    def test_modified_permission_is_rejected(self):
        grant=self._grant()
        digest=gate.fingerprint(grant)
        registry={
            "schema_version":1,
            "policy":"permission-required",
            "default_decision":"deny",
            "official_repository":"MUBA-RH/MUBA",
            "issuer":"MUBA Developer",
            "protected_scope":"create-new-project-from-architecture",
            "authorized_grants":[
                {"grant_id":grant["grant_id"],"fingerprint":digest,"status":"active"}
            ],
        }
        grant["project_name"]="UNAPPROVED-MODIFIED-PROJECT"
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp)
            permission=root/"MUBA_PERMISSION.json"
            registry_path=root/"muba_authorizations.json"
            permission.write_text(json.dumps(grant),encoding="utf-8")
            registry_path.write_text(json.dumps(registry),encoding="utf-8")
            with self.assertRaises(gate.PermissionDenied):
                gate.verify_permission(permission,registry_path)


if __name__=="__main__":
    unittest.main(verbosity=2)
