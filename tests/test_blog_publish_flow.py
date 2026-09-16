import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import blogger_publisher
import telegram_poll_dispatch


class BlogPublishFlowTests(unittest.TestCase):
    def test_publish_draft_uses_blogger_publish_endpoint(self):
        response = mock.Mock(status_code=200)
        response.json.return_value = {"id": "123", "url": "https://example.blogspot.com/post", "title": "검토 완료 글"}
        with mock.patch.dict(os.environ, {"BLOGGER_BLOG_ID": "blog-9"}), \
             mock.patch.object(blogger_publisher, "get_access_token", return_value="token"), \
             mock.patch.object(blogger_publisher.requests, "post", return_value=response) as post:
            result = blogger_publisher.publish_draft("123")
        self.assertTrue(result["ok"])
        self.assertEqual(post.call_args.args[0], "https://www.googleapis.com/blogger/v3/blogs/blog-9/posts/123/publish")

    def test_authorized_telegram_button_publishes_selected_draft(self):
        callback = {
            "id": "callback-1",
            "data": "blog_publish:123",
            "message": {"chat": {"id": "777"}},
        }
        with mock.patch.object(telegram_poll_dispatch, "CHAT_ID", "777"), \
             mock.patch.object(blogger_publisher, "publish_draft", return_value={
                 "ok": True, "title": "검토 완료 글", "url": "https://example.blogspot.com/post"
             }) as publish, \
             mock.patch.object(telegram_poll_dispatch, "answer_callback") as answer, \
             mock.patch.object(telegram_poll_dispatch, "reply") as reply:
            telegram_poll_dispatch.handle_blog_callback(callback)
        publish.assert_called_once_with("123")
        self.assertIn("공개 발행 완료", reply.call_args.args[0])
        self.assertGreaterEqual(answer.call_count, 2)

    def test_other_chat_cannot_publish(self):
        callback = {
            "id": "callback-2",
            "data": "blog_publish:123",
            "message": {"chat": {"id": "999"}},
        }
        with mock.patch.object(telegram_poll_dispatch, "CHAT_ID", "777"), \
             mock.patch.object(blogger_publisher, "publish_draft") as publish, \
             mock.patch.object(telegram_poll_dispatch, "answer_callback"):
            telegram_poll_dispatch.handle_blog_callback(callback)
        publish.assert_not_called()


if __name__ == "__main__":
    unittest.main()
