import sys


def main():
    terminated = False

    while not terminated: 
        sys.stdout.write("$ ")
        command = input()
        print(f"{command}: command not found")

        
if __name__ == "__main__":
    main()
