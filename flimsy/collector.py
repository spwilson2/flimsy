class InstanceCollector(object):
    instances = []
    def __new__(typ, *args, **kwargs):
        obj = super(InstanceCollector, typ).__new__(*args, **kwargs)
        typ.instances.append(obj)
        return obj

class SuiteCollector()