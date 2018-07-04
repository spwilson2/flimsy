import traceback

import fixture
import state
import test as test_mod
import log
import sandbox

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
            self.handle_skip(e)
        except fixture.BrokenFixtureException as e:
            self.handle_broken_fixture(e)
        else:
            self.handle_run()
        finally:
            self.builder.teardown(self.testitem)
        self.handle_postbuild()

class TestParameters(object):
    def __init__(self, test):
        #TODO Pass Suite Fixtures by passing suite object.
        self.test = test
        self.log = log.TestLogWrapper(log.test_log, test)

class TestRunner(RunnerPattern):
    def handle_run(self):
        self.sandbox_test()

    def handle_prebuild(self):
        log.test_log.test_status(self.testitem, state.State.InProgress)

    def handle_postbuild(self):
        log.test_log.test_status(self.testitem, self.testitem.status)
    
    def sandbox_test(self):
        try:
            sandbox.Sandbox(self.testitem, TestParameters(self.testitem))
        except sandbox.SubprocessException as e:
            self.testitem.status = state.State.Failed
        else:
            self.testitem.status = state.State.Passed


class SuiteRunner(RunnerPattern):
    def handle_run(self):
        for test in self.testitem:
            test.runner(test).execute()
        self.testitem.status = self.compute_result()
        
    def handle_prebuild(self):
        log.test_log.suite_status(self.testitem, state.State.InProgress)

    def handle_postbuild(self):
        log.test_log.suite_status(self.testitem, self.testitem.status)

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
        for test in self.testitem.tests:
            if test.status == state.State.Failed:
                return test.status
            passed |= test.status == state.State.Passed
        if passed:
            return state.State.Passed
        else:
            return state.State.Skipped

class LibraryRunner(RunnerPattern):
    def handle_run(self):
        for suite in self.testitem.suites:
            suite.runner(suite).execute()
        self.testitem.status = state.State.Passed
    
    def handle_broken_fixture(self, broken_fixture_exception):
        exc = traceback.format_exc(e)
        msg = 'Global Fixture %s failed to build. Skipping all tests.' % e.fixture
        log.test_log.error('%s\n%s' % (exc, msg))
    
    def handle_skip(self, skip_exception):
        exc = traceback.format_exc(e)
        msg = 'Global Fixture %s raised a SkipException, skipping all tests.' % e.fixture
        log.test_log.info('%s\n%s' % (exc, msg))

    def handle_prebuild(self):
        log.test_log.library_status(self.testitem, state.State.InProgress)

    def handle_postbuild(self):
        log.test_log.library_status(self.testitem, self.testitem.status)