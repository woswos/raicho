import os


def verbose():
    return bool(os.environ.get('VERBOSE'))


def quiet(*arguments):
    return [] if verbose() else list(arguments)
