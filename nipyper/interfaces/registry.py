import sys, inspect, pkgutil
import nipype
from nipype.interfaces.traits_extension import Undefined

from flask.ext.restful import fields

interface_spec = {
    # 'apiVersion': fields.String,
    'type': fields.String,
    'name': fields.String,
    'module': fields.String,
    'inputs': fields.Raw,
    'outputs': fields.Raw,
    'argspec': fields.Raw
}

module_spec = {
    # 'apiVersion': fields.String,
    'type': fields.String,
    'name': fields.String,
    'interfaces': fields.Raw,
    'submodules': fields.Raw
}

total_spec = {
    # 'apiVersion': fields.String,
    'interfaces': fields.Raw,
    'modules': fields.Raw
}

class InterfaceRegistry:

    interfaces = {}
    modules = {}

    def __init__(self):
        self.__populate()

    def __resolveModuleMembers(self, module):
        """Grabs all subclasses of Interface from the module add addes them to the registry."""

        cleaned = self.__cleanModuleName(module.__name__)

        if cleaned in self.modules:
            return

        self.modules[cleaned] = {
            'name': cleaned,
            'interfaces': [],
            'submodules': []
        }

        parent = cleaned.split(".")
        parent.pop(len(parent) - 1)
        parent = ".".join(parent)

        if parent not in self.modules:
            self.__resolveModuleMembers(sys.modules["nipype.interfaces." + parent])
        if parent != cleaned and cleaned not in self.modules[parent]['submodules']:
            self.modules[parent]['submodules'].append(cleaned)


        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and issubclass(obj, nipype.interfaces.base.Interface):
                submodule = self.__cleanModuleName(obj.__module__)
                if submodule != cleaned:
                    self.__resolveModuleMembers(sys.modules[obj.__module__])
                    continue

                fullname = submodule + "." + obj.__name__
                if (fullname in self.interfaces):
                    continue

                self.modules[submodule]['interfaces'].append(fullname)

                # instance = obj()

                in_spec = obj.input_spec() if obj.input_spec is not None else None
                out_spec = obj.output_spec() if obj.output_spec is not None else None

                in_def = {}

                if in_spec is not None:
                    for name, value in sorted(in_spec.trait_get().items()):
                        in_def[name] = value if value is not Undefined else None

                out_def = {}

                if out_spec is not None:
                    for name, value in sorted(out_spec.trait_get().items()):
                        out_def[name] = value if value is not Undefined else None

                argspec = inspect.getargspec(obj.__init__)

                self.interfaces[fullname] = {
                    'class': obj,
                    'name': obj.__name__,
                    'module': self.__cleanModuleName(obj.__module__),
                    'inputs': in_def,
                    'outputs': out_def,
                    'argspec': {
                        'args': argspec.args,
                        'varargs': argspec.varargs,
                        'keywords': argspec.keywords,
                        'defaults': argspec.defaults
                    }
                }


    def __populate(self, baseModule = 'nipype.interfaces', visited = set()):
        """Recursively searches nipype.interfaces to populate the registry."""
        try:
            module = sys.modules[baseModule]
            path = module.__path__

            # print(baseModule, path)

            self.__resolveModuleMembers(module)

            # recursively search submodules
            for obj in pkgutil.walk_packages(path):
                # print obj
                fullname = baseModule + "." + obj[1]
                k = 'module:' + fullname
                if (k in visited):
                    continue
                visited.add(k)
                if not obj[2]:
                    self.__resolveModuleMembers(sys.modules[fullname])
                else:
                    self.__populate(fullname, visited)

                cleaned = self.__cleanModuleName(fullname)
                self.__checkRemoveModule(cleaned)

            self.__checkRemoveModule(self.__cleanModuleName(baseModule))

        except KeyError:
            __import__(baseModule)
            self.__populate(baseModule, visited)

    def __checkRemoveModule(self, name):
        if len(self.modules[name]['interfaces']) == 0 and len(self.modules[name]['submodules']) == 0:
            self.modules.pop(name, None)
            parent = name.split(".")
            parent.pop(len(parent) - 1)
            parent = ".".join(parent)
            if parent != name and parent in self.modules:
                self.modules[parent]['submodules'].remove(name)

    def __cleanModuleName(self, module, prefix = "nipype.interfaces"):
        if module == prefix:
            return ""
        elif prefix in module:
            return module[len(prefix + "."):]
        return module

    def resolveModule(self, module = ""):
        module = self.__cleanModuleName(module)
        if module not in self.modules:
            return None
        return self.modules[module]

    def resolveInterface(self, name):
        resolved = self.__cleanModuleName(name)
        if resolved not in self.interfaces:
            return None
        return self.interfaces[resolved]

    def resolve(self, query):
        result = self.resolveInterface(query)
        if result is not None:
            return result, True
        result = self.resolveModule(query)
        if result is not None:
            return result, False
        return None, False


registry = InterfaceRegistry()

if __name__ == '__main__':
    # print filter(lambda k: 'nipype.interfaces' in k, sys.modules.keys())
    print registry.list()