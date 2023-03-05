import unittest

from feste import context, task


class TestTask(unittest.TestCase):
    def test_task_bin_op(self):
        @task.feste_task
        def add(x, y):
            return x + y

        a = add(1, 1)
        b = add(1, 1)
        c = a + b
        self.assertIsInstance(c, task.FesteDelayed)

    def test_task_unary_op(self):
        @task.feste_task
        def add(x, y):
            return x + y

        a = add(1, 1)
        b = abs(a)
        self.assertIsInstance(b, task.FesteDelayed)

    def test_task_eager(self):
        
        @task.feste_task
        def dummy_task(x: int) -> int:
            return x + 1

        with context.set(eager=False):
            ret_delayed = dummy_task(0)
            self.assertIsInstance(ret_delayed, task.FesteDelayed)

        with context.set(eager=True):
            ret_eager = dummy_task(0)
            self.assertEqual(ret_eager, 1)

    def test_task_eaget_class(self):
        class DummyTask(task.FesteBase):
            @task.feste_task
            def dummy_add(self, a, b) -> int:
                return a + b

        with context.set(eager=True):
            dtask_eager = DummyTask()
            ret_eager = dtask_eager.dummy_add(1, 1)
            self.assertEqual(ret_eager, 2)

        with context.set(eager=False):
            dtask = DummyTask()
            ret = dtask.dummy_add(1, 1)
            self.assertIsInstance(ret, task.FesteDelayed)


