# COMMENT = '\033[90m'
# HEADER = '\033[35m'
# OKBLUE = '\033[34m'
# OKGREEN = '\033[32m'

NORMAL = '\033[0m'
WARNING = '\033[33m'
ERROR = '\033[31m'

# BOLD = '\033[1m'
# UNDERLINE = '\033[4m'


def warning(msg, *args, **kwargs):
    print(WARNING + 'warning: ' + str(msg) + NORMAL, *args, **kwargs)


def error(msg, *args, **kwargs):
    print(ERROR + 'error: ' + str(msg) + NORMAL, *args, **kwargs)
