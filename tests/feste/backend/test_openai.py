import unittest
from unittest.mock import MagicMock, patch

import openai

from feste import context
from feste.backend.openai import CompleteParams, OpenAI


class OpenAIMock:
    def create(self, **kwargs):
        prompt = kwargs.pop("prompt")
        n = len(prompt)
        if isinstance(prompt, tuple):
            choices = [MagicMock(text="batched " + t) for t in prompt]
        else:
            choices = [MagicMock(text="single "+ prompt)]
        return MagicMock(choices=choices)


class TestOpenAI(unittest.TestCase):
    def setUp(self):
       self.api = OpenAI("invalid-key")

    def test_complete(self):
        with patch("openai.Completion", new_callable=OpenAIMock):
            ret = self.api.complete._obj(self.api, prompt="a")
            self.assertEqual(ret, "single a")

    def test_complete_batch(self):
        with patch("openai.Completion", new_callable=OpenAIMock):
            ret = self.api.complete_batch._obj(self.api, prompt=("a", "b"))
            self.assertListEqual(ret, ["batched a", "batched b"])

    def test_prepare_params(self):
        params = CompleteParams(user=None)
        all_params = self.api._prepare_parameters(params)
        self.assertNotIn("user", all_params)

    def test_set_api_key(self):
        mock_key = "abc"
        self.api.set_api_key(mock_key)
        self.assertEqual(openai.api_key, mock_key)

    # def test_(self):
    #     #a = OpenAI()
    #     #print()
    #     #print()
    #     #print(a.complete.__func__)
    #     with context.set(eager=True):
    #         b = OpenAI()
    #         v = b.complete("lala")
    #         print(v)
    #         #print(b.complete.__func__)
    #     #print()




