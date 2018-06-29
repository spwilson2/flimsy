import traceback

import test as test_mod
import log
import sandbox

class LogWrapper(object):
    def __init__(self, test):
        self.test = test
        self.__log = log.Log

    def debug(self, message):
        self._log(message, level=log.Level.Debug)
    
    def warn(self, message):
        self._log(message, level=log.Level.Warn)

    def log(self, message, level=log.Level.Info):
        self._log(message, level)

    def _log(self, message, level):
        self.__log.testmessage(self.test, message, level, log.find_caller())


class TestParameters(object):
    def __init__(self, test):
        # Fixtures
        # Log
        self.test = test
        self.log = LogWrapper(test)

class BrokenFixtureException(Exception):
    pass

class FixtureBuilder(object):
    # TODO Add logging of fixture setup/teardown
    
    def __init__(self, fixtures):
        self.fixtures = fixtures
        self.built_fixtures = []

    def setup(self, testitem):
        for fixture in self.fixtures:
            # Mark as built before, so if the build fails 
            # we still try to tear it down.
            self.built_fixtures.append(fixture)
            try:
                fixture.setup(testitem)
            except Exception as e:
                exc = traceback.format_exc()
                print(exc)
                print('Exception raised while setting up fixture for %s' % testitem)
                raise BrokenFixtureException(e)
            
    def teardown(self, testitem):
        for fixture in self.built_fixtures:
            try:
                fixture.teardown(testitem)
            except Exception:
                # TODO Log the exception, keep cleaning up.
                exc = traceback.format_exc()
                print(exc)
                print('Exception raised while tearing down fixture for %s' % testitem)


class TestRunner(object):
    def __init__(self, test):
        self.test = test
    
    def run(self):
        try:
            self.pretest()
        except BrokenFixtureException:
            self.test.status = test_mod.State.Skipped
        else:
            self.sandbox_test()
        self.posttest()

        return self.test.status
    
    def sandbox_test(self):
        try:
            sandbox.Sandbox(self.test, TestParameters(self.test))
        except sandbox.SubprocessException as e:
            self.test.status = test_mod.State.Failed
        else:
            self.test.status = test_mod.State.Passed

    def pretest(self):
        log.Log.testresult(self.test, test_mod.State.InProgress)
        self.builder = FixtureBuilder(self.test.fixtures)
        self.builder.setup(self.test)

    def posttest(self):
        log.Log.testresult(self.test, self.test.status)
        self.builder.teardown(self.test)

class SuiteRunner(object):
    def __init__(self, suite):
        self.suite = suite

    def run(self):
        try:
            self.presuite()
        except BrokenFixtureException:
            self.suite.status = test_mod.State.Skipped
        else:
            for test in self.suite:
                test.runner(test).run()
            self.suite.status = self.compute_result()
        self.postsuite()

    def compute_result(self):
        '''        
        Status of the test suite by default is:
        * Passed if all contained tests passed
        * Failed if any contained tests failed
        * Skipped if all contained tests were skipped
        * NotRun if all contained tests have not run
        * Unknown if there is one or more tests NotRun and one or more are marked  either Passed or Skipped
        '''
        passed = False
        for test in self.suite.tests:
            if test.status == test_mod.State.Failed:
                return test.status
            passed |= test.status == test_mod.State.Passed
        if passed:
            return test_mod.State.Passed
        else:
            return test_mod.State.Skipped
        
    def presuite(self):
        log.Log.suiteresult(self.suite, test_mod.State.InProgress)
        self.builder = FixtureBuilder(self.suite.fixtures)
        self.builder.setup(self.suite)

    def postsuite(self):
        log.Log.suiteresult(self.suite, self.suite.status)
        self.builder.teardown(self.suite)