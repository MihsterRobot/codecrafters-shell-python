import sys

from . import commands as c
from .commands import COMMANDS, EXIT


def main():
    while True:
        line = input("$ ")

        command_name = []

        for char in line: 
            if char == " ": 
                break
            command_name.append(char)

        command_name = "".join(command_name)

        if command_name in COMMANDS: 
            handler = COMMANDS[command_name] 
            command_args = line.replace(command_name + " ", "")
            # command_args = "".join(command[1:])

            output, signal = handler(command_args)

            if signal is EXIT:
                break

            if output is not None: 
                print(output)

            continue
        
        path = c.find_executable(command_name)
        
        if path is not None: 
            command_args = command[1:]
            print(c.run_external_program(path, command_args), end="")
            continue
        
        print(f"{command_name}: not found")


if __name__ == "__main__":
    main()
