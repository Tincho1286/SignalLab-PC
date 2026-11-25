from threading import Event
from time import monotonic
import unittest

from signallab_pc import jobs
from signallab_pc.dft_application import DFTExecution
from signallab_pc.execution import ExecutionContext


class ExecutionContractTests(unittest.TestCase):
    def test_existing_dft_context_alias_and_nested_worker_progress(self):
        self.assertIs(DFTExecution, ExecutionContext)
        outer, inner = [], []
        jobs.bind(Event(), outer.append)
        self.addCleanup(jobs.clear)
        ctx = ExecutionContext(progress=inner.append)
        ctx.run(lambda: jobs.checkpoint(.5))
        jobs.checkpoint(.75)
        self.assertEqual(outer, [50, 75])
        self.assertEqual(inner, [50])

    def test_explicit_cancel_at_engine_checkpoint_and_observer_cleanup(self):
        cancelled = Event()
        ctx = ExecutionContext(cancel=cancelled, progress=lambda _: cancelled.set())
        with self.assertRaises(jobs.OperationCancelled):
            ctx.run(lambda: jobs.checkpoint(.25))
        jobs.checkpoint(.50)
        with self.assertRaises(TimeoutError):
            ExecutionContext(deadline=monotonic()-1).run(lambda: None)
