import os
import pickle

from config import config

def _create_uid_index(iterable):
    index = {}
    for item in iterable:
        assert item.uid not in index
        index[item.uid] = item
    return index


class _CommonMetadataMixin:
    @property
    def uid(self):
        return self._metadata.uid
    @property
    def result(self):
        return self._metadata.status
    @result.setter
    def result(self, result):
        self._metadata.status = result


class InternalTestResult(object, _CommonMetadataMixin):
    def __init__(self, metadata, suite, directory):
        self._metadata = metadata
        self.suite = suite
    
        self.stderr = os.path.join(
            InternalSavedResults.output_path(self.uid, suite.uid),
            'stderr'
        )
        self.stdout = os.path.join(
            InternalSavedResults.output_path(self.uid, suite.uid),
            'stdout'
        )


class InternalSuiteResult(object, _CommonMetadataMixin):
    def __init__(self, metadata, directory):
        self._metadata = metadata
        self.directory = directory
        self._wrap_tests()
    
    def _wrap_tests(self):
        self._tests = [InternalTestResult(test, self, self.directory) 
                       for test in self._metadata.tests]
        del self._metadata.tests
        self._tests_index = _create_uid_index(self._tests)
    
    def get_test(self, uid):
        return self._tests_index[uid]
    
    def __iter__(self):
        return iter(self._tests)

    def get_test_result(self, uid):
        return self.get_test(uid)


class InternalLibraryResults(object, _CommonMetadataMixin):
    def __init__(self, metadata, directory):
        self.directory = directory
        self._metadata = metadata
        self._wrap_suites()

    def _wrap_suites(self):
        self._suites = [InternalSuiteResult(suite, self.directory) 
                        for suite in self._metadata.suites]
        del self._metadata.suites
        self._suites_index = _create_uid_index(self._suites)
    
    def add_suite(self, suite):
        if suite.uid in self._suites:
            raise ValueError('Cannot have duplicate suite UIDs.')
        self._suites[suite.uid] = suite
    
    def get_suite_result(self, suite_uid):
        return self._suites_index[suite_uid]

    def get_test_result(self, test_uid, suite_uid):
        return self.get_suite_result(suite_uid).get_test_result(test_uid)


class InternalSavedResults():
    @staticmethod
    def output_path(test_uid, suite_uid, base=None):
        '''
        Return the path which results for a specific test case should be
        stored.
        '''
        if base is None:
            base = config.result_path
        return os.path.join(
                base,
                suite_uid.replace(os.path.sep, '-'), 
                test_uid.replace(os.path.sep, '-'))

    @staticmethod
    def save(results, path, protocol=pickle.HIGHEST_PROTOCOL):
        with open(path, 'w') as f:
            pickle.dump(results, f, protocol)

    @staticmethod
    def load(path):
        with open(path, 'w') as f:
            return pickle.load(f)