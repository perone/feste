# This module contains modified code from Dask which is
# licensed under BSD 3-Clause License for the following holder:
# Copyright (c) 2014, Anaconda, Inc. and contributors.
from typing import Any, Callable

from feste.graph import FesteGraph
from feste.optimization import Optimizer
from feste.scheduler import get_multiprocessing


def compute(*args, scheduler_fn: Callable = get_multiprocessing,  # type: ignore
            optimize_graph: bool = True, **kwargs) -> Any:
    """This function will compute the given objects using the default
    multiprocessing scheduler.

    :param scheduler_fn: a scheduler (defaults to multiprocessing scheduler)
    :param optimize_graph: if graph should be optimized
    :return: computed objects
    """
    feste_graph, collections, repack = FesteGraph.collect(*args)

    if optimize_graph:
        optimizer = Optimizer.from_backends()
        feste_graph = optimizer.apply(feste_graph)

    keys, postcomputes = [], []
    for x in collections:
        keys.append(x.__dask_keys__())
        postcomputes.append(x.__dask_postcompute__())

    results = scheduler_fn(dict(feste_graph), keys, **kwargs)
    return repack([f(r, *a) for r, (f, a) in zip(results, postcomputes)])  # type: ignore
