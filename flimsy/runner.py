import traceback

import fixture
import state
import test as test_mod
import log
import sandbox

def compute_aggregate_result(iterable):
    '''        
    Status of the test suite by default is:
    * Passed if all contained tests passed
    * Failed if any contained tests failed
    * Skipped if all contained tests were skipped
    * NotRun if all contained tests have not run
    * Unknown if there is one or more tests NotRun and one or more are marked  either Passed or Skipped
    '''
    passed = False
    for testitem in iterable:
        if testitem.status == state.State.Failed:
            return testitem.status
        passed |= testitem.status == state.State.Passed
    if passed:
        return state.State.Passed
    else:
        return state.State.Skipped

class RunnerPattern(object):
    def __init__(self, testitem):
        self.testitem = testitem
        self.builder = fixture.FixtureBuilder(testitem.fixtures)
    
    def handle_run(self):
        pass
    
    def handle_broken_fixture(self, broken_fixture_exception):
        pass
    
    def handle_skip(self, skip_exception):
        pass
    
    def handle_postbuild(self):
        pass

    def handle_prebuild(self):
        pass
    
    def execute(self):
        self.handle_prebuild()
        try:
            self.builder.setup(self.testitem)
        except fixture.SkipException as e:
            self.testitem.status = state.State.Skipped
            self.handle_skip(e)
        except fixture.BrokenFixtureException as e:
            self.testitem.status = state.State.Skipped
            self.handle_broken_fixture(e)
        else:
            self.handle_run()
        finally:
            self.builder.teardown(self.testitem)
        self.handle_postbuild()

class TestParameters(object):
    def __init__(self, test, suite):
        self.test = test
        self.suite = suite
        self.log = log.TestLogWrapper(log.test_log, test, suite)

class TestRunner(RunnerPattern):
    def __init__(self, test, suite):
        RunnerPattern.__init__(self, test)
        self.suite = suite
        self.test = test

    def handle_run(self):
        self.sandbox_test()

    def handle_prebuild(self):
        log.test_log.test_status(self.test, self.suite, state.State.InProgress)

    def handle_postbuild(self):
        log.test_log.test_status(self.test, self.suite, self.test.status)

    def sandbox_test(self):
        try:
            sandbox.Sandbox(TestParameters(self.test, self.suite))
        except sandbox.SubprocessException as e:
            self.test.status = state.State.Failed
        else:
            self.test.status = state.State.Passed


class SuiteRunner(RunnerPattern):
    def __init__(self, suite):
        RunnerPattern.__init__(self, suite)
        self.suite = suite

    def handle_run(self):
        for test in self.suite:
            test.runner(test=test, suite=self.suite).execute()
        self.suite.status = compute_aggregate_result(
                iter(self.suite)
        )

    def handle_prebuild(self):
        log.test_log.suite_status(self.suite, state.State.InProgress)

    def handle_postbuild(self):
        log.test_log.suite_status(self.suite, self.suite.status)

class LibraryRunner(RunnerPattern):
    def handle_run(self):
        for suite in self.testitem.suites:
            suite.runner(suite).execute()
        self.testitem.status = compute_aggregate_result(
                iter(self.testitem)
        )

    def handle_broken_fixture(self, broken_fixture_exception):
        exc = traceback.format_exc(broken_fixture_exception)
        msg = ('Global Fixture %s failed to build. Skipping all tests.' % 
                broken_fixture_exception.fixture)
        log.test_log.error('%s\n%s' % (exc, msg))
    
    def handle_skip(self, skip_exception):
        exc = traceback.format_exc(skip_exception)
        msg = ('Global Fixture %s raised a SkipException, skipping all tests.' 
                % skip_exception.fixture)
        log.test_log.info('%s\n%s' % (exc, msg))

    def handle_prebuild(self):
        log.test_log.library_status(self.testitem, state.State.InProgress)

    def handle_postbuild(self):
        log.test_log.library_status(self.testitem, self.testitem.status)