import operator
from abc import ABC, abstractmethod
from typing import Any, Callable

from dask.core import istask
from dask.delayed import tokenize
from tlz import groupby

from feste.graph import FesteGraph


def make_getitem_task(object: Any, index: int) -> Any:
    """This function will create a new __getitem__ task which
    is used to get single values from return of fused calls.

    :param object: the object to get the item from
    :param index: which index to get
    :return: a task tuple (function, object, index)
    """
    return (operator.getitem, object, index)


class Optimization(ABC):
    """Optimization abstract class. This class represents an
    optimization that can be applied on the Feste graph."""
    @abstractmethod
    def apply(self, graph: FesteGraph) -> FesteGraph:
        """Apply the optimization into the graph and return
        a modified graph.

        :param graph: Feste graph to optimize
        :return: optimized graph
        """
        raise NotImplementedError


class Optimizer:
    """This is Feste optimizer, it received a list of optimizations and
    apply these optimizations on a Feste graph.

    :param optimizations: list Feste optimizations.
    """
    def __init__(self, optimizations: list[Optimization]):
        self.optimizations = optimizations

    def apply(self, graph: FesteGraph) -> FesteGraph:
        """Apply all optimizations in the Feste graph.

        :param graph: graph to optimize
        :return: graph optimized (with all optimizations)
        """
        for optim in self.optimizations:
            graph = optim.apply(graph)
        return graph

    @classmethod
    def from_backends(cls) -> 'Optimizer':
        """Create the optimizer using all optimizations from classes
        that are inheriting from the backend FesteBase class."""
        # TODO: Avoid circular imports from task
        from feste.task import FesteBase
        optimizations = []
        subclasses = FesteBase.__subclasses__()
        for subclass in subclasses:
            optimizations.extend(subclass.optimizations())
        optimizer = Optimizer(optimizations)
        return optimizer


class BatchOptimization(Optimization):
    """This is a static optimization to do batching of calls
    statically. Another optimization is done during scheduling
    as tasks might get ready before/after.

    :param rewrite_rules: rule that describes how to change a
                          single call to a batched call for
                          APIs that support it.
    """
    def __init__(self, rewrite_rules: dict[Callable, Callable]) -> None:
        self.rewrite_rules = rewrite_rules

    def apply(self, graph: FesteGraph) -> FesteGraph:
        # Get all tasks from the graph
        dependencies = graph.get_all_dependencies()
        tasks = []
        for key, task in dict(graph).items():
            if not istask(task):
                continue

            # This can be improved as we are
            # not optimizing nodes that have dependencies
            # to avoid circular dependencies
            if dependencies[key]:
                continue

            # Add the key as suffix of the task arguments
            # as we need to keep track of which keys
            # the task belong to.
            suffix_task = task + (key,)
            tasks.append(suffix_task)

        # Group by <function / object>, so we don't call
        # the batch for different objects (different parameters)
        # Note: we use here identity instead of equality
        #       across objects to group them.
        task_groups = groupby(lambda x: (x[0], x[1]), tasks)
        new_tasks = {}

        # Group key = (function, object)
        # Group task = [(function, object, parameter, key), ...]
        for group_key, group_tasks in task_groups.items():
            # Check if batching is possible
            if len(group_tasks) <= 1:
                continue

            # Check if the key is in the rewrite rules
            rewrite_rule_keys = self.rewrite_rules.keys()
            if group_key[0] not in rewrite_rule_keys:
                continue

            # Build argument list for the task
            # TODO: need to support more than one arg
            arg_key_list = [(task[2], task[3]) for task
                            in group_tasks]
            unzipped_arg_key_list = zip(*arg_key_list)
            arg_list, key_order = unzipped_arg_key_list

            # New task using rewriting rule
            new_function = self.rewrite_rules[group_key[0]]
            new_task = (new_function, group_key[1]) + (arg_list,)
            key_name = "fuse-batch-" + tokenize(new_task)
            new_tasks[key_name] = new_task

            # Replace each call to get from the batched
            # responde call.
            for index, task in enumerate(group_tasks):
                new_task = make_getitem_task(key_name, index)
                graph.update({key_order[index]: new_task})

        graph.update(new_tasks)
        return graph
