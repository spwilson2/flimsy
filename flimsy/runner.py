import test as test_mod

import sandbox
# TODO Create process wrapper for collecting exceptions/status


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
            sandbox.Sandbox(self.test.test, args=(None,))
        except sandbox.SubprocessException:
            self.test.status = test_mod.Failed
        else:
            self.test.status = test_mod.Passed

    def pretest(self):
        for fixture in self.test.fixtures:
            fixture.setup(self.test)
        print '\tRunning Test: %s' % self.test.name

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
        
        # TODO Store the test results
        self.postsuite()

    def presuite(self):
        for fixture in self.suite.fixtures:
            fixture.setup(self.suite)
        print 'Running Suite: %s' % self.suite.name

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