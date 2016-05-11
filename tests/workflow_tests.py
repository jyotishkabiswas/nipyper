from time import sleep
from base import BaseWorkflowTest

from nipyper.workflows.tasks import parse
from nipyper.app import celery as app
from celery import states

from nipype.interfaces.utility import Function

class TestWorkflowContext(BaseWorkflowTest):

    def test_create(self):
        wfctx = self._initCtx("ctx0")
        self.assertTrue("ctx0" in wfctx._dir)
        wfctx.delete().get()

    def __run_block(self, wfctx):
        wfctx.run()
        self.assertFalse(wfctx.execution is None)
        status = wfctx.status
        retriesLeft = 500
        while (status != states.SUCCESS) and (status != states.FAILURE) and retriesLeft >= 0:
            sleep(0.1)
            retriesLeft -= 1
            status = wfctx.status
            print 'status:', status
        result = wfctx.result
        for k, v in result.iteritems():
            self.assertTrue(v.successful())
        return result

    def test_parse_interface(self):
        nodeDef = self._get_add_desc()
        wf = parse(nodeDef, 'add_interface')
        self.assertEqual(wf.name, 'add_interface')

    def test_parse_node(self):
        nodeDef = self._get_add_desc('Node', 'add_node')
        wf = parse(nodeDef, 'add_node')
        self.assertEqual(wf.name, 'add_node')

    def test_parse_mapnode(self):
        nodeDef = self._get_add_desc('MapNode', 'add_mapnode')
        nodeDef['iterfield'] = ['a', 'b']
        nodeDef['inputs']['a'] = [1, 3, 5]
        nodeDef['inputs']['b'] = [7, 9, 11]
        wf = parse(nodeDef, 'add_mapnode')
        self.assertEqual(wf.name, 'add_mapnode')

    def test_run_interface(self):
        nodeDef = self._get_add_desc()
        wfctx = self._initCtx('ctx1')
        wf = parse(nodeDef, wfctx.id)
        wfctx.setWorkflow(wf)
        result = self.__run_block(wfctx)
        self.assertTrue(nodeDef['name'] in result)
        result = result[nodeDef['name']].result
        self.assertTrue(result['traceback'] == None)
        self.assertEqual(result['result'].outputs.out, 12)
        wfctx.delete()

    def test_run_node(self):
        nodeDef = self._get_add_desc('Node', 'add_node')
        wfctx = self._initCtx('ctx2')
        wf = parse(nodeDef, wfctx.id)
        wfctx.setWorkflow(wf)
        result = self.__run_block(wfctx)
        self.assertTrue(nodeDef['name'] in result)
        result = result[nodeDef['name']].result
        self.assertTrue(result['traceback'] == None)
        self.assertEqual(result['result'].outputs.out, 12)
        wfctx.delete()

    def test_run_workflow(self):
        nodeDef1 = self._get_add_desc('Node', 'A')
        nodeDef2 = self._get_add_desc('Node', 'B')
        nodeDef3 = self._get_add_desc('Node', 'O')
        wfDef = {
            'type': 'Workflow',
            'name': 'add_wf',
            'nodes': {
                'A': nodeDef1,
                'B': nodeDef2,
                'O': nodeDef3
            },
            'edges': [
                {'from': 'A', 'to': 'O', 'output': 'out', 'input': 'a'},
                {'from': 'B', 'to': 'O', 'output': 'out', 'input': 'b'}
            ]
        }
        wfctx = self._initCtx('ctx3')
        wf = parse(wfDef, wfctx.id)
        wfctx.setWorkflow(wf)
        result = self.__run_block(wfctx)
        self.assertTrue('O' in result)
        result = result['O'].result
        self.assertTrue(result['traceback'] == None)
        self.assertEqual(result['result'].outputs.out, 24)
        wfctx.delete()


# class TestRunMapNode(BaseWorkflowTest):

#     def __run_block(self, wfctx):
#         wfctx.run()
#         self.assertFalse(wfctx.execution is None)
#         status = wfctx.status
#         retriesLeft = 500
#         while (status != states.SUCCESS) and (status != states.FAILURE) and retriesLeft >= 0:
#             sleep(0.1)
#             retriesLeft -= 1
#             status = wfctx.status
#             print 'status:', status
#         result = wfctx.result
#         for k, v in result.iteritems():
#             self.assertTrue(v.successful())
#         return result

#     def test_run_mapnode(self):
#         nodeDef = self._get_add_desc('MapNode', 'add_mapnode')
#         nodeDef['iterfield'] = ['a', 'b']
#         nodeDef['inputs']['a'] = [1, 3, 5]
#         nodeDef['inputs']['b'] = [7, 9, 11]
#         wfctx = self._initCtx("ctx3")
#         wf = parse(nodeDef, wfctx.id)
#         wfctx.setWorkflow(wf)
#         result = self.__run_block(wfctx)
#         wfctx.delete()

# class TestParseInterface(TestCase(methodname="create_context")):