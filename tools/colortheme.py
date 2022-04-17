#  default color theme
tango = {
    "BLACK"         : '\033[38;2;23;26;27m',
    "DARKBLUE"      : '\033[38;2;52;101;164m',
    "DARKGREEN"     : '\033[38;2;78;154;6m',
    "DARKCYAN"      : '\033[38;2;0;153;204m',
    "DARKRED"       : '\033[38;2;204;0;0m',
    "DARKMAGENTA"   : '\033[38;2;117;80;123m',
    "DARKYELLOW"    : '\033[38;2;196;160;0m',
    "GRAY"          : '\033[38;2;186;189;182m',
    "DARKGRAY"      : '\033[38;2;136;138;133m',
    "BLUE"          : '\033[38;2;114;159;207m',
    "GREEN"         : '\033[38;2;138;226;52m',
    "CYAN"          : '\033[38;2;51;181;229m',
    "RED"           : '\033[38;2;239;41;41m',
    "MAGENTA"       : '\033[38;2;173;127;168m',
    "YELLOW"        : '\033[38;2;237;212;0m',
    "WHITE"         : '\033[38;2;238;238;236m',
#    "END"           : '\033[0m'
}

def colorTheme(themeName = tango,display = False):
    exec("{0} = '{1}'".format( 'END', '\033[0m' ), globals() )

    for color in themeName.keys():
        exec("{0} = '{1}'".format( color, themeName[color] ), globals() )
    
    if display == True:
        print( "Color scheme is changed" )
        for color in themeName:
            if str(color) == 'END':
                continue
            else:
                print   ( " {} is [{} {} {}]".format  (
                                                        str(color),
                                                        themeName[color],
                                                        str(color),
                                                        '\033[0m'
                                                    )
                        )

def cprint(text,color):
    print(color + text + '\033[0m')