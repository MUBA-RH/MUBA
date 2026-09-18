from __future__ import annotations
import pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import guardian as g

class GuardianSecurityExam(unittest.TestCase):
 def setUp(self):
  g.reset_runtime_security_state(); g.set_lockdown(False)

 def test_existing_dev_command_gate_unchanged(self):
  self.assertEqual(g.authorized_command(g.GROUP_ID,g.DEV_ID,"#BAN"),"#BAN")
  self.assertIsNone(g.authorized_command(g.GROUP_ID,123,"#BAN"))
  self.assertIsNone(g.authorized_command(-1,g.DEV_ID,"#BAN"))
  self.assertTrue(g.is_control_attempt("#STATUS"))

 def test_only_three_official_links_allowed(self):
  allowed=["https://muba-rh.github.io/MUBA/","https://x.com/MUBA_RH","https://t.me/MUBA_RH"]
  for url in allowed:
   self.assertIsNone(g.inspect_message(g.GROUP_ID,101,url),url)
  blocked=["https://google.com","https://example.com/a","t.me/not_muba","x.com/other","muba-rh.github.io/OTHER"]
  for i,url in enumerate(blocked,200):
   e=g.inspect_message(g.GROUP_ID,i,url)
   self.assertEqual((e or {}).get("action"),"delete",url)

 def test_first_ca_mutes_second_same_id_bans(self):
  ca="0x"+"a"*40
  first=g.inspect_message(g.GROUP_ID,777,ca)
  second=g.inspect_message(g.GROUP_ID,777,ca)
  self.assertEqual(first["action"],"mute")
  self.assertEqual(first["strike"],1)
  self.assertEqual(second["action"],"ban")
  self.assertEqual(second["strike"],2)

 def test_strikes_are_bound_to_numeric_sender_id(self):
  ca="0x"+"b"*40
  self.assertEqual(g.inspect_message(g.GROUP_ID,11,ca)["action"],"mute")
  self.assertEqual(g.inspect_message(g.GROUP_ID,12,ca)["action"],"mute")
  self.assertEqual(g.inspect_message(g.GROUP_ID,11,ca)["action"],"ban")

 def test_dev_is_never_auto_moderated(self):
  ca="0x"+"c"*40
  self.assertIsNone(g.inspect_message(g.GROUP_ID,g.DEV_ID,ca))
  self.assertIsNone(g.inspect_message(g.GROUP_ID,g.DEV_ID,"https://evil.example"))

 def test_fake_ca_words_alone_warn_not_mute(self):
  e=g.inspect_message(g.GROUP_ID,55,"Beware of fake CA scams")
  self.assertEqual(e["action"],"warn")
  self.assertEqual(g.fake_ca_strikes(55),0)

 def test_existing_flood_detection_remains(self):
  event=None
  for i in range(7): event=g.inspect_message(g.GROUP_ID,88,"hello",now=100+i)
  self.assertEqual((event or {}).get("kind"),"flood")

if __name__=="__main__": unittest.main(verbosity=2)
