import ast, pathlib, unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
SRC=(ROOT/"dev_mtproto_translator.py").read_text(encoding="utf-8")

class DevMtprotoTranslatorTests(unittest.TestCase):
    def test_isolated_from_bot_runtime(self):
        self.assertNotIn("bot_mention",SRC)
        self.assertIn("MUBA_DEV_SESSION",SRC)
    def test_uses_telegram_user_translation(self):
        self.assertIn("TranslateTextRequest",SRC)
        self.assertIn('to_lang="en"',SRC)
    def test_official_channel_is_required_and_numeric(self):
        self.assertIn("MUBA_OFFICIAL_CHANNEL_ID",SRC)
        self.assertIn("return int(raw)",SRC)
    def test_destination_is_resolved_then_allowlisted(self):
        self.assertIn("entity=await client.get_entity(peer)",SRC)
        self.assertIn("utils.get_peer_id(entity)",SRC)
        self.assertIn("resolved_id != _official_channel_id()",SRC)
        self.assertIn("BLOCKED: destination is not the official MUBA channel",SRC)
    def test_send_and_chat_both_enforce_official_channel(self):
        self.assertGreaterEqual(SRC.count("await _official_channel(client,peer)"),2)
        self.assertNotIn("client.send_message(peer,translated)",SRC)
        self.assertIn("client.send_message(entity,translated)",SRC)
    def test_local_secret_file_fallback(self):
        self.assertIn("~/muba_dev_session.secret",SRC)
    def test_no_secret_or_channel_literals(self):
        self.assertNotIn('api_hash = "',SRC.lower())
        self.assertNotIn("934598759",SRC)
        self.assertNotIn("-1004485415245",SRC)
    def test_parses(self):
        ast.parse(SRC)

if __name__=="__main__":
    unittest.main()
