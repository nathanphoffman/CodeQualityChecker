# A handler is loud if it re-raises, uses the caught error, or calls something that speaks up: print, a logger, exit.
LOUD_NAME_ENDINGS = {"debug", "info", "warning", "warn", "error", "exception", "critical", "print", "exit", "fatal",
                     "println", "eprintln", "dbg", "panic", "abort", "trace"}

LOUD_RECEIVERS = {"logging", "logger", "log", "console", "tracing"}
BROAD_EXCEPTIONS = {"Exception", "BaseException"}

# Callbacks passed to a promise's .catch that do nothing, written without spaces after the "=>".
SILENT_CALLBACK_BODIES = ("{})", "null)", "undefined)", "[])")

# Swallowing an error you expect (a missing key, a bad number) is half as bad as swallowing anything at all.
NARROW_SILENT_WEIGHT = 0.5

# Error checks per line of code: 100% between one per 6 ** 3 and one per 6 ** 4 lines, since how they are written varies.
# The middle of that range, in powers of 6, is 6 ** 3.5 lines per check, and the range stretches half a power either side.
LINES_PER_ERROR_CHECK = 6 ** 3.5
FULL_CREDIT_POWERS = 0.5
MIN_LINES_PER_ERROR_CHECK = 6 ** 3
MAX_LINES_PER_ERROR_CHECK = 6 ** 4
