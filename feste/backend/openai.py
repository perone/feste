from typing import Any, NamedTuple, Optional

import openai

from feste.optimization import BatchOptimization, Optimization
from feste.task import FesteBase, feste_task


class CompleteParams(NamedTuple):
    """Parameters for the OpenAI Complete API."""
    model: str = "text-davinci-003"
    suffix: Optional[str] = None
    max_tokens: int = 16
    temperature: float = 1.0
    top_p: float = 1.0
    n: int = 1
    stream: bool = False
    logprobs: Optional[int] = None
    echo: bool = False
    stop: Optional[str] = None
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    best_of: int = 1
    logit_bias: Optional[dict[str, int]] = None
    user: Optional[str] = None


class OpenAI(FesteBase):
    """This is the OpenAI API main class.

    :param api_key: the OpenAI API key
    :param organization: optional organization
    """
    def __init__(self, api_key: str,
                 organization: Optional[str] = None) -> None:
        super().__init__()
        self.set_api_key(api_key, organization)
        self.api_key = api_key
        self.organization = organization

    def _api_key_guard(self) -> None:
        """OpenAI Python client doesn't do proper encapsulation of
        API Keys, see: https://github.com/openai/openai-python/issues/233.
        Therefore, we need to set the API in each process before each call
        to make sure it is set in the object."""
        if openai.api_key is None:
            self.set_api_key(self.api_key, self.organization)

    @staticmethod
    def set_api_key(api_key: str, organization: Optional[str] = None) -> None:
        """Sets the API key and organization in the OpenAI module.

        :param api_key: the OpenAI API key
        :param organization: optional organization
        """
        openai.organization = organization
        openai.api_key = api_key

    @classmethod
    def optimizations(cls) -> list[Optimization]:
        """Optimizations implemented for OpenAI API."""
        batch_optim = BatchOptimization({
            cls.complete._obj: cls.complete_batch._obj,
        })
        return [batch_optim,]

    @staticmethod
    def _prepare_parameters(complete_params: CompleteParams) -> dict[str, Any]:
        all_params = complete_params._asdict()
        all_params = {k: v for k, v in all_params.items() if v is not None}
        return all_params

    @feste_task
    def complete(self, prompt: str,
                 complete_params: CompleteParams = CompleteParams()) -> str:
        """This is the OpenAI official complete() API.

        :param prompt: input prompt text
        :param complete_params: the API parameters (e.g. temperature, etc)
        """
        all_params = self._prepare_parameters(complete_params)
        all_params.update({"prompt": prompt})
        self._api_key_guard()
        ret = openai.Completion.create(**all_params)
        text = str(ret.choices[0].text)
        return text

    @feste_task
    def complete_batch(self, prompt: list[str],
                       complete_params: CompleteParams = CompleteParams()) \
            -> list[str]:
        """This is the OpenAI official complete() API, but batched.

        :param prompt: input prompt text list
        :param complete_params: the API parameters (e.g. temperature, etc)
        """
        all_params = self._prepare_parameters(complete_params)
        all_params.update({"prompt": prompt})
        self._api_key_guard()
        ret = openai.Completion.create(**all_params)
        choices = [str(r.text) for r in ret.choices]
        return choices
