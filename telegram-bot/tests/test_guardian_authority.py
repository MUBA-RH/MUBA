from __future__ import annotations
import pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from guardian import authorized_command,is_control_attempt,is_guardian_group,is_dev,status_text,help_text

class GuardianAuthorityExam(unittest.TestCase):
 def test_scope_is_exact_main_group(self):
  self.assertTrue(is_guardian_group(-1004485415245))
  self.assertFalse(is_guardian_group(-1004485415244))
  self.assertFalse(is_guardian_group(12345))
 def test_only_dev_has_command_authority(self):
  self.assertEqual(authorized_command(-1004485415245,934598759,"#STOP"),"#STOP")
  self.assertIsNone(authorized_command(-1004485415245,111,"#STOP"))
  self.assertIsNone(authorized_command(-999,934598759,"#STOP"))
 def test_commands_are_exact(self):
  for cmd in ("#START","#STOP","#GUARDIAN","#STATUS","#HELP"):
   self.assertEqual(authorized_command(-1004485415245,934598759,cmd),cmd)
  self.assertIsNone(authorized_command(-1004485415245,934598759,"#DELETE"))
 def test_unknown_hash_command_is_control_attempt(self):
  self.assertTrue(is_control_attempt("#DELETE"))
  self.assertFalse(is_control_attempt("MUBA nedir?"))
 def test_status_and_help(self):
  self.assertIn("ACTIVE",status_text(False)); self.assertIn("PAUSED",status_text(True))
  self.assertIn("#START",help_text()); self.assertIn("#STOP",help_text())

if __name__=="__main__": unittest.main(verbosity=2)
