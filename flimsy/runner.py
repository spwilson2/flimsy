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


class TestRunner(object):
    def __init__(self, test):
        self.test = test
    
    def run(self):
        self.pretest()
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
        for fixture in self.test.fixtures:
            fixture.setup(self.test)
        log.Log.testresult(self.test, test_mod.State.InProgress)

    def posttest(self):
        log.Log.testresult(self.test, self.test.status)
        for fixture in self.test.fixtures:
            fixture.teardown(self.test)

class SuiteRunner(object):
    def __init__(self, suite):
        self.suite = suite

    def run(self):
        self.presuite()
        for test in self.suite:
            test.runner(test).run()
        self.postsuite()

    def set_result(self):
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
                self.suite.status = test.status
                return
            passed |= test.status == test_mod.State.Passed
        if passed:
            self.suite.status = test_mod.State.Passed
        else:
            self.suite.status = test_mod.State.Skipped
        
    def presuite(self):
        # TODO Add logging for suites.
        for fixture in self.suite.fixtures:
            fixture.setup(self.suite)
        log.Log.suiteresult(self.suite, test_mod.State.InProgress)

    def postsuite(self):
        self.set_result()
        log.Log.suiteresult(self.suite, self.suite.status)
        for fixture in self.suite.fixtures:
            fixture.teardown(self.suite)