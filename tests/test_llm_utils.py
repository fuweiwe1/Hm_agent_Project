"""LLM 重试工具测试。"""
import unittest

from utils.llm_utils import llm_retry


class TestLlmRetry(unittest.TestCase):
    def test_success_on_first_try(self):
        call_count = 0

        @llm_retry(max_retries=3)
        def succeed():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = succeed()
        self.assertEqual(result, "ok")
        self.assertEqual(call_count, 1)

    def test_retries_then_succeeds(self):
        call_count = 0

        @llm_retry(max_retries=3, backoff_seconds=0)
        def fail_twice_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RuntimeError("transient")
            return "ok"

        result = fail_twice_then_succeed()
        self.assertEqual(result, "ok")
        self.assertEqual(call_count, 3)

    def test_raises_after_exhausting_retries(self):
        @llm_retry(max_retries=2, backoff_seconds=0)
        def always_fail():
            raise RuntimeError("permanent")

        with self.assertRaises(RuntimeError) as ctx:
            always_fail()
        self.assertIn("permanent", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
