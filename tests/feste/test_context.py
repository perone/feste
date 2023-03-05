import unittest

from feste import context


class TestContext(unittest.TestCase):
    def test_change_context(self):
        context_before = context.global_context.copy()
        with context.set(abcdefg=True):
            context_before["abcdefg"] = True
            self.assertEqual(context.global_context, context_before)
        self.assertNotEqual(context.global_context, context_before)
