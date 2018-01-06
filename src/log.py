# COMMENT = '\033[90m'
# HEADER = '\033[35m'
# OKBLUE = '\033[34m'
# OKGREEN = '\033[32m'

NORMAL = '\033[0m'
WARNING = '\033[33m'
ERROR = '\033[31m'

BOLD = '\033[1m'
# UNDERLINE = '\033[4m'


def log(txt, *args, **kwargs):
    print(txt, *args, **kwargs)
    return


def warning(msg, *args, **kwargs):
    log(WARNING + 'warning: ' + str(msg) + NORMAL, *args, **kwargs)


def error(msg, *args, **kwargs):
    log(ERROR + 'error: ' + str(msg) + NORMAL, *args, **kwargs)


def bold(msg, *args, **kwargs):
    log(BOLD + str(msg) + NORMAL, *args, **kwargs)
