Prompt templates
-------------------------------------------------------------------------------
To facilitate prompting management we use
`Jinja2 <https://jinja.palletsprojects.com/en/3.1.x/templates>`_ templating
engine. Jinja2 is quite powerful because it has a rich language for loops,
controls and variable rendring with proper environment management, therefore
there is no need to reinvent the wheel.

.. seealso:: Different than other LLM orchestration and chaining APIs, **Feste
             prompts are language-aware**. This is a design choice to enable
             multi-lingual prompts and proper language manamgement. We adopted
             the `ISO-639 <https://en.wikipedia.org/wiki/ISO_639>`_ for it.

.. note:: All examples in this page are executed in **eager mode** for clarity.

Simple example
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The most simple use of a prompt template is the following:

.. code-block:: python
    
    from feste.prompt import Prompt

    p = Prompt("Hello {{message}}!")
    res = p(message="world")

    print(res)
    "Hello world!"

Language-aware prompt
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
The default language of a prompt is English (en), but you can change that:

.. code-block:: python
    
    p = Prompt("Olá {{mensagem}}!", language="pt")
    
    print(p.language)
    Language(part3='por', part1='pt', name='Portuguese', ...)

By using the correct language in the prompt, you will get warnings if you
do things like concatenation of prompts with different languages:

.. code-block:: python
    
    p_en = Prompt("Hello {{message}}!")
    p_pt = Prompt("Olá prompt", language="pt")
    
    p_new = p_en + p_pt

    "LanguageMismatch: You are concatenating prompts with different languages."

Getting template variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
You can also get the list of prompt variables from your template:

.. code-block:: python

    p = Prompt("Hello {{message}}! My name is {{name}}.")
    
    print(p.variables())
    {'message', 'name'}

Prompt environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Sometimes it is helpful to share a common environment across different
prompt templates. Think of systems where for example you want to share
a agent name across different templates. To achieve that you can use
an environment like in the example below:

.. code-block:: python

    from feste.prompt import Prompt, FesteEnvironment

    smart_bot_env = FesteEnvironment()
    smart_bot_env.globals.update({
        "agent_name": "SmartBot"
    })
    p = Prompt("Hello {{message}}! My name is {{agent_name}}.",
               environment=smart_bot_env)    
    
    print(p(message="John"))
    "Hello John! My name is SmartBot."




