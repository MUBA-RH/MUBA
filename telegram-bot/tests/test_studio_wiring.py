import ast,pathlib,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
class StudioWiring(unittest.TestCase):
 def test_runtime_symbols_and_routes_exist(self):
  s=(ROOT/"bot_mention.py").read_text()
  tree=ast.parse(s); names={n.name for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
  for n in ("inline_studio","studio_page_handler","studio_generate_handler","studio_render_handler"): self.assertIn(n,names)
  self.assertIn('app.router.add_get("/studio"',s);self.assertIn('InlineQueryHandler(inline_studio)',s)
 def test_guardian_source_not_modified_by_studio_module(self):
  s=(ROOT/"muba_studio.py").read_text();self.assertNotIn("guardian",s.lower())
if __name__=="__main__":unittest.main()
