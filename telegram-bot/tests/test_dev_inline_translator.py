import ast, pathlib, unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
SRC=(ROOT/"bot_mention.py").read_text(encoding="utf-8")

class DevInlineTranslatorTests(unittest.TestCase):
 def test_dev_only_and_prefix_gate_exist(self):
  self.assertIn("not is_dev(query.from_user.id)",SRC)
  self.assertIn('startswith("tr ")',SRC)
 def test_cloudflare_translation_model_isolated(self):
  self.assertIn("@cf/meta/m2m100-1.2b",SRC)
  self.assertIn('"source_lang":"tr"',SRC)
  self.assertIn('"target_lang":"en"',SRC)
 def test_existing_inline_studio_is_preserved(self):
  self.assertIn("async def inline_studio",SRC)
  self.assertIn("InlineQueryHandler(inline_studio)",SRC)
 def test_runtime_parses(self):
  ast.parse(SRC)

if __name__=="__main__":
 unittest.main()
