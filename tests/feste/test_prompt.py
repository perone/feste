import unittest

from feste.prompt import FesteEnvironment, Prompt


class TestPrompt(unittest.TestCase):
    def test_single_parameter(self):
        p = Prompt("Hello {{message}}.")
        res = p(message="World")
        self.assertEqual(res.compute(), "Hello World.")

    def test_multiple_parameter(self):
        p = Prompt("Hello {{message}}, dear {{name}}.")
        res = p(message="World", name="John")
        self.assertEqual(res.compute(), "Hello World, dear John.")

    def test_environment(self):
        smart_bot_env = FesteEnvironment()
        smart_bot_env.globals.update({
            "agent_name": "SmartBot"
        })
        p = Prompt("Hello {{message}}! My name is {{agent_name}}.",
                environment=smart_bot_env)
        expected_msg = "Hello John! My name is SmartBot."
        ret = p(message="John")
        self.assertEqual(ret.compute(), expected_msg)

    def test_length(self):
        p = Prompt("Hello")
        self.assertEqual(len(p), 5)

    def test_variables(self):
        p = Prompt("{{a}} and {{b}}")
        expected = {"a", "b"}
        self.assertEqual(p.variables(), expected)

    def test_concatenate(self):
        a = Prompt("prompt A ")
        b = Prompt("prompt B")
        c = a + b
        out = c()
        self.assertEqual(out.compute(), "prompt A prompt B")
