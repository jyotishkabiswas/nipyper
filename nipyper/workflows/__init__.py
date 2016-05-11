from flask.ext.restful import request, reqparse, abort, Resource, marshal
from nipyper.app import api, app

from .tasks import parse, create_basedir, delete_basedir
from .context import WorkflowContext

from celery import states
import uuid

flowParser = reqparse.RequestParser()
flowParser.add_argument('type', type=str, required=True, location='json', help='type must be one of {Interface, Node, MapNode, Workflow} (required)')
flowParser.add_argument('name', type=str, required=True, location='json', help='specify a name for the workflow (required)')
flowParser.add_argument('interface', type=str, location='json', help='specify a valid interface')
flowParser.add_argument('args', type=list, location='json', help='specify a list of positional constructor arguments')
flowParser.add_argument('args', type=dict, location='json', help='specify a hash of keyword constructor arguments')
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
            return workflow_contexts[wfctxid].get_status()
        result = parse.AsyncResult(wfctxid)
        if wfctxid not in pending and result.status == states.PENDING:
            abort(400, message='There is no workflow context with that id')
        result = pending[wtcxid] if wfctxid in pending else result
        if result.successful():
            wf = result.result
            wfctx = WorkflowContext(wfctxid, gctimeout=3600 * 24)
            workflow_contexts[wfctxid] = wfctx
            wfctx.setWorkflow(wf)
            del pending[wfctxid]
            return wfctx.get_status()
        if result.failure():
            abort(404, message=result.traceback)

    def post(self):
        flow = flowParser.parse_args()
        taskid = uuid.v4()
        while taskid in pending:
            taskid = uuid.v4()
        result = parse.apply_async((flow, taskid,), task_id=taskid)
        pending[result.task_id] = result
        return result.task_id

    def put(self, wfctxid):
        if wfctxid not in workflow_contexts:
            abort(400, message='There is no workflow context with that id')
        workflow_contexts[wfctxid].run()
        return wfctxid.status

    def delete(self, wfctxid):
        if wfctxid in workflow_contexts:
            workflow_contexts[wfctxid].delete()
        result = parse.AsyncResult(wfid)
        result.revoke()
        result.forget()

class WorkflowResult(Resource):

    def get(self, wfctxid, path):
        pass

from nipyper.util import memoize

@memoize
def create_route():
    api.add_resource(Workflow, '/workflows/', endpoint = 'workflow')
    api.add_resource(Workflow, '/workflows/<string:id>/', endpoint = 'context')

create_route()