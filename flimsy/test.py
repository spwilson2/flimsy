# TODO: Enum of test states
NotRun, Passed, Failed, Skipped = range(4)
instances = []

class TestCase(object):
    def __new__(klass, *args, **kwargs):
        obj = super(TestCase, klass).__new__(klass, *args, **kwargs)
        instances.append(obj)
        return obj

    def __init__(self, *args, **kwargs):
        name = kwargs.pop('name', None)
        self.name = name
        self.init(*args, **kwargs)
        self.status = NotRun
    
    def init(self):
        pass