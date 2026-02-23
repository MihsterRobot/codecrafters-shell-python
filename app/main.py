import sys


def echo(cmd): 
    print(cmd)


def main():
    while True:
        sys.stdout.write("$ ")
        command = input()

        if command == "exit": 
            break
        
        echo(command)

        # print(f"{command}: command not found")


if __name__ == "__main__":
    main()
