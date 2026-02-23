import sys


# def echo(cmd): 
#     print(cmd)

def echo(cmd):
    return cmd

def main():
    while True:
        sys.stdout.write("$ ")
        command = input()

        if command == "exit": 
            break
        
        print(echo(command))

        # print(f"{command}: command not found")


if __name__ == "__main__":
    main()
