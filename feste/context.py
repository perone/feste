from typing import Any

# Default global context
global_context: dict[str, Any] = {
    "eager": False,
    "multiprocessing.chunk_size": 2,
    "multiprocessing.rerun_exceptions_locally": False,
    "multiprocessing.num_workers": None,
    "multiprocessing.func_loads": None,
    "multiprocessing.func_dumps": None,
}


def get(key: str) -> Any:
    """Gets the global context configuration for a particular key.

    :param key: configuration key.
    :return: the configuration for the specified key.
    """
    return global_context[key]


class set:
    """Creates a context to replace a configuration key.

    :param kwargs: the configuration keys.
    """
    def __init__(self, **kwargs) -> None:  # type: ignore
        self.new_context = kwargs
        self.save_context: dict[str, Any] = {}

    def __enter__(self) -> 'set':
        global global_context
        self.save_context = global_context.copy()
        global_context.update(self.new_context)
        return self

    def __exit__(self, type, value, traceback) -> None:  # type: ignore
        global global_context
        global_context = self.save_context
