import sys

from .commands import COMMANDS, EXIT


def main():
    while True:
        command = input("$ ").split()
        
        # Extract the command name (first token) from the user's input
        command_name = command[0]

        # Command name isn't a builtin or registered handler
        if command_name not in COMMANDS: 
            print(f"{command_name}: not found")
            continue

        # Retrieve the command's handler and isolate the raw argument string
        handler = COMMANDS[command_name] 
        command_args = command.removeprefix(command_name + " ")

        output, signal = handler(command_args)

        if signal is EXIT:
            break

        if output is not None: 
            print(output)


if __name__ == "__main__":
    main()
