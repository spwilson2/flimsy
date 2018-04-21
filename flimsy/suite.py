import runner as runner_mod

instances = []

class TestSuite(object):
    fixtures = tuple()
    runner = runner_mod.SuiteRunner

    def __new__(klass, *args, **kwargs):
        obj = super(TestSuite, klass).__new__(klass, *args, **kwargs)
        instances.append(obj)
        return obj

    def __init__(self, tests, name):
        self.name = name
        self.tests = tests
    
    def __iter__(self):
        return iter(self.tests)