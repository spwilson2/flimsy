import os

import config

#TODO Change into a class, will simplify logic for passing TestClass results to the log.
# (TestCases are uniquely identified by 'parent_suite.uid' and their own 'uid')
def uid(testitem, filepath, class_name=None):
    '''
    The generic function used to produce uid of test objects.

    :class:`TestSuite` objects defined within the same folder must have a unique
    name in order to be unique. :class:`TestCase` objects defined within the
    same test suite must have a unique name from all other tests in that suite.
    '''
    # Trim the file path to be the path relative to the parent of this
    # directory.
    filepath = os.path.relpath(filepath,
                               os.path.commonprefix((config.constants.testing_base,
                                                    filepath)))
    fmt = '{file}:{class_}:{name}'
    if class_name is None:
        class_name = testitem.__class__.__name__
    return fmt.format(file=filepath, name=testitem.name,
                      class_=class_name)

# FIXME: Should merge UID functions into a full blown class.
def path_from_uid(uid):
    split_path = uid.split(':')[0]
    return os.path.join(config.constants.testing_base, split_path)
