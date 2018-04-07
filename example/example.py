import flimsy
import six
#################
# Test Cases
#################

# Create a parameterizable test definition
class Test(flimsy.TestCase):
    # Instead of users needing to explicitly call super().__init__, init is passed the same arguments as __init__.
    # If name is passed as a keyword argument to __init__, it will be used as the name of the test. 
    # If not, init must set the name attribute.
    def init(self, value):
        self.value = value
        if not hasattr(self, 'name'):
            self.name =  'TestPass' if value else 'TestFail'

    def test(self, test_parameters):
        assert self.value

# Create a parameterized version of the test
false_test = Test(False)
# Create another parameterized version, but supply a name rather than the parameterize's version.
true_test = Test(True, name='TestPassCustom')


# Create tests from a function, name of the function is automatically used as test name.
@flimsy.testfunction
def test_function(test_parameters):
    pass

# Create tests using non-python related applications and checking return value.
flimsy.test_application('test.sh')


#################
# Test Suites
#################

# At the most basic level, a TestSuite is just a linear collection of tests.
# Tests contained in the default TestSuite will run in the given order.
tests = [false_test, true_test]
flimsy.TestSuite(tests, name='Truth Tests')

# Tests not explicity placed into a TestSuite will automatically be grouped into a module test suite.
# The type of this default test suite can be changed
class CustomSuite(flimsy.TestSuite):
    pass
flimsy.defaultsuite = CustomSuite


# TestSuites provide an iterator interface for test runners.
# It's possible to modify the order of tests by overriding the __iter__ method::
class ReverseSuite(flimsy.TestSuite):
    def __iter__(self):
        return reversed(self.tests)

############
# Fixtures
############

# Like many test frameworks Flimsy supports the concept of fixtures.
# Fixtures are a way to perform setup and cleanup of requirements for test execution.



# Unlike some test frameworks, fixtures are all enumerated and created for their respective tests before test execution phase.
# One use case for this is to interact with build systems.
class BuildSystemFixture(flimsy.Fixture):
    targets = []
    def setup(self, testsuites):
        if not subprocess.call('make ' + ''.join(targets)):
            testsuites.skip()

flimsy.globalfixture(BuildSystemFixture)
class BuildTargetFixture(flimsy.Fixture):
    def init(self, target):
        BuildSystemFixture.targets.append(target)
        self.target = target
# In the above we create a BuildTargetFixture and a global BuildSystemTarget.
# When each BuildTargetFixture is initialized before tests begin, they add themselves to this list.
# Then, just before the first test suite begins running, the setup method of the BuildSystemFixture is executed, and all the targets are supplied to make.


# Fixtures can also skip tests if they are unable to perform the necessary initialization.
class SkipFixture(flimsy.Fixture):
    def setup(self, testitem):
        testitem.skip()

    def teardown(self, testitem):
        pass

@flimsy.usefixture(SkipFixture)
class SkippedTest(flimsy.TestCase):
    def test(self):
        assert False

##############
# Runners
##############

# To allow modification of test running logic, TestCases and TestSuites contain a runner class attribute which defines the Runner Subclass to use.
# This allows modification of test running logic.
# For example, you might wish that the test suite would fail all additional tests after a single test has failed.
# To modify the default running behavior, overrride the run method.
class IterativeRunner(flimsy.SuiteRunner):
    def run(self):
        self.presuite()
        test_iter = iter(self.suite)
        for test in test_iter:
            result = test.run()
            if result = flimsy.Failed:
                break
        for test in test_iter:
            test.result = flimsy.Failed
        self.postsuite()
class FailFastSuite(flimsy.TestSuite):
    runner = IterativeRunner


#################
# Configuration
#################
flimsy.config.defaultsuite
flimsy.config.defaultsuiterunner
flimsy.config.defaulttestrunner

flimsy.config.defaultpathfilter

# In order to collect tests items, flimsy executes the python files containing tests.
# To prevent accidental running of unrelated scripts, by default flimsy will first check files for a top level import statement from flimsy.
flimsy.config.checkforimport

###############
# Other
###############

# Perform special logic if this module is not being collected by whimsy.
# NOTE: Only tests which are instantiated in the collecting module will be collected on this pass.
if not flimsy.collecting == __name__:
    six.print_('This module is not currently being collected, but it was imported.')



# Test Phases:
# * Test Collection
# * Test Parameterization
# * Fixture Parameterization
# * Global Fixture Setup
# * Iteratevely run suites:
#    * Suite Fixture Setup
#    * Iteratively run tests:
#       * Test Fixture Setup
#       * Run Test
#       * Test Fixture Teardown
#    * Suite Fixture Teardown
# * Global Fixture Teardown