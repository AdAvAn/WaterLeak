import utime
import sys
import uio

# srctype = pycopy-lib
# type = package
# version = 0.7.5
# author = Stefan Lehmann, Paul Sokolovsky
# long_desc = README.rst
# depends = os
# https://github.com/pfalcon/pycopy-lib/tree/master/logging

CRITICAL = 50
ERROR    = 40
WARNING  = 30
INFO     = 20
DEBUG    = 10
NOTSET   = 0

_level_dict = {
    CRITICAL: "CRITICAL",
    ERROR: "ERROR",
    WARNING: "WARNING",
    INFO: "INFO",
    DEBUG: "DEBUG",
}

class Logger:

    level = NOTSET

    def __init__(self, name):
        self.name = name
        self.handlers = ()
        self.parent = None
        self.propagate = True

    def _level_str(self, level):
        l = _level_dict.get(level)
        if l is not None:
            return l
        return "LVL%s" % level

    def setLevel(self, level):
        self.level = level

    def isEnabledFor(self, level):
        return level >= self.level

    def log(self, level, msg, *args):
        dest = self
        while dest.level == NOTSET and dest.parent:
            dest = dest.parent
        if level >= dest.level:
            record = LogRecord(
                self.name, level, None, None, msg, args, None, None, None
            )

            if dest.handlers:
                for hdlr in dest.handlers:
                    hdlr.emit(record)

    def debug(self, msg, *args):
        self.log(DEBUG, msg, *args)

    def info(self, msg, *args):
        self.log(INFO, msg, *args)

    def warning(self, msg, *args):
        self.log(WARNING, msg, *args)

    warn = warning

    def error(self, msg, *args):
        self.log(ERROR, msg, *args)

    def critical(self, msg, *args):
        self.log(CRITICAL, msg, *args)

    def exc(self, e, msg, *args):
        buf = uio.StringIO()
        print(str(e), buf)
        self.log(ERROR, msg + "\n" + buf.getvalue(), *args)

    def exception(self, exeption, msg, *args):
        self.exc(exeption, msg, *args)

    def addHandler(self, hdlr):
        if self.handlers is ():
            self.handlers = []
        self.handlers.append(hdlr) # type: ignore


class Handler:
    def __init__(self):
        self.formatter = Formatter()

    def setFormatter(self, fmt):
        self.formatter = fmt

    def format(self, record):
        return self.formatter.format(record)


class StreamHandler(Handler):
    def __init__(self, stream=None):
        super().__init__()
        self._stream = stream or sys.stderr
        self.terminator = "\n"

    def emit(self, record):
        self._stream.write(self.formatter.format(record) + self.terminator)
        self.flush()

    def flush(self):
        if hasattr(self._stream, 'flush'):
            self._stream.flush()


class FileHandler(StreamHandler):
    def __init__(self, filename, mode="a", encoding=None, delay=False):
        super().__init__(None)

        self.encoding = encoding
        self.mode = mode
        self.delay = delay
        self.filename = filename

        if not delay:
            self._stream = open(self.filename, self.mode)

    def emit(self, record):
        if self._stream is None:
            self._stream = open(self.filename, self.mode)

        super().emit(record)

    def close(self):
        if self._stream is not None:
            self._stream.close()


class Formatter:

    converter = utime.localtime

    def __init__(self, fmt=None, datefmt=None, style="%"):
        self.fmt = fmt or "%(message)s"
        self.datefmt = datefmt

        if style not in ("%", "{"):
            raise ValueError("Style must be one of: %, {")

        self.style = style

    def usesTime(self):
        if self.style == "%":
            return "%(asctime)" in self.fmt
        elif self.style == "{":
            return "{asctime" in self.fmt

    def format(self, record):
        # The message attribute of the record is computed using msg % args.
        record.message = record.msg % record.args

        # If the formatting string contains '(asctime)', formatTime() is called to
        # format the event time.
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)

        # If there is exception information, it is formatted using formatException()
        # and appended to the message. The formatted exception information is cached
        # in attribute exc_text.
        if record.exc_info is not None:
            record.exc_text += self.formatException(record.exc_info)
            record.message += "\n" + record.exc_text

        # The record’s attribute dictionary is used as the operand to a string
        # formatting operation.
        if self.style == "%":
            return self.fmt % record.__dict__
        elif self.style == "{":
            return self.fmt.format(**record.__dict__)
        else:
            raise ValueError(
                "Style {0} is not supported by logging.".format(self.style)
            )

    def formatTime(self, record, datefmt=None):
        assert datefmt is None  # datefmt is not supported
        ct = utime.localtime(record.created)
        return "{0}-{1}-{2} {3}:{4}:{5}".format(*ct)

    def formatException(self, exc_info):
        raise NotImplementedError()

    def formatStack(self, stack_info):
        raise NotImplementedError()


class LogRecord:
    def __init__(
        self, name, level, pathname, lineno, msg, args, exc_info, func=None, sinfo=None
    ):
        ct = utime.time()
        self.created = ct
        self.msecs = (ct - int(ct)) * 1000
        self.name = name
        self.levelno = level
        self.levelname = _level_dict.get(level, None)
        self.pathname = pathname
        self.lineno = lineno
        self.msg = msg
        self.args = args
        self.exc_info = exc_info
        self.func = func
        self.sinfo = sinfo


# root = Logger("root")
# root.setLevel(WARNING)
# sh = StreamHandler()
# sh.formatter = Formatter()
# root.addHandler(sh)
# _loggers = {}