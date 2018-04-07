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

#print flimsy.TestCase.instances