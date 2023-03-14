from concurrent.futures import Executor, Future
from typing import NamedTuple, Optional

import cohere

from feste.task import FesteBase, feste_task


class GenerateParams(NamedTuple):
    """Parameters for the Cohere generate API."""
    prompt_vars: object = {}
    model: Optional[str] = "xlarge"
    preset: Optional[str] = None
    num_generations: Optional[int] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    k: Optional[int] = None
    p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    end_sequences: Optional[list[str]] = None
    stop_sequences: Optional[list[str]] = None
    return_likelihoods: Optional[str] = None
    truncate: Optional[str] = None
    logit_bias: dict[int, float] = {}


class DummyExecutor(Executor):
    def submit(self, fn, *args, **kwargs) -> Future:  # type: ignore
        f: Future = Future()
        try:
            result = fn(*args, **kwargs)
        except BaseException as e:
            f.set_exception(e)
        else:
            f.set_result(result)
        return f


class Cohere(FesteBase):
    """This is the Cohere API main class.

    .. note:: Note that the Cohere API uses an internal thread pool to do calls. This
              internal pool is replaced by a dummy one in Feste's implementation because
              we are already parallelizing the calls from outside of Cohere API
              implementation.

    :param api_key: the Cohere API key
    :param client_name: optional client name
    :param check_api_key: if API key should be checked (offline)
    :param max_retries: default number of retries
    """
    def __init__(self, api_key: str,
                 client_name: Optional[str] = None,
                 check_api_key: bool = True,
                 max_retries: int = 3) -> None:
        super().__init__()
        self.client = cohere.Client(api_key=api_key,
                                    num_workers=1,
                                    check_api_key=check_api_key,
                                    max_retries=max_retries,
                                    client_name=client_name)
        # Cohere API uses a thread pool internally, we don't need it as we
        # are already paralelizing the calls. So we just replace the
        # executor here with a dummy serial one.
        self.client._executor = DummyExecutor()

    @feste_task
    def generate(self, prompt: str,
                 complete_params: GenerateParams = GenerateParams()) -> str:
        """This is the Cohere official generate() API.

        :param prompt: input prompt text
        :param complete_params: the API parameters (e.g. temperature, etc)
        """
        all_params = complete_params._asdict()
        all_params.update({"prompt": prompt})
        ret = self.client.generate(**all_params)
        return str(ret.generations[0].text)
