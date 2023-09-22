import os

COMMENT = '//'

class Parser(object):
    def __init__(self, vm_file):
        self.vm = open(vm_file, 'r')
        self.curr_instruction = None
        self.asm_file = vm_file.replace('.vm', '.asm')
        self.commands = self.command_dict()
        self.initialize()

    @property
    def has_next_instruction(self):
        return bool(self.next_instruction)
    @property
    def command_type(self):
        if len(self.curr_instruction) > 0:
            return self.commands.get(self.curr_instruction[0].lower())

    def command_dict(self):
        return {
            'and': 'C_ARITHMETIC',
            'or': 'C_ARITHMETIC',
            'sub': 'C_ARITHMETIC',
            'add': 'C_ARITHMETIC',
            'neg': 'C_ARITHMETIC',
            'not': 'C_ARITHMETIC',
            'eq': 'C_ARITHMETIC',
            'lt': 'C_ARITHMETIC',
            'gt': 'C_ARITHMETIC',
            'push': 'C_PP',
            'pop': 'C_PP',
        }

    def initialize(self):
        self.vm.seek(0)
        line = self.vm.readline().strip()
        while self.is_comment(line):
            line = self.vm.readline().strip()
        self.load_next_instruction(line)

    def next(self):
        self.curr_instruction = self.next_instruction
        self.load_next_instruction()

    def load_next_instruction(self, line=None):
        line = line if line != None else self.vm.readline().strip()
        self.next_instruction = line.split(COMMENT)[0].strip().split()

    def is_comment(self, line):
        return line == '' or line[:2] == COMMENT

class CodeWriter(object):
    def __init__(self, asm_file):
        self.asm = open(asm_file, 'w')
        self.bool_count = 0
        self.addresses = self.address_dict()
        self.curr_file = asm_file.replace('.asm', '').split('\\')[-1]

    def write_push_pop(self, operation, segment, num):
        self.resolve_address(segment, num)
        if operation == 'push':
            if segment == 'constant':
                self.write('D=A')
            else:
                self.write('D=M')
            self.push_D_to_stack()
        elif operation == 'pop':    
            self.write('D=A')
            self.write('@R14') # available space
            self.write('M=D')
            self.pop_from_stack()
            self.write('D=M')
            self.write('@R14')
            self.write('A=M')
            self.write('M=D')
        else:
            print('error!\n')
    
    def resolve_address(self, segment, num):
        address = self.addresses.get(segment)
        if segment == 'constant':
            self.write('@'+str(num))
        elif segment in ['local', 'argument', 'this', 'that']:
            self.write('@'+str(address))
            self.write('D=M')
            self.write('@'+num)
            self.write('A=D+A')
        elif segment in ['temp', 'pointer']:
            self.write('@'+str(address + int(num)))
        elif segment == 'static':
            self.write('@'+self.curr_file+'.'+str(num))

    def write_arithmetic(self, operation):
        '''
        and, or, sub, add, neg, not, eq, lt, gt 
        '''
        if operation not in ['neg', 'not']:
            self.pop_from_stack()
            self.write('D=M')
        self.pop_from_stack()

        if operation in ['eq', 'lt', 'gt']:
            self.write('D=M-D')
            self.write('@BOOL{}'.format(self.bool_count))
            if operation == 'eq':
                self.write('D;JEQ')
            elif operation == 'lt':
                self.write('D;JLT')
            elif operation == 'gt':
                self.write('D;JGT')
            
            self.call_SP()
            self.write('M=0')
            self.write('@ENDBOOL{}'.format(self.bool_count))
            self.write('0;JMP')

            self.write('(BOOL{})'.format(self.bool_count))
            self.call_SP()
            self.write('M=-1')
            self.write('(ENDBOOL{})'.format(self.bool_count))
            self.bool_count += 1
        elif operation in ['add', 'or', 'sub', 'and', 'neg', 'not']:
            if operation == 'add':
                self.write('M=M+D')
            elif operation == 'or':
                self.write('M=M|D')
            elif operation == 'sub':
                self.write('M=M-D')
            elif operation == 'and':
                self.write('M=M&D')
            elif operation == 'neg':
                self.write('M=-M')
            elif operation == 'not':
                self.write('M=!M')

        self.increase_SP()

    def address_dict(self):
        return {
            'local': 'LCL', # R1
            'argument': 'ARG', # R2
            'this': 'THIS', # R3
            'that': 'THAT', # R4
            'pointer': 3, # R3, R4
            'temp': 5, # R5-12
            'static': 16, # R16-255
        }

    def push_D_to_stack(self):
        self.write('@SP')
        self.write('A=M')
        self.write('M=D')
        self.increase_SP()

    def increase_SP(self):
        self.write('@SP')
        self.write('M=M+1')

    def decrease_SP(self):
        self.write('@SP')
        self.write('M=M-1')

    def pop_from_stack(self):
        self.decrease_SP()
        self.write('A=M')
    
    def call_SP(self):
        self.write('@SP')
        self.write('A=M')
    
    def write(self, command):
        self.asm.write(command + '\n')

class Main(object):
    def __init__(self, file_path):
        parser = Parser(file_path)
        self.cw = CodeWriter(parser.asm_file)

        while parser.has_next_instruction:
            parser.next()
            self.cw.write('// ' + ' '.join(parser.curr_instruction))
            if parser.command_type == 'C_PP':
                self.cw.write_push_pop(parser.curr_instruction[0], parser.curr_instruction[1], parser.curr_instruction[2])
            elif parser.command_type == 'C_ARITHMETIC':
                self.cw.write_arithmetic(parser.curr_instruction[0])

if __name__ == '__main__':
    import sys
    file_path = sys.argv[1]
    Main(file_path)
