# This module contains modified code from Dask which is
# licensed under BSD 3-Clause License for the following holder:
# Copyright (c) 2014, Anaconda, Inc. and contributors.

import inspect
import operator
import types
from typing import Any, Optional

from dask.base import is_dask_collection, replace_name_in_key
from dask.core import quote
from dask.delayed import Delayed, right, tokenize, unpack_collections, unzip
from dask.highlevelgraph import HighLevelGraph
from dask.utils import apply, funcname
from tlz import concat, curry

from feste import context
from feste.compute import compute
from feste.optimization import Optimization


class FesteDelayed(Delayed):
    """Feste delayed is a lazy-evaluation node in Feste's graph."""
    def __call__(self, *args, pure=None, dask_key_name=None, **kwargs):  # type:ignore
        if context.get("eager"):
            return self._obj(*args, **kwargs)
        else:
            func = feste_task(apply, pure=pure)
            if dask_key_name is not None:
                return func(self, args, kwargs, dask_key_name=dask_key_name)
            return func(self, args, kwargs)

    def compute(self, **kwargs) -> Any:  # type: ignore
        (result,) = compute(self, traverse=False, **kwargs)
        return result

    def __repr__(self) -> str:
        return f"FesteDelayed({repr(self.key)})"

    def _rebuild(self, dsk, *, rename=None) -> Any:  # type: ignore
        key = replace_name_in_key(self.key, rename) if rename else self.key
        if isinstance(dsk, HighLevelGraph) and len(dsk.layers) == 1:
            layer = next(iter(dsk.layers))
        else:
            layer = None
        return FesteDelayed(key, dsk, self._length, layer=layer)

    @classmethod
    def _get_binary_operator(cls, op, inv=False) -> Any:  # type: ignore
        method = feste_task(right(op) if inv else op, pure=True)
        return lambda *args, **kwargs: method(*args, **kwargs)

    _get_unary_operator = _get_binary_operator


class FesteDelayedLeaf(FesteDelayed):
    """This is very similar to the DelayedLeaf in Dask, with the
    differences that we adjust the call to include eager mode execution."""
    __slots__ = ("_obj", "_pure", "_nout")

    def __init__(self, obj: Any, key: Any,
                 pure: Optional[bool] = None,
                 nout: Optional[int] = None) -> None:
        super().__init__(key, None)
        self._obj = obj
        self._pure = pure
        self._nout = nout

    @property
    def dask(self) -> Any:
        return HighLevelGraph.from_collections(
            self._key, {self._key: self._obj}, dependencies=()
        )

    def __call__(self, *args, **kwargs) -> Any:  # type: ignore
        if context.get("eager"):
            return self._obj(*args, **kwargs)
        else:
            return call_function(
                self._obj, self._key, args, kwargs,
                pure=self._pure, nout=self._nout
            )

    @property
    def __name__(self) -> Any:
        return self._obj.__name__

    @property
    def __doc__(self):  # type: ignore
        return self._obj.__doc__


@curry
def feste_task(obj: Any, name: Optional[Any] = None,
               pure: Optional[bool] = None,
               nout: Optional[int] = None,
               traverse: bool = True) -> FesteDelayed:
    """Function and decorator that can be used to introduce the lazy-evaluation
    nodes of computation using Feste's graph."""

    if isinstance(obj, FesteDelayed):
        return obj

    if is_dask_collection(obj) or traverse:
        task, collections = unpack_collections(obj)
    else:
        task = quote(obj)
        collections = set()

    if not (nout is None or (type(nout) is int and nout >= 0)):
        raise ValueError("nout must be None or a "
                         "non-negative integer, got %s" % nout)
    if task is obj:
        if not name:
            try:
                prefix = obj.__name__
            except AttributeError:
                prefix = type(obj).__name__
            token = tokenize(obj, nout, pure=pure)
            name = f"{prefix}-{token}"
        return FesteDelayedLeaf(obj, name, pure=pure, nout=nout)
    else:
        if not name:
            name = f"{type(obj).__name__}-{tokenize(task, pure=pure)}"
        layer = {name: task}
        graph = HighLevelGraph.from_collections(name, layer,
                                                dependencies=collections)
        return FesteDelayed(name, graph, nout)


def call_function(func, func_token, args,  # type:ignore
                  kwargs, pure=None, nout=None) -> Any:
    dask_key_name = kwargs.pop("dask_key_name", None)
    pure = kwargs.pop("pure", pure)

    if dask_key_name is None:
        name = "{}-{}".format(
            funcname(func),
            tokenize(func_token, *args, pure=pure, **kwargs),
        )
    else:
        name = dask_key_name

    args2, collections = unzip(map(unpack_collections, args), 2)
    collections = list(concat(collections))

    if kwargs:
        dask_kwargs, collections2 = unpack_collections(kwargs)
        collections.extend(collections2)
        task = (apply, func, list(args2), dask_kwargs)
    else:
        task = (func,) + args2

    graph = HighLevelGraph.from_collections(
        name, {name: task}, dependencies=collections
    )
    nout = nout if nout is not None else None
    return FesteDelayed(name, graph, length=nout)


class FesteBase:
    """Feste Base class that is used for backends. Every backend that
    is added in Feste needs to inherit from this class as it will
    add support for eager execution and optimizations."""
    def __init__(self) -> None:
        eager_mode = context.get("eager")
        if eager_mode:
            self._replace_delayed()

    @classmethod
    def optimizations(cls) -> list[Optimization]:
        return []

    def _replace_delayed(self) -> None:
        members = inspect.getmembers(self)
        for name, obj in members:
            if isinstance(obj, FesteDelayed):
                setattr(self, name, obj._obj)

            if inspect.ismethod(obj):
                if isinstance(obj.__func__, FesteDelayed):
                    original_function = obj.__func__._obj
                    bind_method = types.MethodType(original_function, self)
                    setattr(self, name, bind_method)


for op in [
    operator.abs,
    operator.neg,
    operator.pos,
    operator.invert,
    operator.add,
    operator.sub,
    operator.mul,
    operator.floordiv,
    operator.truediv,
    operator.mod,
    operator.pow,
    operator.and_,
    operator.or_,
    operator.xor,
    operator.lshift,
    operator.rshift,
    operator.eq,
    operator.ge,
    operator.gt,
    operator.ne,
    operator.le,
    operator.lt,
    operator.getitem,
]:
    FesteDelayed._bind_operator(op)


try:
    FesteDelayed._bind_operator(operator.matmul)
except AttributeError:
    pass
