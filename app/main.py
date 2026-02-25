import sys

from . import commands as c
from .commands import COMMANDS, EXIT



def main():
    while True:
        command = input("$ ").split()
        
        # Extract the command name (first token) from the user's input
        command_name = command[0]
        
        if command_name in COMMANDS: 
            # Retrieve the command's handler and isolate the raw argument string
            handler = COMMANDS[command_name] 
            command_args = command[1:]

            output, signal = handler(command_args)

            if signal is EXIT:
                break

            if output is not None: 
                print(output)
        
        path = c.find_executable(command_name)
        command_args = command[1:]

        if path is not None: 
            print(c.run_external_program(path, command_args))
        else: 
            print(f"{command_name}: not found")


if __name__ == "__main__":
    main()
