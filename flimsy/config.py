import suite

_defaultsuite = suite.TestSuite
defaultsuite = _defaultsuite

def reset_for_module():
    global defaultsuite
    defaultsuite = _defaultsuite