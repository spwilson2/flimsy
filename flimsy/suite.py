
import helper
import runner as runner_mod
import state
import test as test_mod
import uid

instances = []

class TestSuiteMetadata():
    def __init__(self, name, uid, tags, path, status):
        self.name = name
        self.uid = uid
        self.tags = tags
        self.path = path
        self.status = status

class TestSuite(object):
    #TODO Change to default if no runner set.
    runner = runner_mod.SuiteRunner
    collector = helper.InstanceCollector()

    def __new__(klass, *args, **kwargs):
        obj = super(TestSuite, klass).__new__(klass, *args, **kwargs)
        TestSuite.collector.collect(obj)
        return obj

    def __init__(self, *args, **kwargs):
        name = kwargs.pop('name', None)
        if name is not None:
            self.name = name
        self.fixtures = kwargs.pop('fixtures', [])
        self.tests = kwargs.pop('tests', [])
        self.tags = set(kwargs.pop('tags', tuple()))
        self.status = state.State.NotRun
        self.path = __file__

        self.init(*args, **kwargs)
        self.uid = uid.uid(self)

    @property
    def metadata(self):
        return TestSuiteMetadata( **{
            'name': self.name,
            'tags': self.tags,
            'status': self.status,
            'path': self.path,
            'uid': self.uid
        })

    def init(self, *args, **kwargs):
        pass

    def __iter__(self):
        return iter(self.tests)