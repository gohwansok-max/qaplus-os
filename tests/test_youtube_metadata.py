import importlib.util
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "youtube_uploader.py"
SPEC = importlib.util.spec_from_file_location("youtube_uploader", SCRIPT_PATH)
youtube_uploader = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(youtube_uploader)


class YouTubeMetadataTests(unittest.TestCase):
    def test_ccp_topic_uses_long_tail_search_intent(self):
        metadata = youtube_uploader.build_short_metadata(
            "HC004 가열살균 공정 CCP 한계기준 관리",
            [{"subtitle": "중심온도 기록과 이탈 시 격리 절차"}],
        )

        self.assertTrue(metadata["title"].startswith("[HACCP CCP 관리]"))
        self.assertIn("가열살균 공정 CCP 한계기준 관리", metadata["title"])
        self.assertIn("HACCP CCP 관리 정보를 찾는 실무자", metadata["description"])
        self.assertIn("중심온도 기록과 이탈 시 격리 절차", metadata["description"])
        self.assertIn("CCP관리", metadata["tags"])
        self.assertLessEqual(len(metadata["title"]), 100)
        self.assertLessEqual(len(",".join(metadata["tags"])), 450)

    def test_fssc_topic_removes_queue_id_and_repairs_spacing(self):
        metadata = youtube_uploader.build_short_metadata("FSC009 PRP OPRP CCP 구분과적용")

        self.assertEqual(metadata["primary_keyword"], "FSSC 22000 실무")
        self.assertNotIn("FSC009", metadata["title"])
        self.assertIn("구분과 적용", metadata["title"])
        self.assertIn("#HACCP #해썹 #식품품질관리 #Shorts", metadata["description"])

    def test_smart_haccp_topic_gets_specific_keyword(self):
        metadata = youtube_uploader.build_short_metadata("스마트HACCP 센서 연동 방법")

        self.assertEqual(metadata["primary_keyword"], "스마트 HACCP")
        self.assertTrue(metadata["title"].startswith("[스마트 HACCP]"))
        self.assertIn("스마트해썹", metadata["tags"])

    def test_long_topic_is_truncated_without_exceeding_youtube_limit(self):
        metadata = youtube_uploader.build_short_metadata("HACCP " + "현장 점검 " * 30)

        self.assertLessEqual(len(metadata["title"]), 100)
        self.assertTrue(metadata["title"].endswith("큐에이플러스"))


if __name__ == "__main__":
    unittest.main()
