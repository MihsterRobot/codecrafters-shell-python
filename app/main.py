import sys


def echo(cmd):
    return cmd.strip("echo")


def main():
    # Map command names to their functionality
    commands = {"exit": "exit", "echo": echo}

    while True:
        sys.stdout.write("$ ")
        command = input()

        # Grab the command 
        handler = commands.get(command)
        if handler == "exit" or handler == None: 
            break
        
        # Run echo() 
        result = handler(command)
        print(result)

        # print(f"{command}: command not found")


if __name__ == "__main__":
    main()
