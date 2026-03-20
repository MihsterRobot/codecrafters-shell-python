import sys

from . import commands as c


def main():
    while True:
        line = input('$ ')
        tokens = c.tokenize(line)

        output_file_path = None

        if '>' in tokens or '1>' in tokens:   
            redir_type = '>' if '>' in tokens else '1>'
            redir_idx = tokens.index(redir_type)

            cmd_tokens = tokens[0:redir_idx]
            command_name = cmd_tokens[0]
            raw_args = ' '.join(cmd_tokens[1:])

            output_file_path = tokens[redir_idx+1]
        else: 
            command_name = tokens[0]
            raw_args = ' '.join(tokens[1:])

        if command_name in c.COMMANDS: 
            handler = c.COMMANDS[command_name] 
            output, signal = handler(raw_args)

            if signal is c.EXIT:
                break

            if output is not None and output_file_path is not None: 
                with open(output_file_path, 'w') as f:
                    f.write(output)
            elif output is not None: 
                print(output)

            continue
        
        path = c.find_executable(command_name)

        if path is not None:
            output = c.run_external_program(path, tokens[1:])
            
            if output_file_path is not None:
                with open(output_file_path, 'w') as f:
                    f.write(output)
            else:
                print(output, end='')

            continue
        
        print(f'{command_name}: not found')


if __name__ == '__main__':
    main()
