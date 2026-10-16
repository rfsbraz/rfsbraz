import unittest

import update_stats as u

README = (
    "- **deleterr** cleans up. <!-- stat:deleterr-stars -->342<!-- /stat --> stars, "
    "about <!-- stat:deleterr-pulls -->29,700<!-- /stat --> Docker Hub pulls.\n"
    "- **telegram-downloader** About <!-- stat:telegram-downloader-pulls -->16,500<!-- /stat --> pulls.\n"
)


class UpdateStats(unittest.TestCase):
    def test_formats_match_the_readme(self):
        self.assertEqual(u.format_value("deleterr-stars", 342), "342")
        self.assertEqual(u.format_value("deleterr-stars", 1234), "1,234")
        self.assertEqual(u.format_value("deleterr-pulls", 29743), "29,700")
        self.assertEqual(u.format_value("deleterr-pulls", 29799), "29,700")
        self.assertEqual(u.format_value("telegram-downloader-pulls", 16591), "16,500")

    def test_small_changes_do_not_touch_the_text(self):
        values = {"deleterr-stars": 342, "deleterr-pulls": 29743, "telegram-downloader-pulls": 16591}
        new, _ = u.update(README, lambda key: values[key])
        self.assertEqual(new, README)

    def test_changed_values_replace_only_the_number(self):
        values = {"deleterr-stars": 350, "deleterr-pulls": 30012, "telegram-downloader-pulls": 16591}
        new, _ = u.update(README, lambda key: values[key])
        self.assertIn("<!-- stat:deleterr-stars -->350<!-- /stat --> stars", new)
        self.assertIn("about <!-- stat:deleterr-pulls -->30,000<!-- /stat --> Docker", new)
        self.assertIn("<!-- stat:telegram-downloader-pulls -->16,500<!-- /stat -->", new)

    def test_failed_fetch_keeps_the_existing_value(self):
        def fetch(key):
            if key == "deleterr-pulls":
                raise OSError("network down")
            return {"deleterr-stars": 351, "telegram-downloader-pulls": 16591}[key]

        new, rows = u.update(README, fetch)
        self.assertIn("<!-- stat:deleterr-pulls -->29,700<!-- /stat -->", new)
        self.assertIn("<!-- stat:deleterr-stars -->351<!-- /stat -->", new)
        self.assertIn(("deleterr-pulls", "29,700", None, "29,700"), rows)

    def test_bad_values_count_as_failures(self):
        for bad in (0, None, -5, "342"):
            new, _ = u.update(README, lambda key: bad)
            self.assertEqual(new, README)

    def test_only_markers_in_the_readme_are_fetched(self):
        asked = []
        u.update("<!-- stat:deleterr-stars -->342<!-- /stat -->", lambda key: asked.append(key) or 342)
        self.assertEqual(asked, ["deleterr-stars"])

    def test_unknown_marker_is_left_alone(self):
        text = "<!-- stat:mystery -->7<!-- /stat -->"
        new, _ = u.update(text, lambda key: 99)
        self.assertEqual(new, text)


if __name__ == "__main__":
    unittest.main()
