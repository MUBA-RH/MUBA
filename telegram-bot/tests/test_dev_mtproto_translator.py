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
    def test_user_session_send(self):
        self.assertIn("client.send_message(peer,translated)",SRC)
    def test_chat_mode_removes_repeated_bot_prefix(self):
        self.assertIn("async def chat_mode(peer)",SRC)
        self.assertIn('argv[0]=="chat"',SRC)
        self.assertIn('await client.send_message(entity,translated)',SRC)
        self.assertIn("/quit",SRC)
    def test_local_secret_file_fallback(self):
        self.assertIn("~/muba_dev_session.secret",SRC)
    def test_no_secret_literals(self):
        self.assertNotIn('api_hash = "',SRC.lower())
        self.assertNotIn("934598759",SRC)
    def test_parses(self):
        ast.parse(SRC)

if __name__=="__main__":
    unittest.main()
