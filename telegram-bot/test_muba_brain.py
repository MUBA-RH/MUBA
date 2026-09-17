"""Regression coverage for the local unified MUBA Brain."""

import importlib
import os
import tempfile
import unittest


_TEMP_DIR = tempfile.TemporaryDirectory()
os.environ["MUBA_MEMORY_FILE"] = os.path.join(_TEMP_DIR.name, "memory.json")
os.environ["MUBA_WEB_ENABLED"] = "0"
import muba_brain


class MubaBrainRegressionTests(unittest.TestCase):
    def setUp(self):
        global muba_brain
        muba_brain = importlib.reload(muba_brain)
        muba_brain.reset_social_state()

    def test_self_test_and_languages(self):
        result = muba_brain.master_self_test()
        self.assertTrue(result["ok"])
        self.assertEqual(result["version"], "MASTER-UNIFIED-2.0")
        self.assertEqual(
            tuple(muba_brain.get_master_brain_spec()["languages"]),
            ("tr", "en", "zh", "ar", "hi"),
        )

    def test_unauthorized_groups_are_silent_and_not_learned(self):
        before = len(muba_brain.STORE.data["learning_queue"])
        response = muba_brain.build_reply(
            "MUBA what is this?", chat_id=-1009999999999, user_id=101
        )
        self.assertEqual(response, "")
        self.assertEqual(len(muba_brain.STORE.data["learning_queue"]), before)

    def test_ca_is_never_invented(self):
        self.assertTrue(muba_brain.set_private_access(101, "approved", muba_brain.MASTER_FOUNDER_ID))
        response = muba_brain.build_reply(
            "What is the official CA or contract address?",
            chat_id=0,
            user_id=101,
        )
        self.assertIn("CA coming soon", response)
        self.assertNotIn("0x", response.lower())

    def test_unrelated_text_is_not_classified_as_knowledge(self):
        self.assertEqual(muba_brain.detect_intents("The train is late"), ["normal_chat"])
        response = muba_brain.build_reply("The train is late", chat_id=0, user_id=101)
        self.assertNotIn("MUBA is a character", response)

    def test_founder_and_protected_configuration_firewalls(self):
        founder = muba_brain.MASTER_FOUNDER_ID
        self.assertFalse(muba_brain.is_founder(founder + 1))
        self.assertFalse(muba_brain.founder_update("official_ca", "0xnot-real", founder))
        self.assertEqual(muba_brain.PROTECTED_CONFIG["official_ca"], "CA coming soon.")
        self.assertFalse(muba_brain.founder_update("source_map", {}, founder + 1))
        self.assertFalse(muba_brain.founder_update("source_map", {"docs": "https://example.invalid"}, founder))

    def test_protected_official_source_map_is_exact_and_immutable(self):
        expected = {
            "official_x": "https://x.com/MUBA_RH",
            "official_website": "https://muba-rh.github.io/MUBA/",
        }
        self.assertEqual(muba_brain.PROTECTED_OFFICIAL_SOURCES, expected)
        self.assertTrue(muba_brain._official_domain(expected["official_x"]))
        self.assertTrue(muba_brain._official_domain(expected["official_website"]))
        self.assertFalse(muba_brain._official_domain("https://x.com/not_muba_rh"))
        self.assertFalse(muba_brain._official_domain("https://muba.example/"))
        founder = muba_brain.MASTER_FOUNDER_ID
        self.assertFalse(muba_brain.register_official_source("other", "https://example.invalid", founder + 1))
        self.assertTrue(muba_brain.register_official_source("other", "https://example.invalid", founder))
        self.assertTrue(muba_brain._official_domain("https://example.invalid"))
        self.assertEqual(muba_brain.STORE.data["source_map"], expected)
        response = muba_brain.build_reply(
            "official Telegram?", muba_brain.MASTER_GROUP_ID, "en", 101
        )
        self.assertNotIn("Official Telegram", response)
        self.assertIn("@MUBA_RH", response)
        self.assertIn("https://muba-rh.github.io/MUBA/", response)

    def test_action_is_not_complete_until_verified(self):
        action_id = muba_brain.create_action(0, 101, "rose_handoff", {"message_id": 44})
        self.assertEqual(action_id, muba_brain.create_action(0, 101, "rose_handoff", {"message_id": 44}))
        actions = muba_brain.STORE.data["actions"]
        self.assertEqual(next(x for x in actions if x["action_id"] == action_id)["state"], "RECEIVED")
        self.assertTrue(muba_brain.update_action_state(action_id, "QUEUED", 101))
        self.assertEqual(next(x for x in actions if x["action_id"] == action_id)["state"], "QUEUED")
        self.assertTrue(muba_brain.verify_action_result(action_id, True, 101, {"rose": "confirmed"}))
        action = next(x for x in actions if x["action_id"] == action_id)
        self.assertEqual(action["state"], "ACTION_CONFIRMED")
        self.assertTrue(action["result"]["verified"])

    def test_user_memory_is_scoped_to_its_numeric_user_id(self):
        founder = muba_brain.MASTER_FOUNDER_ID
        self.assertTrue(muba_brain.set_private_access(101, "approved", founder))
        self.assertTrue(muba_brain.set_private_access(202, "approved", founder))
        self.assertTrue(muba_brain.remember_user_fact(101, "likes memes"))
        own = muba_brain.build_reply("What do you know about me?", chat_id=0, user_id=101)
        other = muba_brain.build_reply("What do you know about me?", chat_id=0, user_id=202)
        self.assertIn("likes memes", own)
        self.assertNotIn("likes memes", other)

    def test_private_access_requires_founder_approval(self):
        pending = muba_brain.build_reply("hello", chat_id=0, user_id=303)
        self.assertIn("Founder", pending)
        founder = muba_brain.MASTER_FOUNDER_ID
        self.assertTrue(muba_brain.set_private_access(303, "approved", founder))
        self.assertNotIn("approval", muba_brain.build_reply("hello", chat_id=0, user_id=303).lower())

    def test_recovery_point_rolls_back_only_with_founder_authority(self):
        founder = muba_brain.MASTER_FOUNDER_ID
        point = muba_brain.create_recovery_point("test", founder)
        self.assertFalse(muba_brain.rollback_recovery_point(point, founder + 1))
        self.assertTrue(muba_brain.rollback_recovery_point(point, founder))

    def test_group_and_topic_memory_are_authorized_and_scoped(self):
        group = muba_brain.MASTER_GROUP_ID
        other_group = -1009999999999
        self.assertTrue(muba_brain.remember_group_fact(group, "inside joke"))
        self.assertFalse(muba_brain.remember_group_fact(other_group, "leak"))
        self.assertIn("inside joke", str(muba_brain.STORE.data["groups"][str(group)]))
        self.assertNotIn(str(other_group), muba_brain.STORE.data["groups"])
        observed = muba_brain.observe_message(group, 101, "What is MUBA?", "en")
        self.assertTrue(observed["accepted"])
        self.assertEqual(observed["topic"], "what_is_muba")

    def test_denied_and_revoked_private_access_remain_blocked(self):
        founder = muba_brain.MASTER_FOUNDER_ID
        self.assertTrue(muba_brain.set_private_access(404, "denied", founder))
        self.assertIn("not approved", muba_brain.build_reply("hello", 0, "en", 404))
        self.assertTrue(muba_brain.set_private_access(404, "revoked", founder))
        self.assertIn("revoked", muba_brain.build_reply("hello", 0, "en", 404))

    def test_social_cooldown_results_in_silence(self):
        group = muba_brain.MASTER_GROUP_ID
        muba_brain.reset_social_state(group, 505)
        self.assertTrue(muba_brain.build_reply("hello", group, "en", 505))
        self.assertEqual(muba_brain.build_reply("hello", group, "en", 505), "")

    def test_learning_stays_candidate_without_founder(self):
        learning_id = muba_brain.queue_master_learning(
            muba_brain.MASTER_GROUP_ID, 606, "community says so", "user_claim", 0.2
        )
        item = next(x for x in muba_brain.STORE.data["learning_queue"] if x["learning_id"] == learning_id)
        self.assertEqual(item["stage"], "candidate")
        self.assertFalse(muba_brain.mature_learning(learning_id, "official", 606))
        self.assertTrue(muba_brain.mature_learning(learning_id, "official", muba_brain.MASTER_FOUNDER_ID))

    def test_source_conflicts_preserve_records_and_priority(self):
        records = [
            {"source": "user_claim", "confidence": 0.99, "value": "claim"},
            {"source": "official_muba", "confidence": 0.8, "value": "official"},
        ]
        ranked = muba_brain.compare_sources(records)
        self.assertEqual([x["value"] for x in ranked], ["official", "claim"])
        self.assertEqual(len(records), 2)
        metadata = muba_brain.provenance(
            "official_muba", 0.8, status="verified", source_type="official",
            authority="founder", evidence=["official source"], version=2,
        )
        for key in ("source", "source_type", "provenance", "confidence", "timestamp",
                    "created_at", "updated_at", "version", "status", "authority",
                    "evidence", "archive_state"):
            self.assertIn(key, metadata)

    def test_web_is_disabled_and_external_results_are_not_official(self):
        self.assertFalse(muba_brain.WEB_ENABLED)
        result = muba_brain.research_current("latest MUBA status")
        self.assertFalse(result["ok"])
        self.assertEqual(result["sources"], [])
        self.assertIn("disabled", result["summary"].lower())

    def test_multilingual_security_rules_create_evidence(self):
        group = muba_brain.MASTER_GROUP_ID
        cases = [
            ("fake CA 0x123", "en"),
            ("sahte CA 0x123", "tr"),
            ("fake CA 0x123", "zh"),
            ("CA مزيف 0x123", "ar"),
            ("fake CA 0x123", "hi"),
        ]
        for text, language in cases:
            response = muba_brain.build_reply(text, group, language, 707)
            self.assertIn("CA coming soon", response)
        incident = muba_brain.STORE.data["security_incidents"][-1]
        self.assertTrue(incident["evidence"])
        self.assertIn(incident["risk"], muba_brain.RISK_LEVELS)


if __name__ == "__main__":
    unittest.main()
