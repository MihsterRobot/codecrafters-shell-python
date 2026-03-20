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
            cmd_name = cmd_tokens[0]
            raw_args = ' '.join(cmd_tokens[1:])

            output_file_path = tokens[redir_idx+1]
        else: 
            cmd_tokens = tokens
            cmd_name = tokens[0]
            raw_args = ' '.join(tokens[1:])

        if '2>' in tokens: 
            redir_idx = tokens.index('2>')
            stderr_file_path = tokens[redir_idx+1]
            
        if cmd_name in c.COMMANDS: 
            handler = c.COMMANDS[cmd_name] 
            output, signal = handler(raw_args)

            if signal is c.EXIT:
                break

            if output is not None and output_file_path is not None: 
                with open(output_file_path, 'w') as f:
                    f.write(output + '\n')
            elif output is not None: 
                print(output)

            continue
        
        exe_name = c.find_executable(cmd_name)

        if exe_name is not None:
            stdout, stderr = c.run_external_program(exe_name, cmd_tokens[1:])

            if output_file_path is not None:
                if stdout: 
                    with open(output_file_path, 'w') as f:
                        f.write(stdout)
            else:
                print(stdout, end='')
              
            if stderr_file_path: 
                    with open(stderr_file_path, 'w') as f: 
                        f.write(stderr)
            else: 
                if stderr: 
                    print(stderr, end='')

            continue
        else: 
            print(f'{cmd_name}: not found')


if __name__ == '__main__':
    main()
