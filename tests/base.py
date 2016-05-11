from unittest import TestCase
from subprocess import call, check_call

from nipyper.workflows.context import WorkflowContext

from nipyper.app import celery as app
from celery.app import app_or_default
app = app_or_default(app)

class BaseWorkflowTest(TestCase):
    def setUp(self):
        app.control.purge()
        call(['rm', '-rf', 'testresults'])
        call(['mkdir', 'testresults'])


    def _get_add_desc(self, node_type='Interface', name='add_interface'):
        fndef = """def _add(a, b):
    return a + b"""
        wfctx = self._initCtx("ctx1")
        nodeDef = {
            'name': name,
            'type': node_type,
            'interface': 'utility.Function',
            'keywords': {
                'input_names': ['a', 'b'],
                'output_names': ['out']
            },
            'inputs': {
                'function_str': fndef,
                'a': 5,
                'b': 7
            }
        }
        return nodeDef

    def _initCtx(self, uuid):
        return WorkflowContext(uuid, basedir='testresults')