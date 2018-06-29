import functools
import runner as runner_mod
import uid

class State():
    enums = '''
    NotRun
    InProgress
    Skipped
    Passed
    Failed
    '''.split()

    for idx, enum in enumerate(enums):
        locals()[enum] = idx

instances = []

class TestCase(object):
    fixtures = tuple()
    runner = runner_mod.TestRunner

    def __new__(klass, *args, **kwargs):
        obj = super(TestCase, klass).__new__(klass, *args, **kwargs)
        instances.append(obj)
        return obj

    def __init__(self, *args, **kwargs):
        if not self.fixtures:
            self.fixtures = []
        name = kwargs.pop('name', None)
        if name is not None:
            self.name = name

        self.init(*args, **kwargs)

        self.status = State.NotRun
        self.path = __file__
        self.uid = uid.uid(self)
    
    def init(self, *args, **kwargs):
        pass

# TODO Change the decorator to make this easier to create copy tests.
# Good way to do so might be return by reference.
def testfunction(f):
    testcase = TestCase(name=f.__name__)
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