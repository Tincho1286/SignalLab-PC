from threading import Event
from time import monotonic
from unittest.mock import patch
import unittest

from signallab_pc import jobs
from signallab_pc.dft_application import DFTExecution
from signallab_pc.execution import ExecutionContext, ResourcePool
from signallab_pc.resources import ResourceLimitError


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

    def test_invalid_budgets_fail_before_entering_work(self):
        for invalid in (-1, 0, True, 1.5):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(ValueError, 'capacidad'):
                    ResourcePool(invalid)
                with self.assertRaisesRegex(ValueError, 'presupuesto'):
                    ExecutionContext(max_work_bytes=invalid)
        with self.assertRaisesRegex(ValueError, 'plazo'):
            ExecutionContext(deadline=float('nan'))
        pool = ResourcePool(4)
        for invalid in (-1, False, 1.5):
            with self.assertRaises(ValueError):
                with pool.reserve(invalid):
                    self.fail('El pool admitió una reserva inválida.')
            with self.assertRaises(ValueError):
                ExecutionContext().require(invalid)
        with self.assertRaises(ResourceLimitError):
            ExecutionContext(max_work_bytes=4).require(5)
        with pool.reserve(4):
            with pool.reserve(0):
                pass

    def test_expiring_while_processing_progress_releases_the_pool(self):
        pool = ResourcePool(4)
        ctx = ExecutionContext(deadline=10, progress=lambda _: None, pool=pool)
        with patch('signallab_pc.execution.monotonic', side_effect=[8, 9, 10]):
            with self.assertRaisesRegex(TimeoutError, 'plazo'):
                ctx.run(lambda: jobs.checkpoint(.5), work_bytes=4)
        with pool.reserve(4):
            pass
