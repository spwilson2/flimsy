import multiprocessing
import traceback
import sys


class SubprocessException(Exception):
    def __init__(self, exception, trace):
        super(SubprocessException, self).__init__(trace)

class ExceptionProcess(multiprocessing.Process):
    class Status():
        def __init__(self, exitcode, exception_tuple):
            self.exitcode = exitcode
            if exception_tuple is not None:
                self.trace = exception_tuple[1]
                self.exception = exception_tuple[0]
            else:
                self.exception = None
                self.trace = None

    def __init__(self, *args, **kwargs):
        multiprocessing.Process.__init__(self, *args, **kwargs)
        self._pconn, self._cconn = multiprocessing.Pipe()
        self._exception = None

    def run(self):
        try:
            super(ExceptionProcess, self).run()
            self._cconn.send(None)
        except Exception as e:
            tb = traceback.format_exc()
            self._cconn.send((e, tb))
            sys.exit(1)

    @property
    def status(self):
        if self._pconn.poll():
            self._exception = self._pconn.recv()
        
        return self.Status(self.exitcode, self._exception)


class Sandbox(object):
    def __init__(self, function, args=tuple(), kwargs={}):
        self.p = ExceptionProcess(target=function, args=args, kwargs=kwargs)
        self.p.start()
        self.p.join()
        status = self.p.status
        if status.exitcode:
            raise SubprocessException(status.exception, status.trace)