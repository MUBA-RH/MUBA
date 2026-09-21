from __future__ import annotations
import pathlib
import unittest

REPO=pathlib.Path(__file__).resolve().parents[2]
WORKFLOW=(REPO/".github/workflows/muba-vault-auto-sync.yml").read_text(encoding="utf-8")
HISTORY=(REPO/"muba_history.json").read_text(encoding="utf-8")

class VaultAutoSyncSafetyTests(unittest.TestCase):
    def test_runs_from_main_and_validates_before_sync(self):
        self.assertIn("branches:\n      - main",WORKFLOW)
        telegram=WORKFLOW.index("Run Telegram regression suite")
        web=WORKFLOW.index("Validate public website")
        history=WORKFLOW.index("Validate canonical MUBA history schema")
        sync=WORKFLOW.index("Synchronize stable main into passive Vault")
        self.assertLess(telegram,sync)
        self.assertLess(web,sync)
        self.assertLess(history,sync)

    def test_preserves_vault_only_content(self):
        self.assertIn("--exclude 'MUBA_SYSTEM_VAULT/'",WORKFLOW)
        self.assertIn("--exclude '.github/workflows/export-muba-full-vault.yml'",WORKFLOW)

    def test_never_writes_back_to_production_or_activates_v2(self):
        self.assertIn('"production_writeback":False',WORKFLOW)
        self.assertIn('"v2_auto_activation":False',WORKFLOW)
        self.assertIn("git push origin HEAD:vault/system-vault-final",WORKFLOW)
        self.assertNotIn("git push origin HEAD:main",WORKFLOW)

    def test_exports_zip_and_checksum_in_same_workflow(self):
        self.assertIn('zip -qr "$archive" "$root"',WORKFLOW)
        self.assertIn('sha256sum "$archive" > "$checksum"',WORKFLOW)
        self.assertIn("actions/upload-artifact@v4",WORKFLOW)

    def test_history_records_automation(self):
        self.assertIn('"20260921-vault-auto-sync"',HISTORY)

if __name__=="__main__":
    unittest.main(verbosity=2)
