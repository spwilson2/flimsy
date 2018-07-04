from __future__ import print_function
import os 
import sys
import time
import terminal
import Queue

import threading
import multiprocessing

class LogLevel():
    Fatal = 0
    Error = 1
    Warn  = 2
    Info  = 3
    Debug = 4
    Trace = 5

# Record Type - 
# Uses static rather than typeinfo so idenifiers can be used across processes/networks.
class RecordTypeCounterMetaclass(type):
    counter = 0
    def __init__(cls, name, bases, dct):
        cls.type_id = RecordTypeCounterMetaclass.counter
        RecordTypeCounterMetaclass.counter += 1

class Record(object):
    __metaclass__ = RecordTypeCounterMetaclass

    def __init__(self, data, **metadata):
        self.data = data
        self.metadata = metadata

    def __str__(self):
        return str(self.data)

class VerbosityRecordMixin():
    @property
    def level(self):
        return self.metadata['level']

class StatusRecordMixin:
    @property
    def status(self):
        return self.data
    @property
    def uid(self):
        return self.metadata['metadata'].uid
    @property
    def name(self):
        return self.metadata['metadata'].name

class TestStatus(Record, StatusRecordMixin):
    pass

class TestStderr(Record, StatusRecordMixin):
    pass

class TestStdout(Record, StatusRecordMixin):
    pass

class TestMessage(Record, VerbosityRecordMixin):
    pass

class SuiteStatus(Record, StatusRecordMixin):
    pass

class LibraryMessage(Record, VerbosityRecordMixin):
    pass

# next bit filched from 1.5.2's inspect.py
def currentframe():
    """Return the frame object for the caller's stack frame."""
    try:
        raise Exception
    except:
        return sys.exc_info()[2].tb_frame.f_back

if hasattr(sys, '_getframe'): currentframe = lambda: sys._getframe(3)
# done filching
#
# _srcfile is used when walking the stack to check when we've got the first
# caller stack frame.
#
_srcfile = os.path.normcase(currentframe.__code__.co_filename)

def find_caller():
    '''        
    Find the stack frame of the caller so that we can note the source
    file name, line number and function name.
    
    .. note:  
        From the cpython 2.7 source
        Copyright (C) 2001-2014 Vinay Sajip. All Rights Reserved.
    '''
    f = currentframe()
    #On some versions of IronPython, currentframe() returns None if
    #IronPython isn't run with -X:Frames.
    if f is not None:
        f = f.f_back
    rv = "(unknown file)", 0, "(unknown function)"
    while hasattr(f, "f_code"):
        co = f.f_code
        filename = os.path.normcase(co.co_filename)
        if filename == _srcfile:
            f = f.f_back
            continue
        
        rv = (co.co_filename, f.f_lineno, co.co_name)
        break
    return rv

def _append_dictlist(dict_, key, value):
    list_ = dict_.get(key, [])
    list_.append(value)
    dict_[key] = list

class RecordFilter(object):
    def __init__(self):
        # A key-value tuple which indicates a metadata 
        # pair to apply this filter on.
        self._metadata_match = None
    
    @property
    def metadata_match(self):
        return self._metadata_match
    
    def accept(self, record):
        return True

class FilterContainer(object):
    def __init__(self):
        self.filters = []
        self._frozen = False
    
    def freeze(self):
        if self._frozen:
            raise Exception('FilterContainer cannot be frozen more than once')

        self._frozen = True
        unqualified_filters = []
        qualified_filters = {}

        for f in self.filters:
            if f.metadata_match is None:
                unqualified_filters.append(f)
            else:
                _append_dictlist(qualified_filters, f.metadata_match, f)
        
        self.qualified_filters = qualified_filters
        self.unqualified_filters = tuple(unqualified_filters)
    
    def add_filter(self, record_filter):
        if self._frozen:
            raise Exception('Cannot add filter once log is frozen.')
        self.filters.append(record_filter)

    def remove_filter(self, record_filter):
        if self._frozen:
            raise Exception('Cannot remove filter once log is frozen.')

    def accept(self, record):
        if not self._frozen:
            raise Exception('Cannot apply filters before log is frozen.')
        
        for key in record.metadata:
            filters = self.qualified_filters.get(key, tuple())
            for f in filters:
                if not f.accept(record):
                    return False
        
        for f in self.unqualified_filters:
            if not f.accept(record):
                return False

        return True

class Log(object):
    def __init__(self):
        self.filter_container = FilterContainer()
        self.handlers = []
        self._opened = False # TODO Guards to methods
        self._closed = False # TODO Guards to methods

    def finish_init(self):
        self.filter_container.freeze()
        self._opened = True

    def close(self):
        self._closed = True
        for handler in self.handlers:
            handler.close()

    def log(self, record):
        if not self._opened:
            self.finish_init()

        if not self._accept(record):
            return

        map(lambda handler:handler.prehandle(), self.handlers)
        for handler in self.handlers:
            handler.handle(record)
            handler.posthandle()

    def _accept(self, record):
        return self.filter_container.accept(record)

    def add_handler(self, handler):
        self.handlers.append(handler)
    
    def close_handler(self, handler):
        handler.close()
        self.handlers.remove(handler)

    def add_filter(self, filter):
        self.filter_container.add_filter(filter)
    
    def remove_filter(self, filter):
        self.filter_container.remove_filter(filter)
    
    def get_filters(self):
        return tuple(self.filter_container.filters)

class Handler(object):
    def __init__(self):
        pass
    
    def handle(self, record):
        pass
    
    def close(self):
        pass

    def prehandle(self):
        pass
    
    def posthandle(self):
        pass

class LogWrapper(object):
    def __init__(self, log):
        self.log_obj = log
    
    def log(self, *args, **kwargs):
        self.log_obj.log(*args, **kwargs)

    # Library Logging Methods
    # TODO Replace these methods in a test/create a wrapper?
    # That way they still can log like this it's just hidden that they capture the current test.
    def message(self, message, level=LogLevel.Info):
        self.log_obj.log(LibraryMessage(message, level=level))
    
    def error(self, message):
        self.message(message, LogLevel.Error)

    def warn(self, message):
        self.message(message, LogLevel.Warn)

    def info(self, message):
        self.message(message, LogLevel.Info)

    def debug(self, message):
        self.message(message, LogLevel.Debug)

    def trace(self, message):
        self.message(message, LogLevel.Trace)

    # Ongoing Test Logging Methods
    def test_stdout(self, test, buf):
        self.log_obj.log(TestStdout(buf, metadata=test.metadata))

    def test_stderr(self, test, buf):
        self.log_obj.log(TestStderr(buf, metadata=test.metadata))

    def test_message(self, test, message, level):
        self.log_obj.log(TestMessage(message, uid=test.uid, level=level))

    def test_status(self, test, status):
        self.log_obj.log(TestStatus(status, metadata=test.metadata))
    
    def suite_status(self, suite, status):
        self.log_obj.log(SuiteStatus(status, metadata=suite.metadata))

    def close(self):
        self.log_obj.close()

class TestLogWrapper(object):
    def __init__(self, log, test):
        self.log_obj = log
        self.test = test

    def test_message(self, message, level):
        #trace = find_caller()
        self.log_obj.test_message(self.test, message, level)

    def error(self, message):
        self.test_message(message, LogLevel.Error)

    def warn(self, message):
        self.test_message(message, LogLevel.Warn)

    def info(self, message):
        self.test_message(message, LogLevel.Info)

    def debug(self, message):
        self.test_message(message, LogLevel.Debug)

    def trace(self, message):
        self.test_message(message, LogLevel.Trace)

test_log = LogWrapper(Log())