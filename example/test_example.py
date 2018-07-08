import flimsy
import six

import pdb
#################
# Test Cases
#################

# Create a parameterizable test definition
class Test(flimsy.TestCase):
    # Instead of users needing to explicitly call super().__init__, init is passed the same arguments as __init__.
    # If name is passed as a keyword argument to __init__, it will be used as the name of the test. 
    # If not, the test will take the name of the class.
    def init(self, value):
        self.value = value
        if self.name == 'Test':
            self.name = 'TestPass' if value else 'TestFail'

    def test(self, test_parameters):
        assert self.value

# Create a parameterized version of the test
false_test = Test(False)
# Create another parameterized version, but supply a name rather than the parameterized's version default.
true_test = Test(True, name='TestPassCustom')


# Create tests from a function, name of the function is automatically used as test name.
@flimsy.testfunction
def test_function(test_parameters):
    print 'In test function'
    pass

# Create tests using non-python related applications and checking return value.
flimsy.test_application('Script Test', 'test.sh')

#################
# Test Suites
#################

# At the most basic level, a TestSuite is just a linear collection of tests.
# Tests contained in the default TestSuite will run in the given order.
tests = [false_test, true_test, Test(False, name='2')]
flimsy.TestSuite(tests=tests, name='Truth Tests')

# Tests not explicity placed into a TestSuite will automatically be grouped into a test suite autogenerated for the module.
# The type of this default test suite can be changed for the current module.
class CustomSuite(flimsy.TestSuite):
    pass
flimsy.config.defaultsuite = CustomSuite


# TestSuites provide an iterator interface for test runners.
# It's possible to modify the order of tests by overriding the __iter__ method::
class ReverseSuite(flimsy.TestSuite):
    def __iter__(self):
        return reversed(self.tests)
ReverseSuite(tests=tests, name='Reversed Truth Tests')

############
# Fixtures
############

# Like many test frameworks Flimsy supports the concept of fixtures.
# Fixtures are a way to perform setup and cleanup of requirements for test execution.
# They also are useful for parameterizing tests and carrying state between tests within a TestSuite.


# For example, say we have a test which stores some state in a temporary file, and the next test needs to accees that state.
class TempfileFixture(flimsy.Fixture):
    def setup(self, testitem):
        import tempfile
        self.file_ = tempfile.TemporaryFile()
    def teardown(self, testitem):
        self.file_.close()

suite = flimsy.TestSuite(name='Tempfile Test Suite', fixtures=[TempfileFixture()])

class WriteTempTest(flimsy.TestCase):
    def test(self, test_parameters):
        tempfile_fixture = test_parameters.suite.fixtures[0]
        tempfile_fixture.file_.write('hello')
        tempfile_fixture.file_.flush()

class ReadTempTest(flimsy.TestCase):
    def test(self, test_parameters):
        tempfile_fixture = test_parameters.suite.fixtures[0]
        tempfile_fixture.file_.seek(0, 0)
        assert 'hello' == tempfile_fixture.file_.read()

suite.tests.append(WriteTempTest())
suite.tests.append(ReadTempTest())

# Unlike some test frameworks, fixtures are enumerated and initialized in two steps.
# After all tests files have been enumerated and all tests have been parameterized, fixtures for each test scheduled to run will be notified of the test schedule by having their `schedule_finalized` method called.
# Then the test execution phase begins. 
# Before each test item is executed the associated fixture will be setup(), and after the test, teardown() will be called.
# This two phase approach is particularly useful for interacting with build systems or any time a fixture needs to know of all other fixtures or scheduled tests.
class BuildSystemFixture(flimsy.Fixture):
    targets = []
    def setup(self, testitem):
        import subprocess
        if subprocess.call('make ' + ''.join(self.targets), shell='/bin/bash'):
            self.skip(testitem)

#flimsy.globalfixture(BuildSystemFixture(name='Make Build System'))
class BuildTargetFixture(flimsy.Fixture):
    def init(self, target):
        BuildSystemFixture.targets.append(target)
        self.target = target
# In the above we create a BuildTargetFixture and a global BuildSystemTarget.
# When each BuildTargetFixture is initialized before tests begin, they add themselves to this list.
# Then, just before the first test suite begins running, the setup method of the BuildSystemFixture is executed, and all the targets are supplied to make.


# Fixtures can also skip tests if they are unable to perform the necessary initialization.
class SkipFixture(flimsy.Fixture):
    name = 'Test Skipper'
    def setup(self, testitem):
        testitem.skip()

    def teardown(self, testitem):
        pass

class SkippedTest(flimsy.TestCase):
    fixtures = [SkipFixture()]
    def test(self):
        assert False

##############
# Runners
##############

# For more advanced test writers flimsy enables modification of test running logic.
# TestCases and TestSuites contain a runner class attribute which defines the Runner subclass to use.
# As an example, you might wish that the test suite would fail all additional tests after a single test has failed.
# To modify the default running behavior, overrride the run method.
class IterativeRunner(flimsy.SuiteRunner):
    def handle_run(self):
        test_iter = iter(self.testitem)
        for test in test_iter:
            result = test.runner(test, self.suite).execute()
            if result == flimsy.State.Failed:
                flimsy.log.test_log.message(
                    'Test "%s" failed, skipping' 
                    ' remaining tests in suite' % test.name)
                break
        for test in test_iter:
            # TODO Simplify this interface? Idk this is pretty deep into the library,
            # it's probably not likely for users to modify behavior at this level. 
            test.result = flimsy.State.Skipped
            flimsy.log.test_log.test_status(test, test.result)

class FailFastSuite(flimsy.TestSuite):
    runner = IterativeRunner

FailFastSuite(tests=tests, name='Fail Fast Test Suite')


#################
# Logging
#################

# Flimsy uses a single common log to offer a single point of contact for gathering test status, output, and debug messages.
# This log is thread safe and allows for multiple consumers of information.

# As a convenience, the test_parameters object contains a log accessor to log messages at a given level and automatically attach the test scope.
# To write a debug message to the log during a test::
@flimsy.testfunction
def debug_message_test(test_parameters):
    test_parameters.log.debug('This is a debug message')
    test_parameters.log.warn('This is a warning message')

# The log will also automatically capture print statements, so we could just have easily used the print function.
# However, print statements are considered Stdout rather than a LogMessage type.
# This distiction makes more sense once we introduce the verbosity and stream flags.
# To increase log message output verbosity supply the '-v' flag.
# Each additional flag will increase the verbosity level to a cap.
# Increasing the verbosity level however will not cause test stdout or stderr output to display.
# To enable output of test stdout and stderr, supply the '-s' flag.
# Now all terminal output will be directed to their respective streams as tests are executed.


#TODO
# #################
# # Configuration
# #################
# flimsy.config.defaultsuite
# flimsy.config.defaultsuiterunner
# flimsy.config.defaulttestrunner

# flimsy.config.defaultpathfilter

# # In order to collect tests items, flimsy executes the python files containing tests.
# # To prevent accidental running of unrelated scripts, by default flimsy will first check files for a top level import statement from flimsy.
# flimsy.config.checkforimport

# TODO
# ###############
# # Other
# ###############

# # Perform special logic if this module is not being collected by whimsy.
# # NOTE: Only tests which are instantiated in the collecting module will be collected on this pass.
# if not flimsy.collecting == __name__:
#     six.print_('This module is not currently being collected, but it was imported.')

# # Test Phases:
# # * Test Collection
# # * Test Parameterization
# # * Fixture Parameterization
# # * Global Fixture Setup
# # * Iteratevely run suites:
# #    * Suite Fixture Setup
# #    * Iteratively run tests:
# #       * Test Fixture Setup
# #       * Run Test
# #       * Test Fixture Teardown
# #    * Suite Fixture Teardown
# # * Global Fixture Teardown

#################
# Usage
#################

# Once your tests have been created you probably will want to run them!
# To do so, use the `run`` subcommand like so::
#   flimsy run [directory]
# This will run all test at the given directory, if no directory is provided, 
# the CWD will be used as the directory argument.
#
#

# You can limit the selection of test suites run by supplying the `--exclude-tags|--include-tags <tag-query>` flag.
#
# Say you have the following test suites and you wish to only run suites tagged for the X86 architecture.
x86_suite = flimsy.TestSuite(tests=[Test(True, name='X86Test')], name='X86 Test Suite', tags=['X86'])
arm64_suite = flimsy.TestSuite(tests=[Test(True, name='ARM64Test')], name='ARM64 Test Suite', tags=['ARM64'])

# To do so, execute the run subcommand as follows::
# flimsy run --include-tags X86
#
#
# A note on tags: 
# Some might ask why tests do not have the tags attribute as well.
#
# The reason behind this goes back to flimsy's definition of TestCase and TestSuite.
# A TestSuite is defined as an inseperable collection of tests.
# If TestCases could also be tagged and filtered in the same manner as TestSuites then it would be difficult if not impossible to define consistent behavior for test execution.
# Would the tests in the test suite still run in the same order? 
# Should the test suite containing the test just be ignored?
#
# In order to keep a simpler and consistent interface, flimsy decides to only enable tags at the TestSuite level.

#########################
# Listing Available Tests
#########################

# Using the `x86_suite` and `arm64_suite` created above we can also try out listing test suites.
#
# To query available tests without running them, use the `list` subcommand with the `--tags` flag just as you would when running::
#   flimsy list --include-tags X86
#
# This will output a list of all test suites tagged with `X86`.