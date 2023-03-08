from graphlib import TopologicalSorter
from typing import Any, Iterator, Mapping

from dask.base import collections_to_dsk
from dask.base import unpack_collections as base_unpack_collections
from dask.core import get_dependencies
from dask.dot import dot_graph
from dask.order import order
from rich.pretty import pprint


class FesteGraph(Mapping):
    """A computational graph representing the flow described by the
    call of Feste tasks.

    :param graph: initialize from a dictionary.
    """
    def __init__(self, graph: dict[str, Any]):
        self.graph = graph

    @classmethod
    def collect(cls, *args) -> tuple['FesteGraph', list, callable]:  # type:ignore
        """Create a Feste graph from a collection of objects.

        :param args: collection of objects.
        :return: Tuple (Graph, collections, repack function)
        """
        collections, repack = base_unpack_collections(*args)
        dsk = collections_to_dsk(collections, optimize_graph=False)
        return cls(dict(dsk)), collections, repack

    def get_all_dependencies(self) -> dict[str, str]:
        """Returns a dict with all dependencies."""
        dependencies = {k: get_dependencies(self.graph, k)
                        for k in self.graph}
        return dependencies

    def topological_sorter(self) -> TopologicalSorter:
        """Returns a topological sorter from the graph dependencies."""
        dependencies = self.get_all_dependencies()
        return TopologicalSorter(dependencies)

    def to_dict(self) -> dict:
        """Convert the graph to a dictionary."""
        return dict(self.graph)

    def print(self) -> None:
        """Print the internal graph representation."""
        pprint(self.graph)

    def order(self) -> dict[str, int]:
        """Return the execution order hint."""
        return order(self.graph)  # type: ignore

    def __getitem__(self, key: str) -> Any:
        """Gets an item from the graph.

        :param key: the graph key
        """
        return self.graph[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """Sets an item from the graph.

        :param key: param to set
        :param value: the value to set
        """

        self.graph[key] = value

    def __iter__(self) -> Iterator:
        return iter(self.graph)

    def __len__(self) -> int:
        return len(self.graph)

    def update(self, graph_dict: dict[str, Any]) -> None:
        """Update the internal graph from a dictionary.

        :param graph_dict: dictionary to update from.
        """
        self.graph.update(graph_dict)

    def visualize(self, filename: str) -> None:
        """Export the graph into a file.

        :param filename: filename to export the graph (e.g. .pdf, .png)
        """
        dot_graph(dict(self), filename=filename,
                  verbose=True, collapse_outputs=False)
