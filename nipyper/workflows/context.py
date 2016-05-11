import os, sys, subprocess
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from process_isolation import ProcessTerminationError, IsolationContext, ClientStateError, byvalue
from .tasks import create_basedir, delete_basedir

class WorkflowContext:

    def __init__(self, uuid, basedir="results", gctimeout=-1):
        self.taskMap = {}
        self.id = uuid
        self.wf = None
        self._execution = None
        self._gc = None
        self._basedir = basedir
        self._gctimeout = gctimeout

        self._dir = create_basedir(basedir, self.id)
        self._create_context()


        self._schedule_gc(gctimeout)

    def _schedule_gc(self, timeout = 0):
        if self._gc is not None:
            self._gc.revoke()
            self._gc.forget()
        if timeout >= 0:
            self._gc = delete_basedir.apply_async((self._basedir, self.id,), countdown=timeout)
        else:
            self._gc = None
        return self._gc


    def _create_context(self):
        self._context = IsolationContext()
        self._context.ensure_started()
        # chroot jail the runner process
        try:
            self._context.client.call(os.chroot, self._dir)
        except OSError as e:
            from nipyper.app import app
            if app.config['DEBUG']:
                print "Warning: Unable to install chroot jail, running in debug mode."
                self._context.client.call(os.chdir, self._dir)
            else:
                print "Warning: Unable to install chroot jail, try running with sudo."
                raise e
        plugin = self._context.load_module('celeryplugin')
        self.runner = plugin.CeleryPlugin(plugin_args={'id': self.id})

    def setWorkflow(self, wf):
        self.wf = wf

    def connect(self, fr, output, to, inp):
        self.wf.connect(fr, output, to, inp)

    def run(self, plugin_args=None, updatehash=False, node=None):
        try:
            self._execution = self.wf.run(plugin=self.runner, plugin_args=plugin_args, updatehash=updatehash)
        except ProcessTerminationError as e:
            self._create_context()
            raise e

    @property
    def status(self):
        return self.runner.get_status()

    @property
    def result(self):
        return byvalue(self.runner.get_result())

    @property
    def execution(self):
        return self._execution


    def get_status(self, name = None):
        return self.runner.get_status(name)

    def get_result(self, name = None):
        return self.runner.get_result(name)

    def find_node(self, name):
        pass

    def delete_node(self, name):
        node = self.find_node(name)
        if node is not None:
            self.wf.delete_node(node)

    def delete(self):
        """cleans up state related to this context
        """
        try:
            # self.runner.kill()
            self._context.client.terminate()
        finally:
            subprocess.call(['rm', '-rf', self.id])
            return self._schedule_gc(0)
