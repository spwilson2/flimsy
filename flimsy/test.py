import functools
import runner as runner_mod

# TODO: Enum of test states
NotRun, Passed, Failed, Skipped = range(4)
instances = []

class TestCase(object):
    fixtures = tuple()
    runner = runner_mod.TestRunner

    def __new__(klass, *args, **kwargs):
        obj = super(TestCase, klass).__new__(klass, *args, **kwargs)
        instances.append(obj)
        return obj

    def __init__(self, *args, **kwargs):
        name = kwargs.pop('name', None)
        if name is not None:
            self.name = name
        self.init(*args, **kwargs)
        self.status = NotRun
    
    def init(self):
        pass

def testfunction(f):
    testcase = TestCase(name=f.__name__)
    # TODO/FIXME How to eat the self argument??
    testcase.test = f
    return f

class TestApplication(TestCase):
    def init(self, filename):
        # TODO Save current file being loaded path in order to properly resolve the filename path.
        self.filename = filename
    
    def test(self, test_parameters):
        #TODO
        pass

def test_application(name, filename):
    return TestApplication(filename, name=name)