from __future__ import print_function
import os 
import sys
import time
import test
import terminal
import Queue

import threading
import multiprocessing

class Level():
    enums = '''
    Error 
    Warn 
    Info 
    Debug 
    Trace
    '''.split()

    for idx, enum in enumerate(enums):
        locals()[enum] = idx

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


class Record(object):
    def __init__(self, caller=None):
        self.time = time.time()
        self.caller = find_caller() if caller is None else caller

class Message(object):
    def __init__(self, message, level):
        self.message = message
        self.level = level



class TestWrapper(object):
    def __init__(self, test):
        self.name = test.name
        self.uid = test.uid
        self.path = test.path


class TestLogItem(Record):
    def __init__(self, test, caller):
        super(TestLogItem, self).__init__(caller)
        self.test = TestWrapper(test)


class SuiteWrapper(object):
    def __init__(self, suite):
        self.name = suite.name
        self.tests = [TestWrapper(test) for test in suite.tests]
        self.uid = suite.uid
        self.path = suite.path


class SuiteResult(Record):
    def __init__(self, suite, result):
        Record.__init__(self, caller=None)
        self.suite = SuiteWrapper(suite)
        self.result = result


class TestStdout(TestLogItem):
    def __init__(self, test, message):
        TestLogItem.__init__(self, test, None)
        self.message = message

        
class TestStderr(TestStdout):
    pass


class TestResult(TestLogItem):
    def __init__(self, test, result):
        TestLogItem.__init__(self, test, caller=None)
        self.result = result
        

class LibraryMessage(Message, Record):
    def __init__(self, message, level, caller=None):
        Record.__init__(self, caller)
        Message.__init__(self, message, level)

    
class TestMessage(Message, TestLogItem):
    def __init__(self, test, message, level, caller):
        TestLogItem.__init__(self, test, caller)
        Message.__init__(self, message, level)


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
    
    def set_verbosity(self, verbosity):
        pass

class _Log(object):
    def __init__(self):
        self.handlers = []

    def add_handler(self, handler):
        # TODO Threadsafe
        self.handlers.append(handler)
    
    def close_handler(self, handler):
        # TODO Threadsafe
        handler.close()
        self.handlers.remove(handler)

    def _log(self, record):
        map(lambda handler:handler.prehandle(), self.handlers)
        for handler in self.handlers:
            handler.handle(record)
            handler.posthandle()
    
    def stdout(self, test, message):  
        self._log(TestStdout(test, message))
    
    def stderr(self, test, message):
        self._log(TestStderr(test, message))

    def testmessage(self, test, message, level, caller):
        self._log(TestMessage(test, message, level, caller))

    def testresult(self, test, result):
        self._log(TestResult(test, result))

    def suiteresult(self, test, result):
        self._log(SuiteResult(test, result))

    def message(self, message, level=Level.Info, caller=None):
        self._log(LibraryMessage(message, level, caller=caller))
    
    def set_verbosity(self, verbosity):
        map(lambda handler:handler.set_verbosity(verbosity), self.handlers)
    
    def close(self):
        for handler in self.handlers:
            handler.close()

Log = _Log()