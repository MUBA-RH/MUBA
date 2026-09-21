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

 def test_dev_management_success_does_not_private_report(self):
  s=(ROOT/"bot_mention.py").read_text()
  self.assertNotIn('{"kind":"management","subkind":cmd.lstrip("#").casefold()',s)
  self.assertNotIn('{"kind":"management","subkind":"help"',s)
  self.assertNotIn('{"kind":"management","subkind":"security"',s)
  self.assertNotIn('{"kind":"management","subkind":"lockdown"',s)
  self.assertNotIn('{"kind":"management","subkind":"normal"',s)
  self.assertIn('"kind":"runtime"',s)
  self.assertIn('"kind":"unauthorized_control"',s)

 def test_report_failure_is_best_effort(self):
  s=(ROOT/"bot_mention.py").read_text()
  self.assertIn('logger.exception("Guardian DEV private report failed")',s)
  self.assertIn("from guardian import DEV_ID",s)

 def test_five_language_dev_report_selector(self):
  s=(ROOT/"bot_mention.py").read_text()
  for lang in ("en","tr","zh","ar","hi"):
   self.assertIn('"'+lang+'":{',s)
  self.assertIn("guardian_report_language_keyboard",s)
  self.assertIn('callback_data=f"guardian_lang:{code}"',s)
  self.assertIn('data.startswith("guardian_lang:")',s)
  self.assertIn("if not is_dev(user_id): return",s)

 def test_dev_report_locale_is_not_hardcoded_to_turkish(self):
  s=(ROOT/"bot_mention.py").read_text()
  self.assertNotIn("kind_tr=",s)
  self.assertNotIn("subkind_tr=",s)
  self.assertNotIn("action_tr=",s)
  self.assertIn("get_guardian_report_language",s)
  self.assertIn("set_guardian_report_language",s)
  self.assertIn('GUARDIAN_EVENT_LABELS[lang]',s)

 def test_guardian_violation_history_and_user_identity_are_wired(self):
  s=(ROOT/"bot_mention.py").read_text()
  self.assertIn("append_guardian_violation",s)
  self.assertIn("guardian_violation_history",s)
  self.assertIn('callback_data="guardian_history"',s)
  self.assertIn('callback_data=f"guardian_history:{key}:0"',s)
  self.assertIn('user_name=("@"+tg_user.username)',s)
  self.assertIn("GROUP_ID,user_id",s)
 def test_language_prompt_is_deduplicated(self):
  s=(ROOT/"bot_mention.py").read_text()
  self.assertIn("_GUARDIAN_REPORT_LANGUAGE_PROMPTED",s)
  self.assertIn("if not _GUARDIAN_REPORT_LANGUAGE_PROMPTED:",s)
 def test_guardian_has_telegram_native_command_fallback(self):
  s=(ROOT/"bot_mention.py").read_text()
  self.assertIn("async def guardian_slash_command",s)
  self.assertIn('mapped="#"+name',s)
  self.assertIn('CommandHandler(guardian_name, guardian_slash_command)',s)
  self.assertIn('"status","guardian","security","lockdown","normal"',s)

if __name__=="__main__": unittest.main()
