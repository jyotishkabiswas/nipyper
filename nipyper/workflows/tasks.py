import subprocess, sys
from traceback import format_exception
from subprocess import CalledProcessError

import nipype.pipeline.engine as pe
from celery import task
from celery.app import app_or_default

from nipyper.app import celery as app
from nipyper.interfaces.tasks import resolve

app = app_or_default(app)

@app.task()
def run_node(node, updatehash):
    result = dict(result=None, traceback=None)
    try:
        result['result'] = node.run(updatehash=updatehash)
    except:
        etype, eval, etr = sys.exc_info()
        result['traceback'] = format_exception(etype, eval, etr)
        result['result'] = node.result
    return result

@app.task()
def create_basedir(basedir="results", uuid=""):
    directory = basedir + '/' + uuid
    subprocess.call(['mkdir', directory])
    return directory

@app.task()
def delete_basedir(basedir="results", uuid=""):
    if not len(uuid) > 0:
        raise RuntimeError("Cannot delete results directory.")
    subprocess.call(['rm', '-rf', basedir + '/' + uuid])

@app.task()
def parse(flow, wfctxid = None):
    if 'type' not in flow:
        raise RuntimeError('The flow must have a type.')
    if 'name' not in flow:
        raise RuntimeError('A flow must specify a name.')

    wf = None
    if wfctxid != None:
        wf = pe.Workflow(wfctxid)

    if flow['type'] == 'Interface':
        if 'interface' not in flow:
            raise RuntimeError('An interface must be specified.')
        interface, isInterface = resolve(flow['interface'])
        if not isInterface or interface is None:
            raise RuntimeError('There is no Nipype interface named %s.' % flow['interface'])
        _args = []
        _kwargs = {}
        if 'args' in flow:
            if flow['args'] != None:
                _args = flow['args']
        if 'keywords' in flow:
            if flow['keywords'] != None:
                _kwargs = flow['keywords']
        iface = interface['class'](*_args, **_kwargs)
        if 'inputs' in flow:
            for name, inp in flow['inputs'].iteritems():
                setattr(iface.inputs, name, inp)
        node = pe.Node(iface, flow['name'])
        if wf != None:
            wf.add_nodes([node])
            return wf
        return node

    # TODO: deduplicate Node and MapNode logic
    if flow['type'] == 'Node':
        if 'interface' not in flow:
            raise RuntimeError('Node must have a specified interface.')
        interface, isInterface = resolve(flow['interface'])
        if not isInterface or interface is None:
            raise RuntimeError('There is no Nipype interface named %s.' % flow['interface'])
        name = flow['name'] if 'name' in flow else False
        iterables = flow['iterables'] if 'iterables' in flow else None
        itersource = flow['itersource'] if 'itersource' in flow else False
        synchronize = flow['synchronize'] if 'synchronize' in flow else None
        overwrite = flow['overwrite'] if 'overwrite' in flow else  None
        needed_outputs = flow['needed_outputs'] if 'needed_outputs' in flow else False
        _args = []
        _kwargs = {}
        if 'args' in flow:
            if flow['args'] != None:
                _args = flow['args']
        if 'keywords' in flow:
            if flow['keywords'] != None:
                _kwargs = flow['keywords']
        iface = interface['class'](*_args, **_kwargs)
        node = pe.Node(iface, name, iterables, itersource, synchronize, overwrite, needed_outputs)
        if 'inputs' in flow:
            for name, inp in flow['inputs'].iteritems():
                setattr(node.inputs, name, inp)
        if wf != None:
            wf.add_nodes([node])
            return wf
        return node

    if flow['type'] == 'MapNode':
        if 'interface' not in flow:
            raise RuntimeError('MapNode must have a specified interface.')
        if 'iterfield' not in flow:
            raise RuntimeError('MapNode must have an iterfield.')
        interface, isInterface = resolve(flow['interface'])
        if not isInterface or interface is None:
            raise RuntimeError('There is no Nipype interface named %s.' % flow['interface'])
        iterfield = flow['iterfield']
        name = flow['name'] if 'name' in flow else False
        serial = flow['serial'] if 'serial' in flow else False
        _args = []
        _kwargs = {}
        if 'args' in flow:
            if flow['args'] != None:
                _args = flow['args']
        if 'keywords' in flow:
            if flow['keywords'] != None:
                _kwargs = flow['keywords']
        iface = interface['class'](*_args, **_kwargs)
        node = pe.MapNode(iface, iterfield, name, serial)
        if 'inputs' in flow:
            for name, inp in flow['inputs'].iteritems():
                setattr(iface, name, inp)
        if wf != None:
            wf.add_nodes([node])
            return wf
        return node

    if flow['type'] == 'Workflow':
        if wf == None:
            raise RuntimeError('A name must be provided for the workflow.')
        nodes = {}
        for key, desc in flow['nodes'].iteritems():
            node = parse(desc)
            wf.add_nodes([node])
            nodes[key] = node
        for edge in flow['edges']:
            fr = nodes[edge['from']]
            to = nodes[edge['to']]
            wf.connect(fr, edge['output'], to, edge['input'])
        if 'inputs' in flow:
            for key, inp in flow['inputs'].iteritems():
                setattr(wf.inputs, key, inp)
        return wf

    raise RuntimeError('Flow type must be one of {Interface, Node, MapNode, Workflow}.')

@app.task()
def clean(wfctx):
    pass

@app.task()
def export(wf):
    return wf.export()

@app.task()
def run(wfctx, plugin = 'celery'):
    pass

@app.task()
def add_subgraph(wfctx, id):
    pass

@app.task()
def run_subgraph(wfctx, names):
    pass

@app.task()
def write_graph(wfctx, id):
    pass

@app.task()
def get_prov(wfctx, id):
    pass

@app.task()
def delete_wfctx(id):
    pass