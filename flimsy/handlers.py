from __future__ import print_function

import multiprocessing
import os
import Queue
import sys
import threading
import time

import config
import helper
import log
import terminal
import test
import uid


def test_results_output_path(test_case):
    '''
    Return the path which results for a specific test case should be
    stored.
    '''
    return os.path.join(config.config.result_path, test_case.uid.replace('/','-'))

class TestResult(object):
    def __init__(self, test):
        self.test = test
        helper.mkdir_p(test_results_output_path(self.test))
        self.stdout = open(self.stdout_fname, 'w')
        self.stderr = open(self.stderr_fname, 'w')
    
    def write_stdout(self, buf):
        self.stdout.write(buf)
    
    def write_stderr(self, buf):
        self.stderr.write(buf)

    @property
    def result(self):
        return self._result

    @result.setter
    def result(self, value):
        self._result = value

    @property
    def stdout_fname(self):
        return os.path.join(test_results_output_path(self.test), 'stdout')
    
    @property
    def stderr_fname(self):
        return os.path.join(test_results_output_path(self.test), 'stderr')

class ResultHandler(log.Handler):
    def __init__(self):
        self.results = {}
        self.mapping = {
            log.TestResult: self.handle_testresult,
            log.TestStderr: self.handle_stderr,
            log.TestStdout: self.handle_stdout,
        }

    def handle(self, record):
        self.mapping.get(type(record), lambda _:None)(record)

    def handle_stderr(self, record):
        self.results[record.test.uid].write_stderr(record.message)

    def handle_stdout(self, record):
        self.results[record.test.uid].write_stdout(record.message)

    def handle_testresult(self, record):
        if record.result == test.InProgress:
            # Create a new test result object for the test which is now in progress.
            self.results[record.test.uid] = TestResult(record.test)
        else:
            # Update the given test's status
            self.results[record.test.uid].result = record.result

    def close(self):
        pass


class TerminalHandler(log.Handler):
    def __init__(self, stream, verbosity=log.Info):
        self.stream = stream
        self.verbosity = verbosity
        self.mapping = {
            log.TestResult: self.handle_testresult,
            log.TestStderr: self.handle_stderr,
            log.TestStdout: self.handle_stdout,
            log.TestMessage: self.handle_testmessage,
            log.LibraryMessage: self.handle_librarymessage,
        }
    
    def handle_testresult(self, record):
        if record.result == test.InProgress:
            print('Running %s...' % record.test.name)
        else:
            print('%s - %s' % (record.test.name, record.result))
            print(terminal.separator('-'))

    
    def handle_stderr(self, record):
        if self.stream: print(record.message, file=sys.stderr, end='')
        
    def handle_stdout(self, record):
        if self.stream: print(record.message, file=sys.stdout, end='')
    
    def handle_testmessage(self, record):
        if self.stream: print(record.message, record.caller)

    def handle_librarymessage(self, record):
        print(record.message)

    def handle(self, record):
        if hasattr(record, 'level'):
            if record.level > self.verbosity:
                return
        self.mapping.get(type(record), lambda _:None)(record)
    
    def set_verbosity(self, verbosity):
        self.verbosity = verbosity


class MultiprocessingHandlerWrapper(log.Handler):
    '''
    A class which wraps other handlers and to enable 
    logging across multiprocessing processes
    '''
    def __init__(self, *subhandlers):
        # Create thread to spin handing recipt of messages
        # Create queue to push onto
        self.queue = multiprocessing.Queue()
        self.thread = threading.Thread(target=self.receive)
        self._shutdown = threading.Event()
        self.thread.daemon = True
        self.thread.start()
        self.subhandlers = subhandlers

    def _handle(self, record):
        for handler in self.subhandlers:
            handler.handle(record)

    def receive(self):
        while not self._shutdown.is_set():
            try:
                item = self.queue.get(timeout=0.1)
                self._handle(item)
            except (KeyboardInterrupt, SystemExit):
                raise
            except EOFError:
                return
            except Queue.Empty:
                continue
    
    def send(self, record):
        self.queue.put(record)

    def handle(self, record):
        self.send(record)

    def set_verbosity(self, verbosity):
        for handler in self.subhandlers:
            handler.set_verbosity(verbosity)
    
    def close(self):
        for handler in self.subhandlers: handler.close()
        self._shutdown.set()
        self.thread.join()
