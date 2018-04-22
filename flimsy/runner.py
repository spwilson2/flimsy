import test as test_mod
import log

import sandbox

class LogWrapper(object):
    def __init__(self, test):
        self.test = test
        self.__log = log.Log

    def debug(self, message):
        self._log(message, level=log.Debug)
    
    def warn(self, message):
        self._log(message, level=log.Warn)

    def log(self, message, level=log.Info):
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
            self.test.status = test_mod.Failed
        else:
            self.test.status = test_mod.Passed
        log.Log.result(self.test, self.test.status)

    def pretest(self):
        for fixture in self.test.fixtures:
            fixture.setup(self.test)
        log.Log.message('\tRunning Test: %s' % self.test.name)

    def posttest(self):
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

    def presuite(self):
        for fixture in self.suite.fixtures:
            fixture.setup(self.suite)
        log.Log.message('Running Suite: %s' % self.suite.name, log.Trace)

    def postsuite(self):
        for fixture in self.suite.fixtures:
            fixture.teardown(self.suite)
    
    # Custom running interface?
    # Information need to know to implement failfast:
    # - This test suite
    # - Previous test result
    # - Next test
    # Needs to provide:
    # - Next test to run instead? 
    #   No, can just mark each test as failed until next test is ok.
    #   Instead needs to be able to mark a test state without actually executing test code.

    # Information need to know to implement partial failfast:
    # (Skipping should only be )