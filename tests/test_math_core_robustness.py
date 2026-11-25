from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event
from time import monotonic
import unittest
from unittest.mock import patch

import numpy as np

from signallab_pc import session
from signallab_pc.dsp_application import PSDRequest, estimate_psd
from signallab_pc.dsp_pipeline import estimate_pipeline_memory, run_pipeline, store_pipeline
from signallab_pc.execution import ExecutionContext, ResourcePool
from signallab_pc.jobs import OperationCancelled
from signallab_pc.jobs import checkpoint
from signallab_pc.model import Signal
from signallab_pc.project import Project
from signallab_pc.resources import ResourceLimitError
from test_math_dsp_pipeline import case


class CoreRobustnessTests(unittest.TestCase):
    def test_shared_pool_rejects_contention_releases_and_is_reusable(self):
        pool = ResourcePool(1024)
        ctx = ExecutionContext(pool=pool)
        running, release = Event(), Event()

        def first():
            running.set()
            if not release.wait(5):
                raise TimeoutError('Test de contención vencido.')

        with ThreadPoolExecutor(max_workers=2) as executor:
            active = executor.submit(ctx.run,first,work_bytes=800)
            try:
                self.assertTrue(running.wait(4))
                second = executor.submit(ctx.run,lambda:42,work_bytes=512)
                with self.assertRaises(ResourceLimitError):
                    second.result(timeout=4)
            finally:
                release.set()
            active.result(timeout=4)
        self.assertEqual(ctx.run(lambda:42,work_bytes=1024),42)

    def test_pool_releases_on_failure_and_nested_deadlines_work(self):
        pool = ResourcePool(100)
        ctx = ExecutionContext(pool=pool)
        def fail():
            raise LookupError('Fallo de cálculo')
        with self.assertRaises(LookupError):
            ctx.run(fail,work_bytes=100)
        self.assertEqual(ctx.run(lambda:10,work_bytes=100),10)
        with self.assertRaises(TimeoutError):
            ExecutionContext(deadline=monotonic()-1).run(lambda:None)
        clock=[0.]
        def advance_clock():
            clock[0]=2.
            checkpoint(.5)
        with patch('signallab_pc.execution.monotonic',side_effect=lambda:clock[0]):
            with self.assertRaises(TimeoutError):
                ExecutionContext(deadline=1.).run(lambda:ExecutionContext().run(advance_clock))

    def test_flow_admission_accounts_for_retained_results_before_first_stage(self):
        request=case(2,3)
        memory=estimate_pipeline_memory(request)
        self.assertGreater(memory.total_bytes,memory.work_bytes)
        with patch('signallab_pc.dsp_pipeline.resample') as first:
            with self.assertRaises(ResourceLimitError):
                run_pipeline(request,ExecutionContext(max_work_bytes=memory.total_bytes-1))
            first.assert_not_called()
        run_pipeline(request,ExecutionContext(pool=ResourcePool(memory.total_bytes)))

    def test_psd_cancels_inside_welch_at_an_engine_progress_checkpoint(self):
        source=Signal(np.ones(128),metadata={'sample_rate_hz':16})
        cancel=Event()
        progress=[]
        def update(value):
            progress.append(value)
            if value>0:cancel.set()
        with self.assertRaises(OperationCancelled):
            estimate_psd(PSDRequest(source,segment=16,overlap=8),
                         ExecutionContext(cancel=cancel,progress=update))
        self.assertTrue(0 < progress[-1] < 100)

    def test_atomic_pipeline_commit_and_failed_session_replace(self):
        request=case()
        result=run_pipeline(request)
        project=Project()
        project.add(Signal([17]))
        before=project.document()
        cancel=Event()
        add=Project.add
        def staged_add(pending,value,**kwargs):
            key=add(pending,value,**kwargs)
            if value is result.psd:cancel.set()
            return key
        with patch.object(Project,'add',staged_add), self.assertRaises(OperationCancelled):
            store_pipeline(project,request,result,execution=ExecutionContext(cancel=cancel))
        self.assertEqual(project.document(),before)
        with TemporaryDirectory() as folder:
            path=Path(folder)/'session.json'
            session.save(path,project,session.empty_workspace())
            previous=path.read_bytes()
            store_pipeline(project,request,result)
            with patch('signallab_pc.atomic_file.os.replace',side_effect=OSError('Disco')):
                with self.assertRaises(OSError):
                    session.save(path,project,session.empty_workspace())
            self.assertEqual(path.read_bytes(),previous)
            self.assertEqual(list(Path(folder).iterdir()),[path])
