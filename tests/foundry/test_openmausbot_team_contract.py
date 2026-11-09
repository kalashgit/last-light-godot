import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "docs/production/foundry-ai-last-light.mausteam.json"

class OpenMausBotTeamContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(PACKAGE.read_text())

    def test_format_v1(self):
        self.assertEqual(self.doc["format"], "openmaus.team")
        self.assertEqual(self.doc["version"], 1)
        self.assertEqual(set(self.doc), {"format", "version", "team"})

    def test_members_are_unique_and_valid(self):
        members = self.doc["team"]["members"]
        keys = [m["key"] for m in members]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertGreaterEqual(len(members), 5)
        for member in members:
            self.assertRegex(member["key"], r"^[a-z0-9][a-z0-9_-]*$")
            self.assertEqual(set(member), {"key", "name", "title", "description", "appearance"})
            self.assertIn(member["appearance"]["color"], ("green","blue","red","orange","purple","cyan","pink","yellow","teal","coral"))
            self.assertLessEqual(len(member["description"]), 4000)

    def test_room_links_to_existing_director(self):
        room = self.doc["team"]["room"]
        self.assertEqual(room["defaultResponder"]["kind"], "member")
        keys = {m["key"] for m in self.doc["team"]["members"]}
        self.assertIn(room["defaultResponder"]["member"], keys)

    def test_no_credentials_or_autonomous_permission_fields(self):
        content = PACKAGE.read_text().lower()
        for forbidden in ('"api_key"', '"token"', '"secret"', '"access_token"', '"password"', '"automatically_merge"', '"fullaccess"'):
            self.assertNotIn(forbidden, content)
        self.assertNotIn("routines", self.doc["team"])

if __name__ == "__main__":
    unittest.main()
