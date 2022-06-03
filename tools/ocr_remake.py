import pathlib, sys
from subprocess import call
from enum import Enum
import re, datetime, pprint, os, shutil
import tempfile
from cv2 import TickMeter


PROJECT_DIR = pathlib.Path('/home/starsand/DVM-AutoRuneEnhance/')
sys.path.append(PROJECT_DIR.as_posix())
sys.path.append(PROJECT_DIR.joinpath('tools').as_posix())
sys.path.append(PROJECT_DIR.joinpath('lib', 'python3.10', 'site-packages').as_posix())
sys.path.append(PROJECT_DIR.joinpath('program').as_posix())

import numpy as np
from matplotlib import pyplot as plt
import cv2
import pyautogui as pag
#from PIL import ImageGrab as Image
from PIL import Image
import pyscreeze as pysc
import pyocr
import pandas as pd
import pprint

#* My tools
from tools import colortheme as clr
from tools import reduce_overdetected as rod
from tools.clickcondition import ClickCondition as clcd
from tools.ScreenCapture_pillow import ScreenCapture
from tools.GetUniqueCoordinates import GetUniqueCoordinates
from tools.RuneSummaryTemplates import Templates
from tools.TerminalColors import TerminalColors as tc
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import threading


bg = tc().bg
fg = tc().fg

WORKING_DIR = PROJECT_DIR.joinpath('work')       
WORKING_PICTURE_SAVE_DIR = WORKING_DIR.joinpath('img')

RESOURCE_DIR = PROJECT_DIR.joinpath('resources')
TEMPLATE_IMG_DIR = RESOURCE_DIR.joinpath('img', 'template')

RESULT_DIR = PROJECT_DIR.joinpath('result')

LOG_FILE_NAME = "".join(
    [
        'RuneLockManagement_', 
        datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'),
        '.log'
    ]
)
LOG_FILE_PATH = RESULT_DIR.joinpath(LOG_FILE_NAME).as_posix()
RECENT_ENHANCED_LIST_PATH = RESULT_DIR.joinpath('RecentEnhancedList.json').as_posix()

# 実行世代間利用
PROCESS_GENERATION_FILE_DIR  = PROJECT_DIR.joinpath('Generation')
PROCESS_GENERATION_FILE_NAME = 'GenerationFile'

GENYMOTION_FHD_DPI640_RUNESUMMARY_WIDTH = 839 # 639 でコメントなしになる。
GENYMOTION_FHD_DPI640_RUNESUMMARY_HEIGHT = 652

JSON_SAVE_DIR  = PROJECT_DIR.joinpath('program','fastapi','dev')
JSON_FILE_NAME = 'results.json'
JSON_FILE_PATH = JSON_SAVE_DIR.joinpath(JSON_FILE_NAME)

TEMPLATE_SYMBOLS_DIR = TEMPLATE_IMG_DIR.joinpath('ocr')

files = [v.as_posix() for v in RESULT_DIR.glob('./*.png') ]

# ocr の事前準備
tools = pyocr.get_available_tools()
tool  = tools[0]

view = True
MASTER_RECORD = []
def main(files=files):
    global TEMPLATE_SYMBOLS_DIR
    
    for file in files:
    
        Abilities = {}
        
        #画像認識したいファイルを取得
        # 能力値が記載されているコンテナだけ取得
        targetfile = cv2.imread(filename=file)
        templateLeftUp    = cv2.imread(TEMPLATE_SYMBOLS_DIR.joinpath('container_ability_leftup.png').as_posix())
        templateRightDown = cv2.imread(TEMPLATE_SYMBOLS_DIR.joinpath('container_ability_rightdown.png').as_posix())
        
        pos_leftup        = cv2.minMaxLoc( cv2.matchTemplate(targetfile, templateLeftUp, cv2.TM_CCOEFF_NORMED) )
        pos_rightdown     = cv2.minMaxLoc( cv2.matchTemplate(targetfile, templateRightDown, cv2.TM_CCOEFF_NORMED) )
        
        box = (pos_leftup[3][0] , pos_leftup[3][1], pos_rightdown[3][0], pos_rightdown[3][1])
        
        with tempfile.NamedTemporaryFile( dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix=f'_crop_ability.png', delete=False) as AbilityContainerFp:
            def filesave():
                image = Image.open(RESULT_DIR.joinpath(file).as_posix())
                try:
                    image.crop(box).save(AbilityContainerFp.name, quality=100)
                except:
                    tmpimage = cv2.imread(RESULT_DIR.joinpath(file).as_posix())
                    cv2.imshow('test', tmpimage)
                    cv2.waitKey(0)
                    cv2.destroyAllWindows()
            
            with ThreadPoolExecutor(max_workers=100) as executor:
                executor.submit( filesave() )
        
        #+ LineBoxで座標を取得する前に[MAX]の表示を黒で塗りつぶしておく
        #* 複数の座標が取得できた時はまとめて処理する。
        def PreprocessFillMax(resource_dir=TEMPLATE_SYMBOLS_DIR):
            template = cv2.imread(resource_dir.joinpath('max.png').as_posix())
            
            while True:
                baseimage = cv2.imread(AbilityContainerFp.name)
                
                filling_start_position = cv2.minMaxLoc( cv2.matchTemplate(baseimage, template, cv2.TM_CCOEFF_NORMED) )
                
                if filling_start_position[1] < 0.9:
                    return
                else:
                    # 囲む範囲を作成する
                    filling_area = (
                        (filling_start_position[3][0], filling_start_position[3][1]),
                        (filling_start_position[3][0] + template.shape[1], filling_start_position[3][1] + template.shape[0])
                    )
                    
                    cv2.rectangle(
                        img=baseimage,
                        pt1=filling_area[0],
                        pt2=filling_area[1],
                        thickness=-1,
                        color=(0, 0, 0)
                    )
                    
                    
                    print(f'[ {fg.DARKCYAN}{sys._getframe().f_code.co_name}{fg.END} ]',f'OpenCV did draw rectangle {filling_area}')
                    cv2.imwrite(AbilityContainerFp.name, baseimage)
                    
                # testcode preview
                #?cv2.imshow("baseimage_preprocess", baseimage)
                #?cv2.waitKey(0)
                #?cv2.destroyAllWindows()
                
        with ProcessPoolExecutor() as executor:
            executor.submit( PreprocessFillMax() )
        
        # 白黒にして一時ファイルで保存（必要ならoptimizeもする）
        # https://qiita.com/tokkuri/items/ad5e858cbff8159829e9
        
        binaryThreshold = 190
        with tempfile.NamedTemporaryFile( dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix=f'_toBinary{binaryThreshold}.png') as binariedFp:
            targetfile = cv2.imread(AbilityContainerFp.name, 0)
            ret, binaried = cv2.threshold(targetfile, binaryThreshold, 255, cv2.THRESH_BINARY_INV)
            
            #?cv2.imshow("", mat=binaried)
            #?cv2.waitKey(0)
            #?cv2.destroyAllWindows()
            
            cv2.imwrite(binariedFp.name, img=binaried)
            
            # LineBox
            res = tool.image_to_string( Image.open(binariedFp.name), lang='jpn', builder=pyocr.builders.LineBoxBuilder(tesseract_layout=6) )
            
        #? Testcode
        out = cv2.imread(filename=AbilityContainerFp.name)
        for d in res:
            #?print (d.content)
            #?print (d.position)
            cv2.rectangle(out, d.position[0], d.position[1], (0, 0, 255), 1)
    
        #?cv2.imshow('image', out)
        #?cv2.waitKey(0)
        #?cv2.destroyAllWindows()
        #+ メインオプションを保存する
        
        Abilities['Main'] = { 'position': res[0].position }
        
        #? print(len(res))
        #pprint.pprint(res)
        
        if len(res) >= 2:
            Abilities['Sub'] = { 'position': res[1].position }
        
        #print('stoppoint', len(res[0].position), res[1].position, res)
        
        #- サブオプションを取得する。
        binaryThreshold = 130
        with tempfile.NamedTemporaryFile( dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix=f'_toBinary{binaryThreshold}.png') as binariedFp:
            targetfile = cv2.imread(AbilityContainerFp.name, 0)
            ret, binaried = cv2.threshold(targetfile, binaryThreshold, 255, cv2.THRESH_BINARY_INV)
            
            #? cv2.imshow("", mat=binaried)
            #? cv2.waitKey(0)
            #? cv2.destroyAllWindows()
            cv2.imwrite(binariedFp.name, img=binaried)
            
            # LineBox
            res = tool.image_to_string( Image.open(binariedFp.name), lang='jpn', builder=pyocr.builders.LineBoxBuilder(tesseract_layout=6) )
        
        before_count = len(Abilities)
        for i, item in enumerate(res, 1):
            if i <= before_count:
                continue
            else:
                Abilities[f'{i - before_count}'] = { 'position': res[i - 1].position }
        
        
        print(clr.DARKCYAN, 'Abilities Position\n', clr.END, clr.YELLOW, Abilities, clr.END)
        
        # AbilityContainerFp（アビリティ枠を切り取っただけの色付き画像）を(白黒として)被テンプレートマッチング画像として読み込む
        image = cv2.imread(AbilityContainerFp.name, flags=0)
        
        # Abilities 辞書をループする。
        
        #p_cpu_cores = psutil.cpu_count(logical=False)
        
        margin = 3
        #   [with] AbilityContainerFpに対して辞書[キー][座標]の範囲を切り取る。(ネストを深くしないようにするために、ここで一度保存しても良い)
        #   - 名前は[キー]_cropped_before.png    
        def AreaCrop(key, area):
            #global Abilities
            
            box = (area[0][0] + 26, area[0][1] - margin, area[1][0] + margin, area[1][1] + margin) # + 20は菱形消すため
            with tempfile.NamedTemporaryFile( dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix=f'_AbilityClass_{key}_cropped_before.png', delete=False) as fp :
                with threading.Lock():
                    image = Image.open(AbilityContainerFp.name)
                    image.crop(box).save(fp.name, quality=100)
                
                Abilities[key]['filename'] = fp.name
                print(f'[ {sys._getframe().f_code.co_name} ]',clr.RED, f'{key} {box} joined', clr.END,"\t", Abilities[key]['filename'])
        
        keyNames = list(Abilities.keys())
        #print('keynames outputs', keyNames, type(keyNames))
        def ConcurrentTask(abilityClass):
                AreaCrop(abilityClass, Abilities[abilityClass]['position'])
                return f'{sys._getframe().f_code.co_name} {abilityClass} end'
        
        for key in keyNames:
            with ThreadPoolExecutor(max_workers=100) as executor:
                executor.submit( ConcurrentTask(key) )
            
        #? print('concurrent task end')
                #globals()[f'mp_{key}'] = Process(target=AreaCrop, args=(key, Abilities[key]['position']))
                #exec(f'mp_{key}.start()')
        
        #for key, value in Abilities[0].items():
        #    exec(f'mp_{key}.join()')
        
        #? print(clr.GREEN, 'stoppoint join', clr.END )
        #? print(clr.DARKCYAN, 'AbilityContainarFp', AbilityContainerFp.name, clr.END )
        #? pprint.pprint([(f'{k} {v}') for k, v in Abilities.items()])
        
        #+   cropped_before.pngに対して、プラス、％、MAXそれぞれのマッチングを行い、該当する範囲を白で塗りつぶす
        TEMPLATE_SYMBOLS_DIR = TEMPLATE_IMG_DIR.joinpath('ocr')
        #TEMPLATE_SYMBOLS_DIR = TEMPLATE_IMG_DIR.joinpath('ocr', 'max.png')
        
        for key in keyNames:
            template_key = TEMPLATE_SYMBOLS_DIR.joinpath(
                'Other' if key in ["1","2","3","4"] else key)
            template_plus      = cv2.imread(TEMPLATE_SYMBOLS_DIR.joinpath(template_key,'plus.png').as_posix())
            template_percent   = cv2.imread(TEMPLATE_SYMBOLS_DIR.joinpath(template_key,'percent.png').as_posix())
            template_max       = cv2.imread(TEMPLATE_SYMBOLS_DIR.joinpath('max.png').as_posix())
            
            varnames = {
                'template_plus': template_plus,
                'template_percent': template_percent,
                'template_max':template_max
            }
            
            SingleAbilityImage = cv2.imread(Abilities[key]['filename'])
            
            def arrayCheck():
                try:
                    Abilities[key]['matched_rate']
                except:
                    Abilities[key]['matched_rate'] = {}
                
                try:
                    Abilities[key]['fill']
                except:
                    Abilities[key]['fill'] = {}
                
                try:
                    Abilities[key]['fill'][varnames_key.replace('template_',"")]
                except:
                    Abilities[key]['fill'][varnames_key.replace('template_',"")] = {}
                    
                try:
                    Abilities[key]['Param']
                except:
                    Abilities[key]['Param'] = {}
                
            #- 各記号（プラスやMax等）をテンプレートとして単体のアビリティに対してテンプレートマッチングを行う。
            for varnames_key in varnames.keys():
                #? testcode sizecheck
                #? print(clr.DARKGREEN, '--------------', clr.END)
                #? print('SingleAbilityImage', SingleAbilityImage.shape[:])
                #? print(varnames_key,varnames[varnames_key].shape[:2])
                try:
                    retvals = cv2.minMaxLoc( cv2.matchTemplate(SingleAbilityImage, varnames[varnames_key], cv2.TM_CCOEFF_NORMED ) ) #テンプレートマッチングの類似率取得
                except:
                    arrayCheck()
                    Abilities[key]['matched_rate'][varnames_key.replace('template_',"")] = (0, 0, (0, 0),(0, 0))
                    Abilities[key]['fill'][varnames_key.replace('template_',"")]['isEnable'] = False
                    print(clr.DARKRED, f'cv2 Error point. Target { Abilities[key]["filename"]}', clr.END)
                    continue
                
                arrayCheck()
                #- 類似率とその開始座標の格納をしてあげる？プラスは必須だが％とMaxは任意になる。それらの類似率が高い時は後の処理で判別しやすくなる。
                Abilities[key]['matched_rate'][varnames_key.replace('template_',"")] = retvals
                
                #* 最大値が0.5以上の時は max_fill: True/False のような値をAbilities辞書に格納する。(文字認識後に％などを付与しやすくする。)
                Abilities[key]['fill'][varnames_key.replace('template_',"")]['isEnable'] = True if (retvals[1] > 0.5) else False
                
                #pprint.pprint(Abilities)
                
                #* 塗りつぶすべき範囲を計算し、格納する。max_fill_area: (座標)として格納する。(テンプレートマッチングの座標+テンプレート画像サイズ)
                if Abilities[key]['fill'][varnames_key.replace('template_','')]['isEnable'] == True:
                    Abilities[key]['fill'][varnames_key.replace('template_',"")]['area'] = (
                        Abilities[key]['matched_rate'][varnames_key.replace("template_","")][3][0],
                        Abilities[key]['matched_rate'][varnames_key.replace("template_","")][3][1],
                        Abilities[key]['matched_rate'][varnames_key.replace("template_","")][3][0] + varnames[varnames_key].shape[1], # 最大類似率の始点座標 + 高さ
                        Abilities[key]['matched_rate'][varnames_key.replace("template_","")][3][1] + varnames[varnames_key].shape[0], # 最大類似率の始点座標 + 横幅
                    )
        """
        print(tc.bg.DARKBLUE, 'Mathced Rate After TemplateMatching - SingleAbility', clr.END, 'mem size', sys.getsizeof(Abilities))
        pprint.pprint(Abilities)
        """
        
        #- 取得した値がしきい値以上(0.5よりも大きい)時( isEnable == True )は、cropped_beforeに対して該当の範囲を黒でぬりつぶしてほぞんする。
        #- ここはできるなら並列実行したいが難しいかも
        #   - 名前は[キー]_cropped_after.pngとする。(withを設けず、最後に消す。)
        fill_key_names = ['max', 'percent', 'plus']
        def DrawRectangle():
            if Abilities[keyName]['fill'][fill_key_name]['isEnable'] == True:
                filled_image = cv2.imread(Abilities[keyName]['filled_filename'])
                cv2.rectangle(
                    filled_image,
                    pt1=( Abilities[keyName]['fill'][fill_key_name]['area'][0] , Abilities[keyName]['fill'][fill_key_name]['area'][1]),
                    pt2=( Abilities[keyName]['fill'][fill_key_name]['area'][2] , Abilities[keyName]['fill'][fill_key_name]['area'][3]),
                    thickness= -1,
                    color=(0, 0, 0)
                )
                cv2.imwrite(filename=Abilities[keyName]['filled_filename'], img=filled_image)
                
                #?cv2.imshow("",filled_image)
                #?cv2.waitKey(0)
                #?cv2.destroyAllWindows()
                
                #print(f'[ {fg.DARKGREEN}Filled{fg.END} ]',f'{fill_key_name}')
                #cv2.imwrite(Abilities[keyName]['filled_filename'], filled_image)
        
        for keyName in keyNames:
            
            Abilities[keyName]['filled_filename'] = "".join(
                [
                    pathlib.Path(Abilities[keyName]['filename']).parent.as_posix(),
                    '/filled_',
                    pathlib.Path(Abilities[keyName]['filename']).name
                ]
            )
            
            if not pathlib.Path(Abilities[keyName]['filled_filename']).exists():
                shutil.copy(Abilities[keyName]['filename'], Abilities[keyName]['filled_filename'])
            
            #print(f'[ {bg.DARKMAGENTA}Current Proccesing{bg.END} ]',Abilities[keyName]['filled_filename'])
            
            for fill_key_name in fill_key_names:
                
                with ThreadPoolExecutor(max_workers=100) as executor:
                    executor.submit( DrawRectangle() )
            #?cv2.imshow("",filled_image)
            #?cv2.waitKey(0)
            #?cv2.destroyAllWindows()
        
        #-   cropped_after.pngに文字認識を行う。ここは並列化可能なはず
        #pprint.pprint(Abilities)
        basicformat = re.compile( r'([0-9]+)|([^\s,+,0-9,%]+)' )
        basicformat2 = re.compile(r'([^\s,+]+)')
            
        for keyName in keyNames:
            
            binaryThreshold = 130 if keyName not in ['Main', 'Sub'] else 190
            with tempfile.NamedTemporaryFile( dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix=f'_binaried_SingleAbilityReading_{binaryThreshold}.png') as binariedFp:
                targetfile = cv2.imread(Abilities[keyName]['filled_filename'], 0)
                ret, binaried = cv2.threshold(targetfile, binaryThreshold, 255, cv2.THRESH_BINARY_INV)
                
                #?cv2.imshow(keyName, mat=binaried)
                #?cv2.waitKey(0)
                #?cv2.destroyAllWindows()
                
                cv2.imwrite(binariedFp.name, img=binaried)
                
                # LineBox
                res = tool.image_to_string( Image.open(binariedFp.name), lang='jpn', builder=pyocr.builders.TextBuilder(tesseract_layout=7) )
            """
            print(f'[{bg.DARKYELLOW}{fg.BLACK}ocr_remake: var "res" check 1{bg.END}]', res)
            print(f'[{bg.DARKCYAN}{fg.BLACK}ocr_remake: var "res" check 2{bg.END}]'); pprint.pprint(Abilities)
            print(f'[{bg.DARKMAGENTA}{fg.BLACK}ocr_remake: var "res" check 3{bg.END}]'); pprint.pprint(Abilities[keyName])
            print(f'[{bg.DARKGREEN}{fg.BLACK}ocr_remake: var "res" check 4{bg.END}]'); pprint.pprint(Abilities[keyName]['Param'])
            """
            # 空白の時は unknownにする。
            try:
                Abilities[keyName]['Param']['Name'] = (basicformat.findall(res)[0][1])
                #Abilities[keyName]['Param']['Name'] = (basicformat2.findall(res)[0]) #! basicformat無印と2の違い
                Abilities[keyName]['Param']['Value'] = "".join( [basicformat.findall(res)[-1][0].replace(".","").replace(",",""),'%' if Abilities[keyName]['fill']['percent']['isEnable'] == True else "" ])
                #Abilities[keyName]['Param']['Value'] = "".join( [basicformat2.findall(res)[-1].replace(".","").replace(",",""),'%' if Abilities[keyName]['fill']['percent']['isEnable'] == True else "" ]) #! basicformat無印と2の違い
            except:
                #+ 今はエラーで流しちゃうけど、多分この画像に対してもう一度スキャンをかけたりすれば通る可能性はある。
                print(f'[{bg.DARKMAGENTA}{fg.RED}ocr_remake: values check Failed{bg.END}]',Abilities[keyName]['Param'])
                Abilities[keyName]['Param']['Name'] = 'Unknown'
                Abilities[keyName]['Param']['Value'] = 'Unknown'
            
            #print(f'[{bg.DARKYELLOW}{fg.BLACK}ocr_remake: values check{bg.END}]',Abilities[keyName]['Param']['Name'], Abilities[keyName]['Param']['Value'])
            
            # 名前と値が同じだった時はunknownとする。
            if Abilities[keyName]['Param']['Name'] == Abilities[keyName]['Param']['Value']:
                Abilities[keyName]['Param']['Name'], Abilities[keyName]['Param']['Value'] = 'unknown', 'unknown'
            
            #print(Abilities[keyName]['Param']['Name'],' +', Abilities[keyName]['Param']['Value'], sep="")
            #? Testcode
            """
            out = cv2.imread(filename=AbilityContainerFp.name)
            for d in res:
                #?print (d.content)
                #?print (d.position)
                cv2.rectangle(out, d.position[0], d.position[1], (0, 0, 255), 1)
                """
        print(fg.GREEN, AbilityContainerFp.name, fg.END)
        def RecordCreate():
            returnRecord = []
            for AbilitiyPoint in list(Abilities.keys()):
                singleAbilityParam = {
                    AbilitiyPoint: {
                        'Name': Abilities[AbilitiyPoint]['Param']['Name'],
                        'Value': Abilities[AbilitiyPoint]['Param']['Value'],
                    }
                }
                
                returnRecord.append(singleAbilityParam)
                
                print(Abilities[AbilitiyPoint]['Param']['Name'],' +', Abilities[AbilitiyPoint]['Param']['Value'], sep="")
            
            returnRecord.append({'file': file})
            
            return returnRecord
        
        MASTER_RECORD.append(RecordCreate())
    [ pathlib.Path(v).unlink(missing_ok=True) for v in WORKING_PICTURE_SAVE_DIR.glob('./*') if re.search(r'.+(before.png|ability.png)', v.as_posix())]
    return MASTER_RECORD

if __name__ == '__main__':
    pprint.pprint( main() )
    
    #   補正する。
        #   Abilities[キー]に"status": 取得ステータスを追加する。
        #   もし、マルチプロセスを行っているならここで待機。

        # メインとサブを切り取り
    #? Testcode
    """
    out = cv2.imread(filename=AbilityContainerFp.name)
    for d in res:
        #? print (d.content)
        #? print (d.position)
        cv2.rectangle(out, d.position[0], d.position[1], (0, 0, 255), 1)
    
    cv2.imshow('image', out)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    os.unlink(AbilityContainerFp.name, exists=True)
    """