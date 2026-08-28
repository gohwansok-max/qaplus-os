import importlib.util
import datetime
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "generate_blog.py"
SPEC = importlib.util.spec_from_file_location("generate_blog", SCRIPT_PATH)
generate_blog = importlib.util.module_from_spec(SPEC)
with patch("zoneinfo.ZoneInfo", return_value=datetime.timezone.utc):
    SPEC.loader.exec_module(generate_blog)


class GenerateBlogEnvironmentTests(unittest.TestCase):
    def test_process_environment_is_available_and_overrides_dotenv(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            dotenv = Path(temp_dir) / ".env"
            dotenv.write_text(
                "CHEAPAI_API_KEY=dotenv-key\nCHEAPAI_BASE_URL=https://dotenv.invalid/v1\n",
                encoding="utf-8",
            )
            with patch.object(generate_blog, "ROOT_DIR", temp_dir), patch.dict(
                os.environ,
                {
                    "CHEAPAI_API_KEY": "github-secret-key",
                    "CHEAPAI_BASE_URL": "https://runtime.example/v1",
                },
                clear=False,
            ):
                env = generate_blog.load_env()

        self.assertEqual(env["CHEAPAI_API_KEY"], "github-secret-key")
        self.assertEqual(env["CHEAPAI_BASE_URL"], "https://runtime.example/v1")

    def test_missing_llm_credentials_fails_instead_of_succeeding_silently(self):
        with patch.object(generate_blog, "ENV", {}):
            with self.assertRaisesRegex(RuntimeError, "유효한 LLM API 키가 없습니다"):
                generate_blog.run_blog_pipeline("테스트 주제")


if __name__ == "__main__":
    unittest.main()
