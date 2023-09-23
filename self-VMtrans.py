import sys, os
COMMENT = '//'

class Parser:
    def __init__(self, vm_file_path):
        self.vm_file = vm_file_path
        self.vm = open(self.vm_file, 'r')
        self.curr_instruction = None
        self.Load_next_instruction()

    def next(self):
        self.curr_instruction = self.next_instruction
        self.Load_next_instruction()

    def Load_next_instruction(self):
        line = self.vm.readline().strip()
        cnt = 0
        while cnt < 100 and line[:1] == COMMENT or line == '':
            line = self.vm.readline().strip()
            cnt += 1
        self.next_instruction = line.split(COMMENT)[0]
        print(self.next_instruction)

    @property
    def has_more_commands(self):
        return self.next_instruction != ''

    def command_type(self, command):
        return {
            'add': 'C_ARITHMETIC',
            'or': 'C_ARITHMETIC',
            'sub': 'C_ARITHMETIC',
            'and': 'C_ARITHMETIC',
            'neg': 'C_ARITHMETIC',
            'not': 'C_ARITHMETIC',
            'eq': 'C_ARITHMETIC',
            'lt': 'C_ARITHMETIC',
            'gt': 'C_ARITHMETIC',
            'push': 'C_PUSH_POP',
            'pop': 'C_PUSH_POP',
        }

    def close(self):
        self.vm.close()

class CodeWriter:
    def __init__(self, asm_file_path):
        self.asm_file = asm_file_path
        self.asm = open(self.asm_file, 'w')
        self.line_count = 0

    def write_push_pop(self, command, type, num):
        address = address_dict(type)
        if command == 'push':
             
        elif command == 'pop':

    def address_dict(self, type):
        return {
            'local': 'LCL',
            'argument': 'ARG',
            'this': 'THIS',
            'that': 'THAT',
            'pointer': 3,
            'temp': 5,
        }
    
    def write(self, command, code=True):
        self.asm.write(command)
        if code:
            self.asm.write(COMMENT + self.line_count)
            self.line_count += 1
        self.asm.write('\n')


class Main:
    def __init__(self, file_path):
        self.asm_file = file_path.replace('.vm', '.asm')
        self.cw = CodeWriter(self.asm_file)

        def translate(self, vm_file):
            parser = Parser(vm_file)
            while parser.has_more_commands:
                parser.next()
                command = parser.curr_instruction
                type = parser.command_type(command[0])
                if type == 'C_PUSH_POP':
                    self.cw.write_push_pop(command[0], command[1], command[2])
                elif type == 'C_ARITHMETIC':
                    self.cw.write_arithmetic(command[0])
            parser.close()
                



if __name__ == '__main__':
    file_path = sys.argv[1]
    Main(file_path)