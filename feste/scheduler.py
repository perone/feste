# This module contains modified code from Dask which is
# licensed under BSD 3-Clause License for the following holder:
# Copyright (c) 2014, Anaconda, Inc. and contributors.

from __future__ import annotations

import multiprocessing
import multiprocessing.pool
import os
from collections.abc import Hashable, Mapping, Sequence
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from queue import Queue
from warnings import warn

from dask import config
from dask.callbacks import local_callbacks, unpack_callbacks
from dask.core import _execute_task, flatten, get_dependencies
from dask.local import (MultiprocessingPoolExecutor, batch_execute_tasks,
                        default_get_id, default_pack_exception, finish_task,
                        identity, nested_get, queue_get, start_state_from_dask)
from dask.multiprocessing import (_dumps, _loads, _process_get_id, get_context,
                                  initialize_worker_process, pack_exception,
                                  reraise)
from dask.optimization import cull, fuse
from dask.order import order
from dask.system import CPU_COUNT
from dask.utils import ensure_dict

from feste import context


def get_async(submit, num_workers, dsk, result, cache=None,  # type: ignore
              get_id=default_get_id, rerun_exceptions_locally=None,
              pack_exception=default_pack_exception, raise_exception=reraise,
              callbacks=None, dumps=identity, loads=identity, chunksize=None,
              **kwargs):
    """This is mostly Dask's get_async with changes to introduce optimization
    during execution, with batching being an example."""
    chunksize = chunksize or context.get("multiprocessing.chunk_size")

    queue: Queue = Queue()

    if isinstance(result, list):
        result_flat = set(flatten(result))
    else:
        result_flat = {result}
    results = set(result_flat)

    dsk = dict(dsk)
    with local_callbacks(callbacks) as callbacks:
        _, _, pretask_cbs, posttask_cbs, _ = unpack_callbacks(callbacks)
        started_cbs = []
        succeeded = False
        # if start_state_from_dask fails, we will have something
        # to pass to the final block.
        state = {}
        try:
            for cb in callbacks:
                if cb[0]:
                    cb[0](dsk)
                started_cbs.append(cb)

            keyorder = order(dsk)

            state = start_state_from_dask(dsk, cache=cache, sortkey=keyorder.get)

            for _, start_state, _, _, _ in callbacks:
                if start_state:
                    start_state(dsk, state)

            if rerun_exceptions_locally is None:
                rerun_exceptions_locally = \
                    context.get("multiprocessing.rerun_exceptions_locally")

            if state["waiting"] and not state["ready"]:
                raise ValueError("Found no accessible jobs in dask")

            def fire_tasks(chunksize: int) -> None:
                """Fire off a task to the thread pool"""
                # Determine chunksize and/or number of tasks to submit
                nready = len(state["ready"])
                if chunksize == -1:
                    ntasks = nready
                    chunksize = -(ntasks // -num_workers)
                else:
                    used_workers = -(len(state["running"]) // -chunksize)
                    avail_workers = max(num_workers - used_workers, 0)
                    ntasks = min(nready, chunksize * avail_workers)

                # Prep all ready tasks for submission
                args = []
                for _ in range(ntasks):
                    # Get the next task to compute (most recently added)
                    key = state["ready"].pop()
                    # Notify task is running
                    state["running"].add(key)
                    for f in pretask_cbs:
                        f(key, dsk, state)

                    # Prep args to send
                    data = {
                        dep: state["cache"][dep] for dep in get_dependencies(dsk, key)
                    }
                    args.append(
                        (
                            key,
                            dumps((dsk[key], data)),
                            dumps,
                            loads,
                            get_id,
                            pack_exception,
                        )
                    )

                # Batch submit
                for i in range(-(len(args) // -chunksize)):
                    each_args = args[i * chunksize:(i + 1) * chunksize]
                    if not each_args:
                        break
                    fut = submit(batch_execute_tasks, each_args)
                    fut.add_done_callback(queue.put)

            # Main loop, wait on tasks to finish, insert new ones
            while state["waiting"] or state["ready"] or state["running"]:
                fire_tasks(chunksize)
                for key, res_info, failed in queue_get(queue).result():
                    if failed:
                        exc, tb = loads(res_info)
                        if rerun_exceptions_locally:
                            data = {
                                dep: state["cache"][dep]
                                for dep in get_dependencies(dsk, key)
                            }
                            task = dsk[key]
                            _execute_task(task, data)  # Re-execute locally
                        else:
                            raise_exception(exc, tb)
                    res, worker_id = loads(res_info)
                    state["cache"][key] = res
                    finish_task(dsk, key, state, results, keyorder.get)
                    for f in posttask_cbs:
                        f(key, res, dsk, state, worker_id)

            succeeded = True

        finally:
            for _, _, _, _, finish in started_cbs:
                if finish:
                    finish(dsk, state, not succeeded)

    return nested_get(result, state["cache"])


def get_multiprocessing(dsk: Mapping, keys: Sequence[Hashable] | Hashable,  # type: ignore
                        num_workers=None, func_loads=None, func_dumps=None,
                        optimize_graph=True, pool=None, initializer=None,
                        chunksize=None, **kwargs):
    chunksize = chunksize or context.get("multiprocessing.chunk_size")
    pool = pool or config.get("pool", None)
    initializer = initializer or config.get("multiprocessing.initializer", None)
    num_workers = num_workers or context.get("multiprocessing.num_workers") or CPU_COUNT
    if pool is None:
        # In order to get consistent hashing in subprocesses, we need to set a
        # consistent seed for the Python hash algorithm. Unfortunately, there
        # is no way to specify environment variables  only for the Pool
        # processes, so we have to rely on environment variables being
        # inherited.
        if os.environ.get("PYTHONHASHSEED") in (None, "0"):
            os.environ["PYTHONHASHSEED"] = "42"
        mp_context = get_context()
        initializer = partial(initialize_worker_process, user_initializer=initializer)
        pool = ProcessPoolExecutor(
            num_workers, mp_context=mp_context, initializer=initializer
        )
        cleanup = True
    else:
        if initializer is not None:
            warn(
                "The ``initializer`` argument is ignored when ``pool`` is provided. "
                "The user should configure ``pool`` with the needed ``initializer`` "
                "on creation."
            )
        if isinstance(pool, multiprocessing.pool.Pool):
            pool = MultiprocessingPoolExecutor(pool)
        cleanup = False

    # Optimize Dask
    dsk = ensure_dict(dsk)
    dsk2, dependencies = cull(dsk, keys)
    if optimize_graph:
        dsk3, dependencies = fuse(dsk2, keys, dependencies)
    else:
        dsk3 = dsk2

    # We specify marshalling functions in order to catch serialization
    # errors and report them to the user.
    loads = func_loads or context.get("multiprocessing.func_loads") or _loads
    dumps = func_dumps or context.get("multiprocessing.func_dumps") or _dumps

    # Note former versions used a multiprocessing Manager to share
    # a Queue between parent and workers, but this is fragile on Windows
    # (issue #1652).
    try:
        # Run
        result = get_async(
            pool.submit,
            pool._max_workers,
            dsk3,
            keys,
            get_id=_process_get_id,
            dumps=dumps,
            loads=loads,
            pack_exception=pack_exception,
            raise_exception=reraise,
            chunksize=chunksize,
            # rerun_exceptions_locally=False,
            **kwargs,
        )
    finally:
        if cleanup:
            pool.shutdown()
    return result
