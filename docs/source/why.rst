Why Feste ?
-------------------------------------------------------------------------------
Most "Prompt-Ops" tools are nowadays focused in chaining tasks/prompts. Feste
goes beyond chaining and provides optimizations such as **automatic batching**
of API calls to avoid latency, **automatic parallelization** of tasks that can
be executed in parallel and even **distributed execution** (*coming soon*).

Although Feste also provides an **eager mode**, Feste achieves its goals by introducing
a lazy evaluation API where each call to Feste tasks builds an internal graph that gets
otpimized and executed in parallel, so you don't have to worry about async calls or
batching API calls. For more information please read the :ref:`architecture_design`.
