from __future__ import annotations
import pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import guardian as g

class GuardianRiskPolicyExam(unittest.TestCase):
 def setUp(self): g.reset_runtime_security_state(); g.set_lockdown(False)
 def e(self,uid,text): return g.inspect_message(g.GROUP_ID,uid,text,now=100)

 def test_other_token_conversation_is_not_punished(self):
  for text in ("ETH yükseldi","SOL aldım","PEPE hakkında ne düşünüyorsunuz?","Bitcoin ne olur?","Another token looks interesting"):
   self.assertIsNone(self.e(100,text),text)

 def test_discussing_scam_words_is_not_auto_punished(self):
  e=self.e(101,"Birisi bana connect wallet dedi, scam olabilir mi?")
  self.assertEqual((e or {}).get("action"),"warn")
  e=self.e(102,"Arkadaşlar fake CA paylaşanlara dikkat edin.")
  self.assertEqual((e or {}).get("action"),"warn")

 def test_external_link_without_high_risk_is_delete_only(self):
  e=self.e(103,"PEPE hakkında bakın https://example.com/token")
  self.assertEqual(e["action"],"delete")
  self.assertEqual(e["subkind"],"blocked_link")

 def test_wallet_lure_plus_external_link_escalates(self):
  text="Claim airdrop now, connect wallet https://evil.example/claim"
  self.assertEqual(self.e(104,text)["action"],"mute")
  self.assertEqual(self.e(104,text)["action"],"ban")

 def test_credential_request_escalates_without_link(self):
  text="Send me your seed phrase"
  self.assertEqual(self.e(105,text)["action"],"mute")
  self.assertEqual(self.e(105,text)["action"],"ban")

 def test_risk_strikes_are_per_numeric_sender(self):
  text="Claim reward and connect wallet https://evil.example"
  self.assertEqual(self.e(201,text)["action"],"mute")
  self.assertEqual(self.e(202,text)["action"],"mute")
  self.assertEqual(self.e(201,text)["action"],"ban")

 def test_existing_fake_ca_chain_remains_independent(self):
  ca="0x"+"d"*40
  self.assertEqual(self.e(301,ca)["action"],"mute")
  self.assertEqual(self.e(301,ca)["action"],"ban")

 def test_official_links_remain_allowed(self):
  for url in ("https://muba-rh.github.io/MUBA/","https://x.com/MUBA_RH","https://t.me/MUBA_RH"):
   self.assertIsNone(self.e(400,url))

if __name__=="__main__": unittest.main(verbosity=2)
