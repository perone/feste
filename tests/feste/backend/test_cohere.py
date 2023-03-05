import unittest
from unittest.mock import MagicMock, patch

from feste.backend.cohere import Cohere


def generate(*args, **kwargs):
    prompt = kwargs.pop("prompt")
    return MagicMock(generations=[MagicMock(text=prompt)])


class TestCohere(unittest.TestCase):
    def setUp(self) -> None:
       self.api = Cohere(api_key="invalid-key", check_api_key=False)

    @patch("cohere.client.Client.generate", generate)
    def test_generate(self) -> None:
        prompt_test = "TEST"
        ret = self.api.generate._obj(self.api, prompt_test)
        self.assertEqual(ret, prompt_test)
