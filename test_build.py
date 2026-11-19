import copy
import json
import re
import tempfile
import unittest
from pathlib import Path

import build


class Orchive(unittest.TestCase):
    def setUp(self):
        self.good = build.load()

    def test_shipped_data_is_clean(self):
        self.assertEqual(build.validate(self.good), [])

    def test_page_carries_every_post(self):
        html = build.page(self.good)
        self.assertNotIn("__ORCHIVE_DATA__", html)
        for a in self.good:
            for t in a["tweets"]:
                self.assertIn(json.dumps(t, ensure_ascii=False), html)

    def _broken(self, change):
        bad = copy.deepcopy(self.good)
        change(bad)
        return build.validate(bad)

    def test_rejects_bad_archives(self):
        cases = {
            "long text": lambda b: b[0]["tweets"][0].update(text="A" * 281),
            "bad handle": lambda b: b[0]["account"].update(handle="Da Boss"),
            "twin handle": lambda b: b.append(copy.deepcopy(b[0])),
            "dangling reply": lambda b: b[0]["tweets"][0].update(reply_to="nobody/nuffink"),
            "negative likes": lambda b: b[0]["tweets"][0].update(likes=-1),
            "bad date": lambda b: b[0]["tweets"][0].update(at="yesterday"),
            "no tweets": lambda b: b[0].update(tweets=[]),
            "parody link elsewhere": lambda b: b[0]["tweets"][0].update(parody_of="https://evil.example/x.com/a/status/12345"),
            "parody link script": lambda b: b[0]["tweets"][0].update(parody_of="javascript:alert(1)"),
            "newline handle": lambda b: b[0]["account"].update(handle="grug\n"),
            "list reply": lambda b: b[0]["tweets"][0].update(reply_to=["x"]),
            "junk entries": lambda b: b.extend([None, {"account": "oi", "tweets": [1]}]),
            "nothing at all": lambda b: b.clear(),
        }
        for name, change in cases.items():
            self.assertTrue(self._broken(change), name)

    def test_site_has_the_data_files_and_every_app_page(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            build.write_site(self.good, out)
            posts = json.loads((out / "api" / "posts.json").read_text())
            self.assertEqual(len(posts), sum(len(a["tweets"]) for a in self.good))
            self.assertEqual(json.loads((out / "orchive.json").read_text()), self.good)
            for a in self.good:
                one = json.loads((out / "api" / "gitz" / f"{a['account']['handle']}.json").read_text())
                self.assertEqual(one, a)
            for name in build.APPS:
                html = (out / f"{name}.html").read_text()
                self.assertIn(f'data-app="{name}"', html)
                self.assertIn(f"  {name}(", html, f"apps.html has no code for {name}")
                self.assertNotIn("__", html)
            for link in re.findall(r'<li><a href="([a-z]+)"', (out / "index.html").read_text()):
                self.assertIn(link, build.APPS)

    def test_script_closer_cannot_end_the_data_block(self):
        bad = copy.deepcopy(self.good)
        bad[0]["tweets"][0]["text"] = "</script><b>oi"
        self.assertNotIn("</script><b>oi", build.page(bad))


if __name__ == "__main__":
    unittest.main()
