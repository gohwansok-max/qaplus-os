import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from blog_publish_rules import strip_internal_topic_code, validate_blog_post


class BlogPublishRulesTests(unittest.TestCase):
    def test_leading_file_code_is_removed(self):
        self.assertEqual(strip_internal_topic_code("MIC001-5_작업장 공기질 관리"), "작업장 공기질 관리")
        self.assertEqual(strip_internal_topic_code("ALL001 한국형 알레르겐 관리"), "한국형 알레르겐 관리")

    def test_standard_names_are_not_treated_as_file_codes(self):
        self.assertEqual(strip_internal_topic_code("FSSC22000 V7 변경사항"), "FSSC22000 V7 변경사항")
        self.assertEqual(strip_internal_topic_code("ISO22000 내부심사"), "ISO22000 내부심사")

    def test_internal_code_blocks_publish(self):
        with self.assertRaisesRegex(ValueError, "내부 파일 구분코드"):
            validate_blog_post("EQ003 리본블렌더", self.valid_html())

    def test_fewer_than_three_unique_images_blocks_publish(self):
        html = '<img src="https://example.com/a.png" alt="현장 사진"><img src="https://example.com/a.png" alt="점검 사진">'
        with self.assertRaisesRegex(ValueError, "3장 미만"):
            validate_blog_post("정상 제목", html)

    def test_three_unique_images_with_korean_alt_pass(self):
        result = validate_blog_post("정상 제목", self.valid_html())
        self.assertTrue(result["passed"])
        self.assertEqual(result["image_count"], 3)

    @staticmethod
    def valid_html():
        return "".join(
            f'<img src="https://example.com/{index}.png" alt="품질관리 현장 이미지 {index}">'
            for index in range(1, 4)
        )


if __name__ == "__main__":
    unittest.main()
