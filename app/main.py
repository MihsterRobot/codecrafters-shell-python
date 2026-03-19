import sys
import shlex

from . import commands as c
from .commands import COMMANDS, EXIT, tokenize


def main():
    while True:
        line = input('$ ')

        tokens = tokenize(line)
        command_name = tokens[0]
        raw_args = ' '.join(tokens[1:])

        # command_name, raw_args = line.split(' ', 1) if ' ' in line else (line, '')

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
            # arg_list = shlex.split(raw_args)

            print(c.run_external_program(path, tokens[1:]), end='')
            
            continue
        
        print(f'{command_name}: not found')


if __name__ == '__main__':
    main()
