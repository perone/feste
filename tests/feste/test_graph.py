import io
import unittest
from contextlib import closing

from feste.graph import FesteGraph
from feste.task import feste_task


class TestGraph(unittest.TestCase):
    def get_dummy_graph(self):
        @feste_task
        def add(x, y):
            return x + y
        return add

    def test_collect(self):
        add = self.get_dummy_graph()
        a = add(1, 1)
        b = add(2, 2)
        c = a + b

        feste_graph, _, _ = FesteGraph.collect([c])
        dict_graph = dict(feste_graph)
        self.assertEqual(len(dict_graph), 3)

        feste_graph, _, _ = FesteGraph.collect([a])
        dict_graph = dict(feste_graph)
        self.assertEqual(len(dict_graph), 1)
        
    def test_dependencies(self):
        add = self.get_dummy_graph()
        a = add(1, 1)
        b = add(2, 2)
        c = a + b

        feste_graph, _, _= FesteGraph.collect([c])
        deps = feste_graph.get_all_dependencies()
        self.assertEqual(len(deps[c.key]), 2)
        self.assertEqual(len(deps[a.key]), 0)
        self.assertEqual(len(deps[b.key]), 0)

    def test_toposort(self):
        add = self.get_dummy_graph()
        a = add(1, 1)
        b = add(2, 2)
        c = a + b

        feste_graph, _, _ = FesteGraph.collect([c])
        ts = feste_graph.topological_sorter()
        static_order = list(ts.static_order())

        # A and B must be finished before C
        parallel = [a.key, b.key]
        self.assertIn(static_order[0], parallel)
        self.assertIn(static_order[1], parallel)
        self.assertIn(static_order[2], c.key)

    def test_dagviz(self):
        add = self.get_dummy_graph()
        a = add(1, 1)
        b = add(2, 2)
        c = a + b
        feste_graph, _, _ = FesteGraph.collect([c])
        with closing(io.StringIO()) as sio:
            feste_graph.dagviz_metro(sio)
            val = sio.getvalue()
        self.assertTrue(len(val) > 0)
