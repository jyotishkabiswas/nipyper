from flask.ext.restful import request, reqparse, abort, Resource, marshal
from nipyper.app import api, app

from .tasks import parse, create_basedir, delete_basedir
from .context import WorkflowContext

from celery import states
import uuid

from networkx.readwrite import json_graph
import json

flowParser = reqparse.RequestParser()
flowParser.add_argument('type', type=str, required=True, location='json', help='type must be one of {Interface, Node, MapNode, Workflow} (required)')
flowParser.add_argument('name', type=str, required=True, location='json', help='specify a name for the workflow (required)')
flowParser.add_argument('interface', type=str, location='json', help='specify a valid interface')
flowParser.add_argument('args', type=list, location='json', help='specify a list of positional constructor arguments')
flowParser.add_argument('keywords', type=dict, location='json', help='specify a hash of keyword constructor arguments')
flowParser.add_argument('nodes', type=list, location='json', help='specify the contained nodes')
flowParser.add_argument('edges', type=list, location='json', help='specify connections between the nodes')
flowParser.add_argument('inputs', type=dict, location='json', help='specify inputs to the flow')
if app.config['DEBUG']:
    flowParser.add_argument('__sync', type=bool, location='json', help='run the request synchronously (for debugging purposes)')

# TODO: persist context states.
workflow_contexts = {}
pending = {}

class Workflow(Resource):

    def get(self, wfctxid):
        if wfctxid in workflow_contexts:
            wfctx = workflow_contexts[wfctxid]
            out = {}
            for k, v in wfctx.result.iteritems():
                out[k] = {}
                out[k]['status'] = wfctx.get_status(k)
                if out[k]['status'] == 'SUCCESS':
                    result = v.result
                    out[k]['result'] = {}
                    res = result['result']
                    out[k]['traceback'] = result['traceback']
                    outs = res.outputs.__dict__
                    for key, val in outs.iteritems():
                        out[k]['result'][key] = val
            return out
        abort(400, message='There is no workflow context with that id')

        # result = parse.AsyncResult(wfctxid)
        # if wfctxid not in pending and result.status == states.PENDING:
        # result = pending[wtcxid] if wfctxid in pending else result
        # if result.successful():
        #     wf = result.result
        #     wfctx = WorkflowContext(wfctxid, gctimeout=3600 * 24)
        #     workflow_contexts[wfctxid] = wfctx
        #     wfctx.setWorkflow(wf)
        #     del pending[wfctxid]
        #     return wfctx.result
        # if result.failure():
        #     abort(404, message=result.traceback)

    def post(self, wfctxid = None):
        flow = flowParser.parse_args()
        print flow
        taskid = wfctxid if wfctxid is not None else uuid.v4()
        while taskid in workflow_contexts:
            if wfctxid is not None:
                abort(400, message = "Workflow with id " + wfctxid + " already exists.")
                return
            taskid = uuid.v4()
        wf = parse(flow, taskid) # fast enough to do synchronously
        wfctx = WorkflowContext(taskid, gctimeout=3600 * 24)
        wfctx.setWorkflow(wf)
        workflow_contexts[taskid] = wfctx
        return taskid

    def put(self, wfctxid):
        if wfctxid not in workflow_contexts:
            abort(400, message='There is no workflow context with that id')
        wfctx = workflow_contexts[wfctxid]
        wfctx.run()
        out = {}
        for k, v in wfctx.result.iteritems():
            out[k] = {}
            out[k]['status'] = wfctx.get_status(k)
            if out[k]['status'] == 'SUCCESS':
                out[k]['results'] = deepclone(wfctx.get_result(k).result.outputs.__dict__)
        return out

    def delete(self, wfctxid):
        if wfctxid in workflow_contexts:
            workflow_contexts[wfctxid].delete()
            del workflow_contexts[wfctxid]

class WorkflowResult(Resource):

    def get(self, wfctxid, node):
        pass

from nipyper.util import memoize

@memoize
def create_route():
    api.add_resource(Workflow, '/workflows/', endpoint = 'workflow')
    api.add_resource(Workflow, '/workflows/<string:wfctxid>', endpoint = 'context')
    api.add_resource(WorkflowResult, '/results/<string:wfctxid>/<string:node>', endpoint = 'result')

create_route()