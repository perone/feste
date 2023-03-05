import unittest

import feste
from feste.task import feste_task


class TestCompute(unittest.TestCase):
    def get_dummy_graph(self):
        @feste_task
        def add(x, y):
            return x + y
        return add

    def test_compute(self):
        add = self.get_dummy_graph()
        a = add(1, 1)
        b = add(2, 2)
        v = a + b
        ret_direct = v.compute()
        ret_indirect = feste.compute(v)
        self.assertEqual((ret_direct,), ret_indirect)
