from flask.ext.restful import reqparse, abort, Resource, marshal
from nipyper.app import api
from .registry import registry, interface_spec, module_spec
from .tasks import resolve
from traceback import format_exception
import sys

interfaceParser = reqparse.RequestParser()
interfaceParser.add_argument('inputs', type=dict, location='json', help='specify inputs to the interface')

class Interface(Resource):
    # decorators = [auth.login_required]

    def get(self, query = ""):
        if query == "all":
            result = {
                'interfaces': {},
                'modules': {}
            }
            for name, face in registry.interfaces.iteritems():
                result['interfaces'][name] = marshal(face, interface_spec)
            for name, mod in interfaces.modules.iteritems():
                result['modules'][name] = marshal(mod, module_spec)
            return result
        query = query.replace("/", ".")
        message = ""
        try:
            # faster to resolve synchronously rather than go through Celery
            result, isInterface = resolve(query)
            if result is None:
                message = "There is no interface or module at path '/" + query.replace(".", "/") + "'."
                abort(404, message)
            res = {}
            if isInterface:
                res['apiVersion'] = '1.0'
                res['type'] = 'interface'
                res['data'] = marshal(result, interface_spec)
                return res
            else:
                res['apiVersion'] = '1.0'
                res['type'] = 'module'
                res['data'] = marshal(result, module_spec)
                return res
        except:
            abort(400, message = message)

    def post(self, query = ""):
        from nipyper.workflows.tasks import parse
        args = interfaceParser.parse_args()
        query = query.replace("/", ".")
        message = ""
        if query not in registry.interfaces:
            abort(404, message = "There is no interface named " + query)
        normalized = {
            'type': 'Interface',
            'interface': query
        }
        if 'inputs' in parser:
            normalized['inputs'] = parser['inputs']
        result = parse.delay(normalized)
        return result.id

from nipyper.util import memoize

@memoize
def create_route():
    api.add_resource(Interface, '/interfaces/', endpoint = 'module')
    api.add_resource(Interface, '/interfaces/<string:query>/', endpoint = 'interface')
    api.add_resource(Interface, '/interfaces/<path:query>', endpoint = 'path')

create_route()