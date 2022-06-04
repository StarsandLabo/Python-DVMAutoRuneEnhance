import re, sys

tango = {
    "BLACK"         : { 'r': 23,    'g': 26,    'b': 27 },
    "DARKBLUE"      : { 'r': 52,    'g': 101,   'b': 164 },
    "DARKGREEN"     : { 'r': 78,    'g': 154,   'b': 6 },
    "DARKCYAN"      : { 'r': 0,     'g': 153,   'b': 204 },
    "DARKRED"       : { 'r': 204,   'g': 0,     'b': 0 },
    "DARKMAGENTA"   : { 'r': 117,   'g': 80,    'b': 123 },
    "DARKYELLOW"    : { 'r': 196,   'g': 160,   'b': 0 },
    "DARKGRAY"      : { 'r': 136,   'g': 138,   'b': 133 },
    "BLUE"          : { 'r': 114,   'g': 159,   'b': 207 },
    "GREEN"         : { 'r': 138,   'g': 226,   'b': 52 },
    "CYAN"          : { 'r': 51,    'g': 181,   'b': 229 },
    "RED"           : { 'r': 239,   'g': 41,    'b': 41 },
    "MAGENTA"       : { 'r': 173,   'g': 127,   'b': 168 },
    "YELLOW"        : { 'r': 237,   'g': 212,   'b': 0 },
    "GRAY"          : { 'r': 186,   'g': 189,   'b': 182 },
    "WHITE"         : { 'r': 238,   'g': 238,   'b': 236 },
    "ORANGE"        : { 'r': 255,   'g': 140,   'b': 0 }, # non standard color
#    "END"           : '\033[0m'
}

class Name_END_CheckError(Exception):
    pass

def NameCheck(input):
    if input == 'END':
        raise Name_END_CheckError('Name "END" is forbidden(reserved)')

class _Foreground():
    def __init__(self, color=tango) -> None:
        for k, v in color.items():
#            print(f"r'\033[38;2;{v['r']};{v['g']};{v['b']}m'")
            setattr(self, str(k), str(f'\033[38;2;{v["r"]};{v["g"]};{v["b"]}m'))
        setattr(self, 'END', str('\033[0m'))
    
    def show(self):
        for i, v in enumerate( TerminalColors.fg.__dict__.items() ):
            if (i + 1) % 7 == 0:
                print(v[1], v[0], TerminalColors.fg.END)
            else:
                print(v[1], v[0], TerminalColors.fg.END, end="" )
        print()
    
    def AddRGBColor(self, Name: str, r: int, g: int, b: int):
        NameCheck(Name)
        setattr(self, str(Name).upper(), str(f'\033[38;2;{int(r)};{int(g)};{int(b)}m'))
        print(f'[ {sys._getframe().f_code.co_name} ] Add Color: ' + f'\033[38;2;{int(r)};{int(g)};{int(b)}m {Name.upper()}' + TerminalColors.fg.END)
        return
    
    def AddWebColor(self, Name: str, Value: str):
        """Value example: Value='#123456' or '123456' """
        NameCheck(Name)
        try:
            Pattern = re.compile(r'^(?P<sharp>#)?(?P<hexpart>[a-f,A-F,0-9]{6})')
        except:
            print('invalid color value')
        
        r = int( Pattern.search(Value).group('hexpart')[0:2], 16 )
        g = int( Pattern.search(Value).group('hexpart')[2:4], 16 )
        b = int( Pattern.search(Value).group('hexpart')[4:6], 16 )
        
        setattr(self, str(Name).upper(), str(f'\033[38;2;{int(r)};{int(g)};{int(b)}m'))
        print(f'[ {sys._getframe().f_code.co_name} ] Add Color: ' + f'\033[38;2;{int(r)};{int(g)};{int(b)}m {Name.upper()}' + TerminalColors.fg.END)
        return
    
    def DeleteColor(self, Name):
        NameCheck(Name)
        delattr(self, str(Name).upper())
        print('removed color: ' + Name.upper())
    
class _Background():
    def __init__(self, color=tango) -> None:
        for k, v in color.items():
#            print(f"r'\033[38;4;{v['r']};{v['g']};{v['b']}m'")
            setattr(self, str(k), str(f'\033[48;2;{v["r"]};{v["g"]};{v["b"]}m'))
        setattr(self, 'END', str('\033[0m'))

    def show(self):
        for i, v in enumerate( TerminalColors.bg.__dict__.items() ):
            if (i + 1) % 7 == 0:
                print(v[1], v[0], TerminalColors.bg.END)
            else:
                print(v[1], v[0], TerminalColors.bg.END, end="" )
        print()
    
    def AddRGBColor(self, Name: str, r: int, g: int, b: int):
        NameCheck(Name)
        setattr(self, str(Name).upper(), str(f'\033[48;2;{int(r)};{int(g)};{int(b)}m'))
        print(f'[ {sys._getframe().f_code.co_name} ] Add Color: ' + f'\033[48;2;{int(r)};{int(g)};{int(b)}m {Name.upper()}' + TerminalColors.bg.END)
        return
    
    def AddWebColor(self, Name: str, Value: str):
        NameCheck(Name)
        try:
            Pattern = re.compile(r'^(?P<sharp>#)?(?P<hexpart>[a-f,A-F,0-9]{6})')
        except:
            print('invalid color value')
        
        r = int( Pattern.search(Value).group('hexpart')[0:2], 16 )
        g = int( Pattern.search(Value).group('hexpart')[2:4], 16 )
        b = int( Pattern.search(Value).group('hexpart')[4:6], 16 )
        
        setattr(self, str(Name).upper(), str(f'\033[48;2;{int(r)};{int(g)};{int(b)}m'))
        print(f'[ {sys._getframe().f_code.co_name} ] Add Color: ' + f'\033[48;2;{int(r)};{int(g)};{int(b)}m {Name.upper()}' + TerminalColors.bg.END)
        return

    def DeleteColor(self, Name):
        NameCheck(Name)
        delattr(self, str(Name).upper())
        print('removed color: ' + Name.upper())

class TerminalColors():
    fg = _Foreground()
    bg = _Background()

"""
fg = TerminalColors().fg
bg = TerminalColors().bg
print( test.Foreground.CYAN + 'test' + test.Foreground.END )


fg = TerminalColors().fg
bg = TerminalColors().bg
fg.show()

test = TerminalColors().fg
test.AddRGBColor('Orange', 255, 69, 0)
test.show()

bg = TerminalColors().bg
bg.AddRGBColor('END', 255, 69, 0)
bg.show()

bg.AddWebColor('test123456', Value='#123456')
bg.show()
"""