from __future__ import annotations
import pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from guardian import *

class GuardianAuthorityExam(unittest.TestCase):
 def setUp(self): set_lockdown(False)
 def test_scope_is_exact_main_group(self):
  self.assertTrue(is_guardian_group(-1004485415245)); self.assertFalse(is_guardian_group(-1)); self.assertFalse(is_guardian_group(123))
 def test_only_dev_has_command_authority(self):
  for cmd in COMMANDS:
   self.assertEqual(authorized_command(-1004485415245,934598759,cmd),cmd)
   self.assertIsNone(authorized_command(-1004485415245,111,cmd))
   self.assertIsNone(authorized_command(-999,934598759,cmd))
 def test_unknown_control_is_never_authorized(self):
  self.assertTrue(is_control_attempt("#DELETEALL")); self.assertIsNone(authorized_command(-1004485415245,934598759,"#DELETEALL"))
 def test_command_arguments(self):
  self.assertEqual(authorized_command(-1004485415245,934598759,"#UNBAN 123"),"#UNBAN")
  self.assertEqual(command_arg("#UNBAN 123"),"123")
 def test_status_modes(self):
  self.assertIn("ACTIVE",status_text(False)); self.assertIn("PAUSED",status_text(True))
  set_lockdown(True); self.assertIn("LOCKDOWN",status_text(False)); self.assertTrue(lockdown_enabled())
 def test_fake_ca_security(self):
  e=inspect_message(-1004485415245,10,"official ca 0x"+"a"*40,now=1); self.assertEqual(e["kind"],"security")
 def test_suspicious_link(self):
  e=inspect_message(-1004485415245,10,"connect wallet https://evil.example",now=1); self.assertEqual(e["kind"],"suspicious_link")
 def test_lockdown_link(self):
  set_lockdown(True); e=inspect_message(-1004485415245,10,"https://example.com",now=1); self.assertEqual(e["kind"],"suspicious_link")
 def test_flood(self):
  e=None
  for i in range(7): e=inspect_message(-1004485415245,77,"hello",now=100+i)
  self.assertEqual(e["kind"],"flood")
 def test_dev_is_not_passively_moderated(self):
  self.assertIsNone(inspect_message(-1004485415245,934598759,"connect wallet https://x.test",now=1))
 def test_other_groups_are_ignored(self):
  self.assertIsNone(inspect_message(-999,10,"official ca 0x"+"a"*40,now=1))
 def test_help_lists_controls(self):
  h=help_text()
  for cmd in COMMANDS: self.assertIn(cmd,h)

if __name__=="__main__": unittest.main(verbosity=2)
