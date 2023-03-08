import copyreg
import warnings
from pathlib import Path
from typing import Any, Optional, Union

import iso639
from cloudpickle import dumps, loads
from jinja2 import Environment, meta

from feste.task import FesteBase, feste_task


def _unpickle_Language(serialized) -> iso639.Language:  # type: ignore
    """Unpickle iso639 class (to support cloudpickle)."""
    part1 = loads(serialized)
    return iso639.Language.from_part1(part1)


def _pickle_Language(cp: iso639.Language) -> Any:
    """Pickle iso639 class (to support cloudpickle)."""
    serialized = dumps(cp.part1)
    return _unpickle_Language, (serialized,)


# Register pickle/unpickle for iso639.Language
copyreg.pickle(iso639.Language, _pickle_Language)


# Internal Feste globals
FESTE_TEMPLATE_GLOBALS: dict[str, Any] = {
    # TODO: add globals and utilities that are internal to Feste
}


class LanguageMismatch(UserWarning):
    """Exception when languages are mixed across prompts."""
    pass


class FesteEnvironment(Environment):
    """This is the default Feste environment, it adds Feste's global
    utilities into the Jinja2 environment.
    """
    def __init__(self, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(**kwargs)
        self.add_feste_globals()

    def add_feste_globals(self) -> None:
        self.globals.update(FESTE_TEMPLATE_GLOBALS)


class Prompt(FesteBase):
    """Prompt utility. This class represents a prompt and its
    associated language and environment.

    :param template: the prompt template (in Jinja2 format)
    :param language: language code, defaults to en (follows ISO639)
    :param environment: optional environment, defaults to Feste's env.
    """
    def __init__(self, template: str,
                 language: Union[str, iso639.Language] = "en",
                 environment: Optional[Environment] = None) -> None:
        self.environment = environment or FesteEnvironment()
        if isinstance(language, str):
            self.language_code = iso639.Language.match(language)
        else:
            self.language_code = language
        self.template = template

    def __add__(self, other: "Prompt") -> "Prompt":
        """Concatenate two different prompts and check if languages
        match.

        :param other: other Prompt to concatenate
        """
        # Check if prompt languages are the same
        if self.language != other.language:
            warnings.warn("You are concatenating prompts with "
                          "different languages.", LanguageMismatch)

        # Concatenate the templates
        concat_template = self.template + other.template
        new_prompt = Prompt(concat_template, self.language, self.environment)
        return new_prompt

    @property
    def language(self) -> iso639.Language:
        """Returns the ISO639 language code of the prompt."""
        return self.language_code

    @classmethod
    def from_file(cls, filename: Union[Path, str], **kwargs):  # type: ignore
        """Loads the prompt from a text file.

        :param filename: the filename or Python's native Path object.
        :param kwargs: extra arguments being passed to the Prompt constructor.
        """
        filename = Path(filename)
        with filename.open("r") as fhandle:
            template = fhandle.read()
        return cls(template, **kwargs)

    def variables(self) -> set[str]:
        """Return a list of variables present in the template.

        :returns: set of variables.
        """
        parsed_content = self.environment.parse(self.template)
        tokens = meta.find_undeclared_variables(parsed_content)
        return tokens

    @feste_task
    def __call__(self, **kwargs) -> str:  # type: ignore
        compiled_template = self.environment.from_string(self.template)
        return compiled_template.render(**kwargs)

    def __len__(self) -> int:
        return len(self.template)

    def __repr__(self) -> str:
        return f"<Prompt Language='{self.language.name}' Length={len(self)}>"
