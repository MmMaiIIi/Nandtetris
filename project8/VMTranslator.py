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
            'label': 'C_BRANCH',
            'if-goto': 'C_BRANCH',
            'goto': 'C_BRANCH',
            'function': 'C_FUNCTION',
            'call': 'C_FUNCTION',
            'return': 'C_RETURN',
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
        if line == '':
            line = self.vm.readline().strip()
        self.next_instruction = line.split(COMMENT)[0].strip().split()

    def is_comment(self, line):
        return line == '' or line[:2] == COMMENT
    
    def close(self):
        self.vm.close()

class CodeWriter(object):
    def __init__(self, asm_file):
        self.asm = open(asm_file, 'w')
        self.bool_count = 0
        self.func_count = 0
        self.line_count = 0
        self.addresses = self.address_dict()

    def write_init(self):
        self.write('@256')
        self.write('D=A')
        self.write('@SP')
        self.write('M=D')
        self.write_function('call', 'Sys.init', '0')

    def set_file_name(self, vm_file):
        self.curr_file = vm_file.replace('.vm', '').split('/')[-1]
        self.write('//////', code=False)
        self.write('// {}'.format(self.curr_file), code=False)

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
            self.write('@R13') # available space
            self.write('M=D')
            self.pop_from_stack()
            self.write('D=M')
            self.write('@R13')
            self.write('A=M')
            self.write('M=D')
        else:
            print('error!\n')
    
    def resolve_address(self, segment, num):
        address = self.addresses.get(segment)
        if segment == 'constant':
            self.write('@' + str(num))
        elif segment in ['local', 'argument', 'this', 'that']:
            self.write('@' + str(address))
            self.write('D=M')
            self.write('@' + num)
            self.write('A=D+A')
        elif segment in ['temp', 'pointer']:
            self.write('@R' + str(address + int(num)))
        elif segment == 'static':
            self.write('@' + self.curr_file + '.' + str(num))

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

            self.write('(BOOL{})'.format(self.bool_count), code=False)
            self.call_SP()
            self.write('M=-1')
            self.write('(ENDBOOL{})'.format(self.bool_count), code=False)
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

    def write_branch(self, segment, name):
        '''
        if-goto LOOP_START 
        label LOOP_START
        '''
        if segment == 'label':
            self.write('({}${})'.format(self.curr_file, name), code=False)
        elif segment == 'if-goto':
            self.pop_from_stack()
            self.write('D=M')
            self.write('@{}${}'.format(self.curr_file, name))
            self.write('D; JNE')
        elif segment == 'goto':
            self.write('@{}${}'.format(self.curr_file, name))
            self.write('D;JMP')

    def write_function(self, operation, name, num):
        if operation == 'function':
            self.write('({})'.format(name), code=False)
            for x in range(int(num)):
                self.write('D=0')
                self.push_D_to_stack()
        elif operation == 'call':
            RES = name + 'RES' + str(self.func_count) # unique 
            self.func_count += 1

            # push return-address
            self.write('@' + RES)
            self.write('D=A')
            self.push_D_to_stack()
            
            # push LCL
            # push ARG
            # push THIS
            # push THAT
            for address in ['LCL', 'ARG', 'THIS', 'THAT']:
                self.write('@' + address)
                self.write('D=M')
                self.push_D_to_stack()

            # LCL = SP
            self.write('@SP')
            self.write('D=M')
            self.write('@LCL')
            self.write('M=D')

            # ARG = SP-n-5
            self.write('@SP')
            self.write('D=M')
            self.write('@' + str(int(num) + 5))
            self.write('D=D-A')
            self.write('@ARG')
            self.write('M=D')

            # goto f
            self.write('@'+name)
            self.write('0;JMP')

            # (return_address)
            self.write('({})'.format(RES), code=False)
        
    def write_return(self):
        TEMP = 'R13'
        RES = 'R14'

        # TEMP = LCL
        self.write('@LCL')
        self.write('D=M')
        self.write('@' + TEMP)
        self.write('M=D')
        
        # RET = *(TEMP - 5)
        # if no argument, the return address will be covered
        self.write('@' + TEMP)
        self.write('D=M')
        self.write('@5')
        self.write('D=D-A')
        self.write('A=D')
        self.write('D=M')
        self.write('@' + RES)
        self.write('M=D')

        # *ARG = pop()
        self.pop_from_stack()
        self.write('D=M')
        self.write('@ARG')
        self.write('A=M')
        self.write('M=D')

        # SP = ARG + 1
        self.write('@ARG')
        self.write('D=M')
        self.write('@SP')
        self.write('M=D+1')

        # THAT = *(FRAME-1)
        # THIS = *(FRAME-2)
        # ARG = *(FRAME-3)
        # LCL = *(FRAME-4)
        offset = 1
        for address in ['@THAT', '@THIS', '@ARG', '@LCL']:
            self.write('@' + TEMP)
            self.write('D=M')
            self.write('@' + str(offset))
            self.write('D=D-A')
            self.write('A=D')
            self.write('D=M')
            self.write(address)
            self.write('M=D')
            offset += 1

        # gotp RES
        self.write('@' + RES)
        self.write('A=M')
        self.write('0;JMP')
        
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
    
    def write(self, command, code=True):
        self.asm.write(command)
        if code:
            self.asm.write(' // ' + str(self.line_count))
            self.line_count += 1
        self.asm.write('\n')

    def close(self):
        self.asm.close()

class Main(object):
    def __init__(self, file_path):
        self.Parse_file(file_path)
        self.cw = CodeWriter(self.asm_file)
        self.cw.write_init()
        for vm_file in self.vm_files:
            self.translate(vm_file)
        self.cw.close()

    def Parse_file(self, file_path):
        if '.vm' in file_path:
            self.asm_file = file_path.replace('.vm', '.asm')
            self.vm_files = [file_path]
        else:
            file_path = file_path[:-1] if file_path[-1] == '/' else file_path
            path_elements = file_path.split('\\')
            path = '/'.join(path_elements)
            self.asm_file = path + '/' + path_elements[-1] + '.asm'
            dirpaths, dirnames, filenames = next(os.walk(file_path), [[], [], []])
            vm_files = filter(lambda x: '.vm' in x, filenames)
            self.vm_files = [path + '/' + vm_file for vm_file in vm_files]

    def translate(self, vm_file):
        parser = Parser(vm_file)
        self.cw.set_file_name(vm_file)
        while parser.has_next_instruction:
            parser.next()
            self.cw.write('// ' + ' '.join(parser.curr_instruction), code=False)
            if parser.command_type == 'C_PP':
                self.cw.write_push_pop(parser.curr_instruction[0], parser.curr_instruction[1], parser.curr_instruction[2])
            elif parser.command_type == 'C_ARITHMETIC':
                self.cw.write_arithmetic(parser.curr_instruction[0])
            elif parser.command_type == 'C_BRANCH':
                self.cw.write_branch(parser.curr_instruction[0], parser.curr_instruction[1])
            elif parser.command_type == 'C_FUNCTION':
                self.cw.write_function(parser.curr_instruction[0], parser.curr_instruction[1], parser.curr_instruction[2])
            elif parser.command_type == 'C_RETURN':
                self.cw.write_return()
        parser.close()

if __name__ == '__main__':
    import sys
    file_path = sys.argv[1]
    Main(file_path)
