import pathlib,sys
import pprint

TEMPLATE_DIR = pathlib.Path('/home/starsand/DVM-AutoRuneEnhance/resources/img/template/summary/template/')

class Templates():
    
    def __init__(self) -> None:
        for item in TEMPLATE_DIR.glob("*.png"):
            setattr(self, item.stem, {
                "template" : item.as_posix(),
                "sceneName" : item.stem
                })

    def list(self):
        print(f'[{Templates().__class__.__name__}]{sys._getframe().f_code.co_name}: include these objects')
        pprint.pprint( [ v.stem for v in TEMPLATE_DIR.glob("*.png") ] )
        return [ v.stem for v in TEMPLATE_DIR.glob("*.png") ]

#? testcodes
"""
print( list(TEMPLATE_DIR.glob("*.png")) )

test = Templates()

print()
print( test.set['template'] )

test.close['template']
"""