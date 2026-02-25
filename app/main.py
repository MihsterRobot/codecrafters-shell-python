import sys

from commands import COMMANDS, EXIT


def main():
    while True:
        sys.stdout.write("$ ")
        command = input()
        
        # Extract the command name (first token) from the user's input
        cmd = command.split()[0]

        # Command name isn't a builtin or registered handler
        if cmd not in COMMANDS: 
            print(f"{cmd}: not found")
            continue

        # Retrieve the command's handler and isolate the raw argument string
        handler = COMMANDS[cmd] 
        command_args = command.removeprefix(cmd + " ")

        output, signal = handler(command_args)

        if signal is EXIT:
            break

        if output is not None: 
            print(output)


if __name__ == "__main__":
    main()
