import ast
import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
REPO=ROOT.parent
BOT=(ROOT/"bot_mention.py").read_text(encoding="utf-8")
INDEX=(REPO/"index.html").read_text(encoding="utf-8")

class WebStudioPublicTests(unittest.TestCase):
    def test_runtime_parses(self):
        ast.parse(BOT)
        self.assertIn("from collections import OrderedDict, defaultdict", BOT)

    def test_public_web_endpoint_is_isolated_and_rate_limited(self):
        self.assertIn('_WEB_STUDIO_DAILY_LIMIT = 1',BOT)
        self.assertIn('_WEB_STUDIO_ALLOWED_ORIGIN = "https://muba-rh.github.io"',BOT)
        self.assertIn('async def studio_web_generate_handler',BOT)
        self.assertIn('async def studio_web_options_handler',BOT)
        self.assertIn('app.router.add_post("/studio/web-generate", studio_web_generate_handler)',BOT)
        self.assertIn('app.router.add_options("/studio/web-generate", studio_web_options_handler)',BOT)
        self.assertIn('_web_studio_remaining(client_key)<=0',BOT)
        self.assertIn('_web_studio_consume(client_key)',BOT)

    def test_public_generation_reuses_protected_ai_credentials_server_side(self):
        self.assertIn('headers={"Authorization":"Bearer "+os.environ["CLOUDFLARE_API_TOKEN"]}',BOT)
        self.assertNotIn('CLOUDFLARE_API_TOKEN',INDEX)
        self.assertNotIn('TELEGRAM_BOT_TOKEN',INDEX)

    def test_telegram_studio_remains_available(self):
        self.assertIn('app.router.add_post("/studio/generate", studio_generate_handler)',BOT)
        self.assertIn('https://t.me/MUBA_RH_AI_Bot?start=assistant',INDEX)

    def test_web_ui_has_same_page_generation_and_result_controls(self):
        for marker in (
            'id="create-web"',
            'id="studio-result-img"',
            'id="download-image"',
            'id="use-twt"',
            'id="create-another"',
            '"/studio/web-generate"',
        ):
            self.assertIn(marker,INDEX)
        self.assertIn('meta name="muba-studio-api"',INDEX)
        self.assertIn('$MUBA #MUBA 🪶',INDEX)

if __name__=="__main__":
    unittest.main(verbosity=2)
