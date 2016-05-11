# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""Workflow execution via Celery distributed task queue, modeleled after multiproc
"""
import sys, threading, thread
from time import sleep
from copy import deepcopy

from celery import states
from nipype.pipeline.plugins.base import DistributedPluginBase, report_crash

from nipyper.workflows.tasks import run_node

class StoppableThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self, *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self._stop = threading.Event()
        self._pause = threading.Event()

    def pause(self):
        self._pause.set()

    def resume(self):
        self._pause.clear()

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

    def paused(self):
        return self._pause.isSet()


class CeleryPlugin(DistributedPluginBase):
    """Execute workflow with Celery
    """

    def __init__(self, plugin_args=None):
        super(CeleryPlugin, self).__init__(plugin_args=plugin_args)
        # TODO load balance across celery instances on different machines
        # using machine-specific queues. This should happen on the
        # workflow-context (not node) level -- a context should not be sharded,
        # to ensure a shared filesystem.
        self._taskresult = {}
        self._nodes = {}
        self._id = plugin_args['id']
        self._execution = None
        self._started = False

        # we use threading in order to have shared state
        self.mu = threading.RLock()

    def run(self, graph, config, updatehash=False):
        """Executes a pipeline using distributed approaches
        """
        # stop any currently running tasks
        self.kill()

        this = self
        self._graph = graph
        self._count = len(graph.nodes())
        self._taskresult = {}
        for node in graph.nodes():
            self._taskresult[node.name] = None
        self._started = True
        config['execution']['poll_sleep_duration'] = 0.001

        # for now, we'll just wrap the base distributed run() implementation
        # in a thread so it can be done async.
        def __run():
            try:
                super(CeleryPlugin, this).run(graph, config, updatehash)
            except (RuntimeError, SystemExit):
                pass
        self._execution = StoppableThread(target = __run)
        self._execution.start()

    def get_status(self, name = None):
        self.mu.acquire()
        count = len(self._graph.nodes())
        result = None
        if name != None:
            if name in self._taskresult:
                result = self._taskresult[name].status
        elif not self._started:
            result = states.PENDING
        elif self._count <= 0:
            result = states.SUCCESS
        elif self._execution.isAlive():
            result = states.PENDING
        else:
            result = states.FAILURE
        self.mu.release()
        return result

    def get_result(self, name = None):
        self.mu.acquire()
        result = None
        if name == None:
            result = deepcopy(self._taskresult)
        elif name in self._taskresult:
            result = self._taskresult[name]
        self.mu.release()
        return result

    def kill(self):
        """Kill the running exection, return
        """
        if self._execution != None:
            self._execution.stop()
            self._execution.join()
        print "killed execution"

    def rerun(self, name):
        pass

    def pause(self):
        if self._execution != None:
            self._execution.pause()

    def resume(self):
        """Resume execution any running computation. No-op if none exists or already running.
        """
        if self._execution != None:
            self._execution.resume()

    def cleanup(self):
        """Delete any persisted state related to the task, and delete any results.
        """
        pass

    def _get_result(self, taskid):
        if taskid not in self._taskresult:
            raise RuntimeError('Nipype celery task %s not found' % taskid)
        self.mu.acquire()
        result = self._taskresult[taskid]
        if result.successful():
            self._count -= 1
            self.mu.release()
            return result.result
        if result.failed():
            self.mu.release()
            raise RuntimeError('Nipype celery task %s failed' % taskid)
        self.mu.release()
        return None

    def generate_task_id(self, name):
        return self._id + '-' + name

    def _submit_job(self, node, updatehash=False):
        # check if we were stopped by the parent thread
        if self._execution.stopped():
            thread.exit()

        # or paused
        while True:
            if not self._execution.paused():
                break
            sleep(0.01)

        return self.__submit(node, updatehash)

    def __submit(self, node, updatehash=False):
        try:
            if node.inputs.terminal_output == 'stream':
                node.inputs.terminal_output = 'allatonce'
        except:
            pass
        self.mu.acquire()
        result = run_node.delay(node, updatehash)
        self._taskresult[node.name] = result
        self._started = True
        self.mu.release()
        return node.name

    def _report_crash(self, node, result=None):
        if result and result['traceback']:
            node._result = result['result']
            node._traceback = result['traceback']
            return report_crash(node,
                                traceback=result['traceback'])
        else:
            return report_crash(node)

    def _clear_task(self, name):
        pass