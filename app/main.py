import sys

from . import commands as c
from .commands import COMMANDS, EXIT, tokenize


def main():
    while True:
        line = input('$ ')

        tokens = tokenize(line)
        command_name = tokens[0]
        raw_args = ''.join(tokens[1:])

        if command_name in COMMANDS: 
            handler = COMMANDS[command_name] 
            output, signal = handler(raw_args)

            if signal is EXIT:
                break

            if output is not None: 
                print(output)

            continue
        
        path = c.find_executable(command_name)

        if path is not None: 
            print(c.run_external_program(path, tokens[1:]), end='')
            continue
        
        print(f'{command_name}: not found')


if __name__ == '__main__':
    main()
