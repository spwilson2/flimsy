import runner as runner_mod
import test as test_mod

instances = []

class TestSuite(object):
    fixtures = tuple()
    #TODO Change to default if no runner set.
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



    @property
    def status(self):
        # Status of the test suite by default is:
        # * Passed if all contained tests passed
        # * Failed if any contained tests failed
        # * Skipped if all contained tests were skipped
        # * NotRun if all contained tests have not run
        # * Unknown if there is one or more tests NotRun and one or more are marked  either Passed or Skipped

        all()
        #TODO Aggregate the results.
        return test_mod.NotRun