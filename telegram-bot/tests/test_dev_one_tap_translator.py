from pathlib import Path

SRC=(Path(__file__).resolve().parents[1]/"bot_mention.py").read_text()

def test_dev_inline_translation_needs_no_tr_prefix():
    block=SRC[SRC.index("async def dev_inline_translator"):SRC.index("async def guardian_slash_command")]
    assert 'source=" ".join((query.query or "").strip().split())[:2000]' in block
    assert 'startswith("tr ")' not in block
    assert "not is_dev(query.from_user.id)" in block

def test_dev_queries_do_not_fall_through_to_studio():
    block=SRC[SRC.index("async def inline_studio"):SRC.index("async def studio_page_handler")]
    assert "if is_dev(q.from_user.id): return" in block

def test_translation_result_is_user_selected_inline_content():
    block=SRC[SRC.index("async def dev_inline_translator"):SRC.index("async def guardian_slash_command")]
    assert "InlineQueryResultArticle" in block
    assert "InputTextMessageContent(message_text=translated)" in block
    assert "await query.answer([result]" in block
