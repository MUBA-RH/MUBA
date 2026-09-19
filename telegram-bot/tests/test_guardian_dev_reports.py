import ast,pathlib,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]

class GuardianDevReportWiring(unittest.TestCase):
 def test_private_reporter_is_wired_to_security_actions(self):
  s=(ROOT/"bot_mention.py").read_text()
  tree=ast.parse(s)
  names={n.name for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
  self.assertIn("_guardian_dev_report",names)
  self.assertIn("chat_id=DEV_ID",s)
  self.assertGreaterEqual(s.count("await _guardian_dev_report(context,guardian_event,user_id)"),3)

 def test_report_failure_is_best_effort(self):
  s=(ROOT/"bot_mention.py").read_text()
  self.assertIn('logger.exception("Guardian DEV private report failed")',s)
  self.assertIn("from guardian import DEV_ID",s)\n\n def test_report_labels_are_turkish(self):\n  s=(ROOT/"bot_mention.py").read_text()\n  for label in ("MUBA GUARDIAN — DEV RAPORU","Olay:","İşlem:","Kullanıcı ID:","İhlal sayısı:"):\n   self.assertIn(label,s)

if __name__=="__main__": unittest.main()
