import os
import re
import sys
import traceback

import six

import config
import suite as suite_mod
import test as test_mod
import fixture as fixture_mod

# Match filenames that either begin or end with 'test' or tests and use
# - or _ to separate additional name components.
default_filepath_regex = re.compile(r'(((.+[_])?tests?)|(tests?([-_].+)?))\.py$')

def default_filepath_filter(filepath):
    '''The default filter applied to filepaths to marks as test sources.'''
    filepath = os.path.basename(filepath)
    if default_filepath_regex.match(filepath):
        # Make sure doesn't start with .
        return not filepath.startswith('.')
    return False

def path_as_modulename(filepath):
    '''Return the given filepath as a module name.'''
    # Remove the file extention (.py)
    return os.path.splitext(os.path.basename(filepath))[0]

def path_as_suitename(filepath):
    return os.path.split(os.path.dirname(os.path.abspath((filepath))))[-1]

def _assert_files_in_same_dir(files):
    if __debug__:
        if files:
            directory = os.path.dirname(files[0])
            for f in files:
                assert os.path.dirname(f) == directory

class Loader(object):
    '''Class for discovering tests.

    To simply discover and load all tests using the default filter create an
    instance and `load_root`.

    >>> import os
    >>> tl = TestLoader()
    >>> tl.load_root(os.getcwd())

    .. note:: If tests are not manually placed in a TestSuite, they will
        automatically be placed into one for the module.
    '''
    def __init__(self):
        self.suites = []
        self.tests = []
        self.fixtures = []
        self.filepath_filter = default_filepath_filter

    def load_root(self, root):
        '''
        Load files from the given root directory which match
        `self.filepath_filter`.
        '''
        if __debug__:
            self._loaded_a_file = True

        for directory in self._discover_files(root):
            if directory:
                _assert_files_in_same_dir(directory)
                for f in directory:
                    self.load_file(f)

    def load_dir(self, directory):
        for dir_ in self._discover_files(directory):
            _assert_files_in_same_dir(dir_)
            for f in dir_:
                self.load_file(f)

    def load_file(self, path):
        path = os.path.abspath(path)

        # Create a custom dictionary for the loaded module.
        newdict = {
            '__builtins__':__builtins__,
            '__name__': path_as_modulename(path),
            '__file__': path,
        }

        # Add the file's containing directory to the system path. So it can do
        # relative imports naturally.
        old_path = sys.path[:]
        sys.path.insert(0, os.path.dirname(path))
        cwd = os.getcwd()
        os.chdir(os.path.dirname(path))

        def cleanup():
            sys.path[:] = old_path
            os.chdir(cwd)
            # TODO Rather than repeat this create a collector, use the corrector to create a __new__ function for each base we want to collect.
            # Then just call the reset on the collector.
            if test_mod.instances:
                del test_mod.instances[:]
            if suite_mod.instances:
                del suite_mod.instances[:]
            if fixture_mod.instances:
                del fixture_mod.instances[:]
            config.reset_for_module()

        try:
            execfile(path, newdict, newdict)
            #six.exec_(open(path).read(), newdict, newdict)
        except Exception as e:
            print traceback.format_exc()
            #TODO Log error.
            cleanup()
            return
    
        new_tests = test_mod.instances
        new_suites = suite_mod.instances
        new_fixtures = fixture_mod.instances

        self.tests.extend(new_tests)
        self.suites.extend(new_suites)
        self.fixtures.extend(new_fixtures)

        # Create a module test suite for those not contained in a suite.
        orphan_tests = set(new_tests)
        for suite in new_suites:
            for test in suite:
                # Remove the test if it wasn't already removed. 
                # (Suites may contain copies of tests.)
                if test in orphan_tests:
                    orphan_tests.remove(test)
        if orphan_tests:
            orphan_tests = sorted(orphan_tests, key=new_tests.index)
            # Use the config based default to group all uncollected tests.
            module_suite = config.defaultsuite(tests=orphan_tests, name=path_as_suitename(path))
            self.suites.append(module_suite)
        cleanup()

    def _discover_files(self, root):
        '''
        Recurse down from the given root directory returning a list of
        directories which contain a list of files matching
        `self.filepath_filter`.
        '''
        # Will probably want to order this traversal.
        for root, dirnames, filenames in os.walk(root):
            dirnames.sort()
            if filenames:
                filenames.sort()
                filepaths = [os.path.join(root, filename) \
                             for filename in filenames]
                filepaths = filter(self.filepath_filter, filepaths)
                if filepaths:
                    yield filepaths


class DuplicateTestItemException(Exception):
    pass
