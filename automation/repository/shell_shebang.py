"""Recognize shell shebangs without executing scripts or expanding their environment."""

import shlex
from pathlib import Path

ENV_FLAGS = {'-', '-i', '--ignore-environment', '-v', '--debug'}
ENV_VALUE_OPTIONS = {'-u', '--unset', '-C', '--chdir', '-a', '--argv0'}


def env_command(arguments):
    arguments = list(arguments)
    while arguments:
        argument = arguments.pop(0)
        if argument == '--':
            break
        if argument in ENV_FLAGS or argument in {'-S', '--split-string'}:
            continue
        if len(argument) > 2 and argument[:2] in {'-i', '-v'}:
            arguments.insert(0, f'-{argument[2:]}')
            continue
        if argument.startswith('--split-string='):
            arguments[:0] = shlex.split(argument.partition('=')[2])
            continue
        if argument.startswith('-S'):
            arguments[:0] = shlex.split(argument[2:])
            continue
        if argument in ENV_VALUE_OPTIONS:
            if not arguments:
                return None
            arguments.pop(0)
            continue
        option, separator, _ = argument.partition('=')
        if separator and option.startswith('--') and option in ENV_VALUE_OPTIONS:
            continue
        if len(argument) > 2 and argument[:2] in {'-u', '-C', '-a'}:
            continue
        if argument.startswith('-'):
            return None
        arguments.insert(0, argument)
        break
    while arguments and '=' in arguments[0]:
        arguments.pop(0)
    return arguments[0] if arguments else None


def shell_header(line):
    if not line.startswith(b'#!'):
        return False
    try:
        arguments = shlex.split(line[2:].decode())
        if not arguments:
            return False
        command = arguments[0]
        if Path(command).name == 'env':
            command = env_command(arguments[1:])
    except (UnicodeError, ValueError):
        return False
    return command is not None and Path(command).name in {'sh', 'bash'}
