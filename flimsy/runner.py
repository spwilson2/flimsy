class TestRunner(object):
    def __init__(self, test):
        self.test = test
    
    def run(self):
        self.pretest()
        try:
            # TODO Sandbox the test
            # TODO Store the test results
            self.test.test()
        except:
            pass
        self.posttest()

    def pretest(self):
        pass

    def posttest(self):
        pass

class SuiteRunner(object):
    def __init__(self, suite):
        self.suite = suite

    def run(self):
        self.presuite()
        for test in self.suite:
            test.run()
        
        # TODO Store the test results
        self.postsuite()

    def presuite(self):
        pass

    def postsuite(self):
        pass
    
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