import runner as runner_mod
import test as test_mod
import uid

instances = []

class TestSuite(object):
    fixtures = tuple()
    #TODO Change to default if no runner set.
    runner = runner_mod.SuiteRunner

    def __new__(klass, *args, **kwargs):
        obj = super(TestSuite, klass).__new__(klass, *args, **kwargs)
        instances.append(obj)
        return obj

    def __init__(self, *args, **kwargs):
        name = kwargs.pop('name', None)
        if name is not None:
            self.name = name
        self.tests = kwargs.pop('tests', [])
        self.tags = set(kwargs.pop('tags', tuple()))
        self.init(*args, **kwargs)
        self.status = test_mod.State.NotRun
        self.path = __file__
        self.uid = uid.uid(self)

    def init(self, *args, **kwargs):
        pass

    def __iter__(self):
        return iter(self.tests)