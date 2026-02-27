import sys

from . import commands as c
from .commands import COMMANDS, EXIT


def main():
    while True:
        line = input("$ ")
        
        if " " in line:
            command_name, raw_args = line.split(" ", 1)
        else:
            command_name, raw_args = line, ""
        
        if command_name in COMMANDS: 
            # Retrieve the command's handler and isolate the raw argument string
            handler = COMMANDS[command_name] 
            # Combine all tokens after the command name back into a single argument string
            
            output, signal = handler(raw_args)

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
