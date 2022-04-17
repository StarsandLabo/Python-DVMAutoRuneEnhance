#+ ######### init params #########
import pathlib, sys

from cv2 import CAP_PROP_APERTURE, cvtColor, reduce
PROJECT_DIR = pathlib.Path('/home/starsand/DVM-AutoRuneEnhance/')
sys.path.append(PROJECT_DIR.as_posix())
sys.path.append(PROJECT_DIR.joinpath('tools').as_posix())
sys.path.append(PROJECT_DIR.joinpath('lib', 'python3.10', 'site-packages').as_posix())

WORKING_DIR = PROJECT_DIR.joinpath('work')       
WORKING_PICTURE_SAVE_DIR = WORKING_DIR.joinpath('img')

RESOURCE_DIR = PROJECT_DIR.joinpath('resources')
TEMPLATE_IMG_DIR = RESOURCE_DIR.joinpath('img', 'template')

RESULT_DIR = PROJECT_DIR.joinpath('result')

GENYMOTION_FHD_DPI640_RUNESUMMARY_WIDTH = 639
GENYMOTION_FHD_DPI640_RUNESUMMARY_HEIGHT = 652

# テンプレートマッチングでヒットした近い座標を削除する際、近い座標と範囲する値
debugmode = True
equipPositions = [] # ルーン装着箇所
equipPosition  = None

permissiveRange = 20
masterCount     = 0     # 近似座標削除関数で使用するループ回数のカウント変数(再起処理を行うので外部から与えたい。)
hitPositionList = []    # cv2で取得する、関数に与える座標の配列名。

#* basic modules
import os, pprint, time, statistics, tempfile, datetime, re

#* advanced modules
import numpy as np
from matplotlib import pyplot as plt
import cv2
import pyautogui as pag
#from PIL import ImageGrab as Image
from PIL import Image
import pyscreeze as pysc
import pyocr
from tqdm import tqdm

#* My tools
from tools import colortheme as clr
from tools import reduce_overdetected as rod
from tools.clickcondition import ClickCondition as clcd
from tools.ScreenCapture_pillow import ScreenCapture
from tools.GetUniqueCoordinates import GetUniqueCoordinates
clr.colorTheme()   # initialize


#+++++++++++ main ++++++++++
# 画面キャプチャする。現在のスクリーン状態を
def tmpMatchTemplate(color, template):
    #+ 類似度調査 ディスプレイ全体の画像を取得する。(この機能は別の関数に分離しても良いかも)
    with tempfile.NamedTemporaryFile( dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix='.jpg' ) as tmpf:
        sc = ScreenCapture()
        sc.grab(mode=color, filepath=tmpf.name)
        
        # テンプレート画像, 被検索対象をopencvで読み込む
        cvtempimg = cv2.imread(template)
        baseimage = cv2.imread(tmpf.name)
        
        # テンプレートマッチングする
        matchResult = cv2.matchTemplate(baseimage, cvtempimg, cv2.TM_CCOEFF_NORMED)
    
    # 最大一致率を取得
    matchestValue = cv2.minMaxLoc(matchResult)
    
    return matchestValue

# クリックする座標を取得する
def GetClickPosition(debug=debugmode, confidence=0.8, falseThrough=False, **kwargs):
    ### perfcounter
    time_sta = time.perf_counter() if debug is True else None
    ###
    pos = None
    
    for i in range(1, kwargs['maxtry'] + 1): 
        pos = pag.locateCenterOnScreen( kwargs['template'], grayscale=True, confidence=confidence)
        #print(f'checkpoint: {pos}, {type(pos)}, {[ v for v in pos ]}')
        #input()
        if pos is None:
            time.sleep( kwargs['timeoutsec'] )
            print(f'searching position (try {i} times)') if debug is True else None
            continue
        else:
            if debug == True:
                time_end = time.perf_counter() if debug is True else None
                
                matchestValue = tmpMatchTemplate(color='color', template=kwargs['template'])
                print( "{0} {1} {2}".format(
                                            f'[{sys._getframe().f_code.co_name} ({clr.DARKGREEN}Scene{clr.END}:{clr.DARKYELLOW}{kwargs["scene"]}{clr.END})]: {pos}',
                                            f'{clr.DARKGREEN}perf{clr.END}: {clr.DARKYELLOW}{round( (time_end - time_sta), 2)}{clr.END}',
                                            f'{clr.DARKGREEN}similarity Max{clr.END}: {clr.DARKYELLOW}{matchestValue[1:]}{clr.END}'
                                        )
                    ) if debug is True else None
                
            return pos
    if pos is None:
        if falseThrough == False:
            retval = pag.confirm   (   
                            text      =f'The element that matches the template image was not found on the foreground screen.\n\n scene: {kwargs["scene"]}',
                            title     = 'Timeout',
                            buttons   = ['Exit', 'Retry', 'Ignore']
            )
            if retval == 'Exit':
                sys.exit()
            elif retval == 'Ignore':
                return
            else:
                return GetClickPosition(debug, **kwargs)
        else:
            return 'falseThrough'

def optimize(image, border=170):
    arr = np.array(image)
    # x軸を読み込む
    for i in range(len(arr)):
        # y軸を走査する
        for j in range(len(arr[i])):
            # 対象ピクセルの座標
            pix = arr[i][j]
            if pix[0] < border or pix[1] < border or pix[2] < border:
                arr[i][j] = [255, 255, 255]
            elif pix[0] >= border or pix[1] >= border or pix[2] >= border:
                arr[i][j] = [0, 0, 0]
    return Image.fromarray(arr)

def optimizeGray(image, border=170):
    arr = np.array(image)
    # x軸を読み込む
    for i in range(len(arr)):
        # y軸を走査する
        for j in range(len(arr[i])):
            # 対象ピクセルの座標
            pix = arr[i][j]
            if pix < border:
                arr[i][j] = 255
            elif pix >= border:
                arr[i][j] = 0
    return Image.fromarray(arr)



def GetMoney(lang='eng', engine=6):
    tools = pyocr.get_available_tools()
    tool  = tools[0]
    #
    remainingMoney_templatepath = TEMPLATE_IMG_DIR.joinpath('enhance',f'remainingMoney.png').as_posix()
    remainingMoney_template = cv2.imread(remainingMoney_templatepath, 0)
    remainingMoney_trimedfile = WORKING_PICTURE_SAVE_DIR.joinpath('tmp_remainingMoney_trimed_area.png').as_posix()
    
    #- 強化開始時の所持金を取得する
    remainingMoney = tmpMatchTemplate(
        color='color', 
        template=remainingMoney_templatepath
    )
    remainingMoney_target_coords = [
        remainingMoney[3][0] + 50,
        remainingMoney[3][1] + 13,
        remainingMoney[3][0] + remainingMoney_template.shape[1],
        remainingMoney[3][1] + remainingMoney_template.shape[0] + 30
    ]
    
    with tempfile.NamedTemporaryFile(dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix='.jpg' ) as tmpf:
        # 画面全体のキャプチャを取得する
        remainingMoney = ScreenCapture()
        remainingMoney.grab(mode='color', filepath=tmpf.name)
        
        # 取得したキャプチャを読み込み、トリム、保存する。
        remainingMoney_origin = Image.open(tmpf.name)
        # 画像を加工し、読み取り精度を向上させる。
        # https://zenn.dev/mosu/articles/c33142cdebc0fd
                
        remainingMoney_origin.crop(remainingMoney_target_coords).save(remainingMoney_trimedfile)
    
    with tempfile.NamedTemporaryFile(dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix='.jpg' ) as tmpf:
        remainingMoney_optimized = Image.open(remainingMoney_trimedfile)
        toAnalyze = optimize(remainingMoney_optimized)
        toAnalyze.save(remainingMoney_trimedfile)
        
        #? testcode
        #tmpimg =cv2.imread(remainingMoney_trimedfile, -1)
        #cv2.imshow('temp',tmpimg)
        #cv2.waitKey(0)
        #cv2.destroyAllWindows()
        
        # origin_gray_trimed.crop(arr).save(tmpf.name) crop の書式が不明だったから見本。
        # pyocr で画像を読み込む
        remainingMoney_display = tool.image_to_string( Image.open(remainingMoney_trimedfile), lang=lang, builder=pyocr.builders.TextBuilder(tesseract_layout=engine) )
    return remainingMoney_display

def equipPositionExistsCheck():
    # equipPositions変数が存在しない時はからの配列を作成する。
    try:
        global equipPositions
        equipPositions
    except NameError:
        exec( (f'equipPositions = []') ,globals() )

    # equipPositions変数が存在するが中身が0の場合
    if len(equipPositions) < 1:
        tmparr = {}
        for i in range(1, 7):
            tmpResult = tmpMatchTemplate(color='color',template=TEMPLATE_IMG_DIR.joinpath('runelist',f'frame{i}.png').as_posix() )
            
            # resultのMax valueを配列に格納する。
            tmparr[str(i)]= tmpResult[1]
    
    # 配列から最も値の高いキーを取得する
    equipPositions = max(tmparr, key=tmparr.get)
    return equipPositions

def matchTemplate(originPath, templatePath):
    with tempfile.NamedTemporaryFile( dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix='.png' ) as tmpf:
        # cropように画像変換
        tmp = cv2.imread(equipPositionOriginFilePath)
        # tmp = cv2.imread(equipPositionOriginFilePath, 0) <- これでグレースケールで読み込めているがとりあえずこのループは様子見。治すならあとで
        cv2.imwrite(tmpf.name, cv2.cvtColor(tmp, cv2.COLOR_RGB2GRAY))
        
        #cv2.imshow(mat=tmp,winname='test')
        #cv2.waitKey(0)
        #cv2.destroyAllWindows()
        
        #input(arr)
        origin_gray_trimed = Image.open(tmpf.name)
        origin_gray_trimed.crop(arr).save(tmpf.name)

        # 比較画像の読み込み(強制グレースケール)
        origin_gray_trimed = cv2.imread(tmpf.name, flags=0)
        template_gray = cv2.imread(templatePath, flags=0)
        
        w, h = template_gray.shape[::-1]
        # テンプレートマッチング
        result = cv2.minMaxLoc( cv2.matchTemplate(origin_gray_trimed, template_gray, cv2.TM_CCOEFF_NORMED) )
        print(f'{clr.DARKGREEN}Detection target{clr.END}: {templatePath.split("/")[-1]}: , {clr.DARKYELLOW}similarity Max{clr.END}: {result[1]}')
        
        # 表示
        rectedimage = cv2.rectangle(origin_gray_trimed, result[3],(result[3][0] + w, result[3][1] + h), (0, 0, 255),1 ) # test for dvm
    return result

def toTargetClick(point, sleeptime=3, debug=debugmode, sceneName=None):
    
    pag.click( point ) # 装着箇所を選択する(number引数で指定)
    
    if debugmode:
        print( "{0}".format(
                            f'[{sys._getframe().f_code.co_name} ({clr.DARKGREEN}Scene{clr.END}:{clr.DARKYELLOW}{sceneName}{clr.END})]: {point}'
                        )
        )
    
    time.sleep(sleeptime)

def viewDetectArea(origin, results, template):
        cv2.rectangle (origin, results[3], (results[3][0] + template.shape[1], results[3][1] + template.shape[0]), (0, 0, 255), 1)
        
        cv2.imshow(mat=origin, winname='template')
        cv2.waitKey(0)
        cv2.destroyAllWindows()

#? testcodes
"""
sc = ScreenCapture()

# 一番大本を取得。
equipPositionOriginFilePath = WORKING_PICTURE_SAVE_DIR.joinpath(f'pos{equipPosition}origin.png').as_posix()
posimg = sc.grab(mode='color', filepath=equipPositionOriginFilePath)

# テンプレートマッチングで切り出したい座標を取得(テストデータを用意する)
coordsList = [[552, 536], [672, 536], [1152, 536], [792, 537], [912, 537], [1032, 537], [1393, 538], [1403, 539], [1153, 656], [553, 658], [672, 658], [792, 658], [912, 658], [1032, 658], [1154, 775], [1032, 776], [1273, 776], [912, 777], [1393, 777], [793, 778], [1394, 895], [792, 896], [912, 896], [1032, 896], [552, 897], [672, 897], [1273, 898], [793, 1016], [1153, 1016], [1273, 1016], [673, 1017], [912, 1017], [1032, 1017], [1394, 1017]]

# 画像を読み込む
template_origin = cv2.imread(equipPositionOriginFilePath)
template_frame = cv2.imread('/home/starsand/DVM-AutoRuneEnhance/resources/img/template/runelist/frame1.png')
frame_w, frame_h = template_frame.shape[0],template_frame.shape[1]  # テンプレートのw,h

# 画像を切り出して保存
arr = [coordsList[2][0], coordsList[2][1], (coordsList[2][0] + frame_w), (coordsList[2][1] + frame_h)]

# オリジンからframeを書き出す
with tempfile.NamedTemporaryFile( dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix='.png' ) as tmpTrimmedRune:
    origin = Image.open(equipPositionOriginFilePath)
    trimmedRune = origin.crop(arr).save(tmpTrimmedRune.name)

# 切り出された画像を二値化(場合によって、この前にもう段画像を切り出す工程が必要になるかも(範囲を更に絞らなければならない時))
    # もう一段階画像を絞る
    trimmedRuneCv2 = cv2.imread(tmpTrimmedRune.name)
    template_plus = cv2.imread( '/home/starsand/DVM-AutoRuneEnhance/resources/img/template/runelist/plus15.png' )
    
    plus_result = cv2.minMaxLoc( cv2.matchTemplate(trimmedRuneCv2, template_plus, cv2.TM_CCOEFF_NORMED) )
    secondCropCoords = (
        plus_result[3][0],
        plus_result[3][1],
        plus_result[3][0] + template_plus.shape[1],
        plus_result[3][1] + template_plus.shape[0]
    )
    
    #pillowで読み込んでcropする。
    pil_TrimmedRune = Image.open(tmpTrimmedRune.name)
    
    with tempfile.NamedTemporaryFile( dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix='.png' ) as tmpToBinary:
        pil_TrimmedRune.crop(secondCropCoords).save(tmpToBinary.name)
        
        #? view testcode
        #? cv2.rectangle (trimmedRuneCv2, plus_result[3], (plus_result[3][0] + template_plus.shape[1], plus_result[3][1] + template_plus.shape[0]), (0, 0, 255), 1)
        
        #? cv2.imshow(tmpTrimmedRune.name, trimmedRuneCv2)
        #? cv2.waitKey(0)
        #? cv2.destroyAllWindows()
        
        def optimize(image, border=170):
            arr = np.array(image)
            # x軸を読み込む
            for i in range(len(arr)):
            # y軸を走査する
                for j in range(len(arr[i])):
                    # 対象ピクセルの座標
                    pix = arr[i][j]
                    if pix[0] < border or pix[1] < border or pix[2] < border:
                        arr[i][j] = [255, 255, 255]
                    elif pix[0] >= border or pix[1] >= border or pix[2] >= border:
                        arr[i][j] = [0, 0, 0]
            return Image.fromarray(arr)
        
        with tempfile.NamedTemporaryFile( dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix='.png' ) as BinaryImageForOCR:
            img = optimize( Image.open(tmpToBinary.name), border=220 )
            img.save(BinaryImageForOCR.name)
            
            tools = pyocr.get_available_tools()
            tool  = tools[0]
            
            enhanceLevel = tool.image_to_string( Image.open(BinaryImageForOCR.name), lang='jpn', builder=pyocr.builders.TextBuilder(tesseract_layout=6) )
            
            input(f'\n{clr.DARKYELLOW}character reader result{clr.END}: \U0001F63C {enhanceLevel} {type(enhanceLevel)} \U0001F436')
"""

#+ 画面遷移
#print(clcd.EnterRuneList, type(clcd.EnterRuneList))
if True == False:
    pag.click( GetClickPosition(debug=True, **clcd.OpenListMenu) ) # リストメニューを開く
    pag.click( GetClickPosition(debug=True, **clcd.EnterRuneManagement) ) # ルーン管理画面は入る
    pag.click( GetClickPosition(debug=True, **clcd.EnterRuneList) ) # ルーン一覧画面へ入る
    pag.click( GetClickPosition(debug=True, **clcd.OpenSortMenu) ) # ［整列］を開く
    pag.click( GetClickPosition(debug=True, **clcd.EnhanceInSortMenu,confidence=0.85) ) # [強化]を開く
    pag.click( GetClickPosition(debug=True, **clcd.Ascend) ) # 昇順へ変更する

# equipPositionsがない場合は現在の画面を強化する。
# 各装着箇所の画像とテンプレートマッチングし、最も値が高いところをequipPositionsに代入する。

equipPositionExistsCheck()
posListIntermidiate = []
ancientRuneScaned = False
scanRuneType = 'Standard'

#検出領域を確認するか。
cv2AreaCheck = {
    'singleRuneTrim': False,            # ルーン1つ1つを見極められるか
    'afterReduceDuplicatedArea': False  # 検出結果で近い領域を間引いた後。後の工程でクリックされていく強化対象
}


for position in equipPositions:
    equipPosition = int(position)
    #! 本番は有効
    
    while True:
        if ancientRuneScaned == True:
            break
        else:
            if  scanRuneType == 'Ancient':
                                mesvar = 'Ancient Rune'
            elif scanRuneType == 'Standard':
                                mesvar = 'Normal Rune'
            
            print(f'Scan start(current target {mesvar})')
            #pag.click( GetClickPosition(debug=True, **clcd.Position(number=equipPosition, confidence=0.9) ) ); time.sleep(1.5) # 装着箇所を選択する(number引数で指定)sleepは後ろの工程に影響が有るため入れておく
            
            #+ 対象ルーンの検出と、近似座標の削除
            #- 画面全体の画像を取得する。(完成版はtempfileでも良いかも) 余力ができたら取得する画面領域は絞る。
            sc = ScreenCapture()

            # グレースケール変換などを書ける画像のオリジナル。とそのパス
            equipPositionOriginFilePath = WORKING_PICTURE_SAVE_DIR.joinpath(f'pos{equipPosition}origin.png').as_posix()
            posimg = sc.grab(mode='color', filepath=equipPositionOriginFilePath)

            # 判別に使用する画像
            origin = cv2.imread(equipPositionOriginFilePath)
            gray   = cv2.cvtColor(origin, cv2.COLOR_BGR2GRAY)

            
            # テンプレート画像を取得(templateはグレースケールに変換した、実際に使用する画像。)※条件によってはグレースケールでなくても良い。
            #templatePath = TEMPLATE_IMG_DIR.joinpath('runelist',f'frame{equipPosition}.png').as_posix()
            # 古代ルーンのスキャン状態に応じてテンプレートのパスを変更する。
            #if scanRuneType == False:
            #    templatePath = TEMPLATE_IMG_DIR.joinpath('runelist',f'frame{equipPosition}.png').as_posix() #! standard
            #else:
            #    templatePath = TEMPLATE_IMG_DIR.joinpath('runelist',f'frame{equipPosition}a.png').as_posix() #! ancient
            
            ancientRuneScaned = True #! 暫定処理(古代ルーンの識別が上手にできたら再開する。)
            templatePath = TEMPLATE_IMG_DIR.joinpath('runelist',f'frame{equipPosition}.png').as_posix() #! standard
            template     = cv2.imread(templatePath, 0)

            # テンプレート画像のサイズを取得
            w, h = template.shape[::-1]

            # テンプレートマッチング(グレースケールのオリジナル画像と、グレースケールのテンプレート画像のマッチング)
            result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
            resMinMaxLoc = cv2.minMaxLoc(result)

            #input(result)

            # マッチング結果が threshold と比較した値にマッチする範囲を取得
            #threshold = 0.695 ## 0.69付近で星6の画像で★6を取得できてる。(template2.png) / (0.695: template3.png)
            # 装着箇所によってスレッショルドを変更する。
            #- 検出内容が左右にずれるときが有るが、鍵マークの検出はずれていない検出時と同じのため、とりあえず実装する。多分テンプレートマッチングより機械学習のほうがこの辺はいける？
            #input(f'{scanRuneType},{equipPosition}')
            matchingThresholdTable = {
                
                    'Standard': {
                        1: 0.575,
                        2: 0.52,   # 古代ルーンも行ける。ただし、下2列が間引かれる。
                        3: 0.525,   # 古代ルーンも行ける。ただし、下2列が間引かれる。
                        4: 0.525,    # 古代ルーンも行ける。ただし、下2列が間引かれる。
                        5: 0.525, # 古代ルーンも行ける。ただし、下2列が間引かれる。
                        6: 0.525
                    },
                    'Ancient': {
                        1: 0.8
                    }
                    
            }
            
            
            threshold = matchingThresholdTable[scanRuneType][equipPosition] ## 0.53がギリギリダイヤとかを検出しないところ / (0.695: template3.png) 現状0.53 Ancient時はもう少し高くても良いかも 0.55ぐらいじゃないと鍵付きとってくれないかも
            locate = np.where(result >= threshold)

            
            if cv2AreaCheck['singleRuneTrim'] == True:
                for item in zip(*locate[::-1]):
                    cv2.rectangle (origin, (item[0], item[1]) , (item[0] + template.shape[1], item[1] + template.shape[0]), (0, 0, 255), 1)
                
                cv2.imshow(mat=origin, winname=templatePath)
                cv2.waitKey(0)
                cv2.destroyAllWindows()
                
                input('input waiting')

            # 検出結果から近似の座標を間引くために、座標を配列に格納
            #input(f'{type(locate)}, {locate}')
            print(clr.DARKRED + f'(1) locateで取得できた値を、ひとつの配列にまとめる ' + clr.END) if debugmode == True else None
            for pointx, pointy in zip(*locate[::-1]):
                #print(f'var point({len(locate[0])}): {pointx, pointy}')
                
                posListIntermidiate.append([pointx, pointy])
            #input(posListIntermidiate)
            
            # 古代ルーンモードに応じた処理。古代ルーンが未処理の時、自戒ループで処理するようにする。
            # 古代ルーンモードがすでにON時、ループを終了する。
            if scanRuneType == False:
                scanRuneType = True
            elif scanRuneType == True:
                ancientRuneScaned = True
                break
    #古代ルーン補完モードここまで
    
    print(len(posListIntermidiate))
    posListIntermidiate_count = len(posListIntermidiate)

    if debugmode == True:
        print(f'[{clr.DARKGREEN}matchTemplateResult{clr.END}] count:{len(posListIntermidiate)}, threshold: {threshold}')

    # 近似する値を削除していく。
    masterCount = 0
    #reducedPositionList = rod.reduceOverDetectedCoordinates(masterPositionList=posListIntermidiate, count=masterCount, permissive=permissiveRange)
    #?import pyperclip
    #?pyperclip.copy(str(posListIntermidiate))
    #input()
    reducedPositionList = GetUniqueCoordinates(posListIntermidiate, templateImagePath=templatePath, permissiveRate=50)
    
    if cv2AreaCheck['afterReduceDuplicatedArea'] == True:
        for item in reducedPositionList:
            cv2.rectangle (origin, (item[0], item[1]) , (item[0] + template.shape[1], item[1] + template.shape[0]), (0, 0, 255), 1)
        
        cv2.imshow(mat=origin, winname=templatePath)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

        input( clr.cprint(f'Current Equip point: {equipPosition}', clr.YELLOW) )

    
    input(f'rplist {reducedPositionList}')
    
    if debugmode == True:
        print(f'[{clr.DARKGREEN}reduceOverDetectedCoordinates{clr.END}] Result: {( len(reducedPositionList) - posListIntermidiate_count)  * -1 } items reduced.')
    
    #input()
    #+ +++++++++++ 配列に格納されている座標のルーンが、強化してもよいかどうか判別する。++++++++++++

    #- 近似した値が削除された配列にテンプレート画像のw, hを加算し、トリミングする範囲をoriginから取得する。

    #- pillowでトリムする範囲を配列へ格納。whileでも良いかもしれない。
    passedItems = []    # チェックを抜けた座標が格納される。
    # 鍵、プラスチェック
    # 強化画面へ遷移する際は、テストデータを予め用意しておいて対応。
    for i, v in enumerate(reducedPositionList):
        print('-' * len( f'idx: {i}, targetCoordinates:[{v[0]}, {v[1]}, {v[0] + w}, {v[1] + h}]') )
        print(f'{clr.DARKRED}idx{clr.END}: {i}, {clr.DARKYELLOW}targetCoordinates{clr.END}:[{v[0]}, {v[1]}, {v[0] + w}, {v[1] + h}]')
        print('-' * len( f'idx: {i}, targetCoordinates:[{v[0]}, {v[1]}, {v[0] + w}, {v[1] + h}]'))

        arr = [v[0], v[1], (v[0] + w), (v[1] + h)]
        
        # オリジンを読み込み、グレースケールで書き出す。
        with tempfile.NamedTemporaryFile( dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix='.png' ) as tmpOrigin:
            tmp = cv2.imread(equipPositionOriginFilePath)
            cv2.imwrite(tmpOrigin.name, cv2.cvtColor(tmp, cv2.COLOR_RGB2GRAY))
            
            #- 画像をトリミングし保存する。#equipPositionOriginFilePathはRGB
            with tempfile.NamedTemporaryFile( dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix='.png' ) as tmpTrimmedRuneFromOrigin:
                
                # オリジンから検査対象を切り抜いて保存。
                origin_gray_trimed = Image.open(tmpOrigin.name)
                origin_gray_trimed.crop(arr).save(tmpTrimmedRuneFromOrigin.name)
                
                #- トリムされた画像からテンプレート(鍵マーク)を検出
                # 鍵マークを読み込み、グレースケール変換
                template_key  = Image.open(TEMPLATE_IMG_DIR.joinpath('runelist','lock.png').as_posix())
                template_key2 = np.array(template_key, dtype=np.uint8)
                template_key3  = cv2.cvtColor(template_key2, cv2.COLOR_RGB2GRAY)
                
                with tempfile.NamedTemporaryFile( dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix='.png' ) as tmpKeySymbol:
                    # トリムされた鍵マークの画像を書き出す。
                    cv2.imwrite(tmpKeySymbol.name, template_key3)
                    template_key_gray = cv2.imread(tmpKeySymbol.name)
                
                    # 検査対象(ルーンひとつ分)のグレースケール画像を読み込む
                    inspectionTarget = cv2.imread(tmpTrimmedRuneFromOrigin.name)
                    
                    # テンプレートマッチングして、信頼度を比較する。
                    result_key = cv2.minMaxLoc( cv2.matchTemplate(inspectionTarget, template_key_gray, cv2.TM_CCOEFF_NORMED) )
                    
                    # 検出範囲を確認する場合はareacheck = True
                    areacheck = False
                    if areacheck == True: viewDetectArea(inspectionTarget, result_key, template_key_gray)
                    
                    if debugmode == True:
                        if result_key[1] <= 0.9 and result_key[1] >= 0.7:
                            
                            areacheck = False
                            if areacheck == True: viewDetectArea(inspectionTarget, result_key, template_key_gray)
                        else:
                            print(f'{clr.DARKGREEN}Detection target{clr.END}: {TEMPLATE_IMG_DIR.joinpath("runelist","lock.png").as_posix().split("/")[-1]}, {clr.DARKYELLOW}similarity Max{clr.END}: {result_key[1]}')
                    
                # 鍵マークのwith を閉じる
                # 比較結果の信頼値が低い場合は continue する。
                if result_key[1] <= 0.7:
                    print(f'{clr.DARKGREEN}Detection target{clr.END}: {TEMPLATE_IMG_DIR.joinpath("runelist","lock.png").as_posix().split("/")[-1]}, {clr.DARKYELLOW}similarity Max{clr.END}: {result_key[1]}, {clr.RED}Lock symbol check did not pass{clr.END}')
                    continue
                    
                #? 現在withで開かれているのは、大本のオリジンと、検査対象(ルーンひとつ分の画像)
                #? 実際の想定はtmpTrimmedRuneFromOrigin.name
                def MatchWithOCRGray(templatePath, originPath=None, threshold=None, withoutOCR=True, **kwargs):
                    # テンプレートマッチングで検査される側(origin)とテンプレートをcv2に取り込む
                    runeOrigin = cv2.imread(originPath)
                    plus_template = cv2.imread(templatePath)
                    
                    plus_results = cv2.minMaxLoc( cv2.matchTemplate(runeOrigin, plus_template, cv2.TM_CCOEFF_NORMED) )
                    cropArea     = (
                        plus_results[3][0],
                        plus_results[3][1],
                        plus_results[3][0] + plus_template.shape[1],
                        plus_results[3][1] + plus_template.shape[0],
                    )
                    #print(f'{templatePath.split("/")[-1]}: {plus_results}')
                    #? view testcode
                    viewDetectArea = False
                    if viewDetectArea == True:
                        cv2.rectangle (runeOrigin, plus_results[3], (plus_results[3][0] + plus_template.shape[1], plus_results[3][1] + plus_template.shape[0]), (0, 0, 255), 1)
                        
                        cv2.imshow('match result', runeOrigin)
                        cv2.waitKey(0)
                        cv2.destroyAllWindows()
                    else:
                        pass
                    
                    if withoutOCR == False:                    
                        # pillowで読み込む
                        pil_runeOrigin = Image.open(originPath)
                        
                        # pillowでcrop
                        with tempfile.NamedTemporaryFile( dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix='.jpg' ) as tmpExtractEnhancedLevel:
                            pil_runeOrigin.crop(cropArea).save(tmpExtractEnhancedLevel.name)
                            
                            # OCRもーどによって挙動を変化させる。
                            with tempfile.NamedTemporaryFile( dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix='.png' ) as tmpBinaryImage:
                                img = optimizeGray ( Image.open(tmpExtractEnhancedLevel.name), border=220 )
                                img.save(tmpBinaryImage.name)
                                #
                                # pyocrを利用して数値を取得する。
                                #
                                tools = pyocr.get_available_tools()
                                tool  = tools[0]
                                
                                enhanceLevel = tool.image_to_string( Image.open(tmpBinaryImage.name), lang='jpn', builder=pyocr.builders.TextBuilder(tesseract_layout=6) )
                                
                        return plus_results, enhanceLevel
                    else:
                        return plus_results
                
                #+ OCRの使用有無でコードを分ける
                witoutOCR = True
                template_plus = TEMPLATE_IMG_DIR.joinpath('runelist','plus.png').as_posix()
                if witoutOCR == True:
                    ret_plusMatch = MatchWithOCRGray(withoutOCR=True, templatePath=template_plus, originPath=tmpTrimmedRuneFromOrigin.name)
                else:
                    ret_plusMatch = MatchWithOCRGray(withoutOCR=False, templatePath=template_plus, originPath=tmpTrimmedRuneFromOrigin.name)
                
                # プラスのマッチ度が高い画像は次の工程に進まない(すでに強化済みという判定)
                if ret_plusMatch[1] > 0.9:
                    print(f'{clr.DARKGREEN}Detection target{clr.END}: {template_plus.split("/")[-1]}: , {clr.DARKYELLOW}similarity Max{clr.END}: {ret_plusMatch[1]}, {clr.RED}Plus symbol check did not pass{clr.END}')
                    continue
                else:
                    arr.append( pysc.center( (arr[0], arr[1], w, h) ) )
                    passedItems.append(arr)
                    
    print(passedItems)
    print('items:', len(passedItems))
    
    # 旧プラス判別
            #旧プラス判別
            #result_plus = matchTemplate(originPath=equipPositionOriginFilePath, templatePath=TEMPLATE_IMG_DIR.joinpath('runelist','plus6.png').as_posix())
            #input( cv2.minMaxLoc(result_plus) )
            #
            #if result_plus[1] >= 0.85:
            #    if debugmode == True:
            #        print(f'{clr.DARKMAGENTA}Will not enhance{clr.END} {arr}: Plus symbol check did not pass. maybe already enhanced.')
            #    continue
            #
            #result_plus = matchTemplate(originPath=equipPositionOriginFilePath, templatePath=TEMPLATE_IMG_DIR.joinpath('runelist','plus9.png').as_posix())
            #if result_plus[1] >= 0.85:
            #    if debugmode == True:
            #        print(f'{clr.DARKMAGENTA}Will not enhance{clr.END} {arr}: Plus symbol check failed. maybe already enhanced.')
            #    continue
                #
            #result_plus = matchTemplate(originPath=equipPositionOriginFilePath, templatePath=TEMPLATE_IMG_DIR.joinpath('runelist','plus12.png').as_posix())
            #if result_plus[1] >= 0.85:
            #    if debugmode == True:
            #        print(f'{clr.DARKMAGENTA}Will not enhance{clr.END} {arr}: Plus symbol check failed. maybe already enhanced.')
            #    continue
            #
            #print(f'{clr.CYAN}Runes proceed to the enhancement process.{clr.END}')
            #
            #input()
            #- 後ろの工程で利用する、強化対象ルーンの中心座標を追加(pyscreeze.center()関数)
            # pyscreeze モジュールに有るcenter関数を借りて、クリックしたいPoint(x, y)を得る。
            #def center(coords):
            #    
            #    Returns a `Point` object with the x and y set to an integer determined by the format of `coords`.
            #
            #    The `coords` argument is a 4-integer tuple of (left, top, width, height).
            #arr.append( pysc.center( (arr[0], arr[1], w, h) ) )
        #passedItems.append(arr)
    
    
    #pag.click( GetClickPosition(debug=True, **clcd.EquipPosition(number=equipPosition, confidence=0.9) ) ) # 装着箇所を選択する(number引数で指定)

    #- moveToはテスト用。
    #pag.moveTo( passedItems[0][-1] ) # 装着箇所を選択する(number引数で指定)
    #? passed Item テストデータ(毎回取得する必要は有る)
    #passedItems = [[1274, 537, 1391, 654, Point(x=1332, y=595)], [1394, 539, 1511, 656, Point(x=1452, y=597)], [553, 659, 670, 776, Point(x=611, y=717)], [793, 660, 910, 777, Point(x=851, y=718)], [552, 778, 669, 895, Point(x=610, y=836)], [672, 778, 789, 895, Point(x=730, y=836)], [792, 778, 909, 895, Point(x=850, y=836)], [913, 779, 1030, 896, Point(x=971, y=837)], [1034, 779, 1151, 896, Point(x=1092, y=837)], [1154, 779, 1271, 896, Point(x=1212, y=837)], [1274, 779, 1391, 896, Point(x=1332, y=837)], [1395, 779, 1512, 896, Point(x=1453, y=837)], [552, 899, 669, 1016, Point(x=610, y=957)], [674, 899, 791, 1016, Point(x=732, y=957)], [793, 899, 910, 1016, Point(x=851, y=957)], [913, 899, 1030, 1016, Point(x=971, y=957)], [1033, 899, 1150, 1016, Point(x=1091, y=957)], [1154, 899, 1271, 1016, Point(x=1212, y=957)], [1275, 899, 1392, 1016, Point(x=1333, y=957)], [1394, 899, 1511, 1016, Point(x=1452, y=957)], [1395, 1019, 1512, 1136, Point(x=1453, y=1077)], [673, 1021, 790, 1138, Point(x=731, y=1079)], [913, 1021, 1030, 1138, Point(x=971, y=1079)], [1034, 1021, 1151, 1138, Point(x=1092, y=1079)]]
    
    for coord in passedItems:
        # 強化画面に遷移する。テスト済み
        if True == True:
            toTargetClick(coord[-1], 0, debug=debugmode, sceneName='PassedItemSelect')    #本番は利用する
            pag.click( GetClickPosition(debug=debugmode,**clcd.EnterEnhance) );time.sleep(2)            #本番は利用する
        
        #レアリティ確認(旧)
        
        #tmpResult = {}
        #for rarerityName in ['LEGEND', 'HERO', 'RARE', 'COMMON']:
        #    template_rarerity = clcd.RarerityCheck(rarerityName)
        #    tmp = tmpMatchTemplate(color='color', template=template_rarerity['template'])
        #    tmpResult[rarerityName] = tmp[1]
        #    #GetClickPosition(debug=debugmode,**clcd.RarerityCheck(rarerityName, confidence=0.95), falseThrough=True)
    
        
        #- レアリティ比較(新)
        def DetectionAreaCheck(templatePath, permissiveRange, threshold=0.8, watchResult=True, reverse=False):
            from tools import reduce_overdetected as rod
            
            #テンプレート画像を読み込む 
            tmpTemplate = cv2.imread(templatePath)
            #input(tmpTemplate.shape[0:2:1])
            
            #テンプレート画像の幅と高さを取得
            w, h = tmpTemplate.shape[0:2:1]
            

            with tempfile.NamedTemporaryFile( dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix='.png' ) as tmpf:
                
                #検出範囲描画先用画像の取得(カラー)
                sc = ScreenCapture()
                sc.grab(mode='color', filepath=tmpf.name)
                
                #検出先を描画したい画像を読み込む
                tmpOrigin = cv2.imread(tmpf.name)
                
                # テンプレートマッチングを実行
                result = cv2.matchTemplate(tmpOrigin, tmpTemplate, cv2.TM_CCOEFF_NORMED)
                
                # テンプレートマッチングがしきい値以上の位置を全て取得
                locate = np.where(result >= threshold)
                
                # 近似の座標を除去する。reverseがonのときは配列を逆さにする
                rarerityCheck_posListIntermidiate = []
                
                if reverse == False:
                    for pointx, pointy in zip(*locate[::-1]):
                        rarerityCheck_posListIntermidiate.append([pointx, pointy])
                elif reverse == True:
                    for pointx, pointy in zip(*locate[::-1]):
                        rarerityCheck_posListIntermidiate.append([pointy, pointx])
                    
                pi = 0 #primaryIndex
                masterCount = 0
                rarerityCheck_reducedPositionList = rod.reduceOverDetectedCoordinates(masterPositionList=rarerityCheck_posListIntermidiate, count=masterCount, permissive=permissiveRange)
                
                # reverse フラグがTrueのときは配列の中身を基に戻す。numpy.int64型だとreverseが使えないかも
                tmparr = []
                if reverse == True:
                    print(f'{type(rarerityCheck_reducedPositionList[0])}:{rarerityCheck_reducedPositionList[0]}')
                    #print(f'{type(rarerityCheck_reducedPositionList[0][0])}:{rarerityCheck_reducedPositionList[0][0]}')
                    for item in rarerityCheck_reducedPositionList:
                        tmparr.append( [item[1], item[0]] )
                    rarerityCheck_reducedPositionList = tmparr
                    

                
                # 領域描画
                if watchResult == True:
                    for point in rarerityCheck_reducedPositionList:
                        cv2.rectangle (tmpOrigin, point, (point[0] + w, point[1] + h), (0, 0, 255), 1)
                
                    #閲覧
                    cv2.imshow('Detection Area',tmpOrigin)
                    cv2.waitKey(0)
                    cv2.destroyAllWindows()
            
            return rarerityCheck_reducedPositionList
        
        detectResult = DetectionAreaCheck(clcd.RarerityCheck_DIA['template'], threshold=0.985, permissiveRange=8, watchResult=False, reverse=True)
        print(f'detectresult\ncoordinates: {detectResult}, items: {len(detectResult)}')
        
        #- 取得された検出結果を比較してレアリティを確定する。
        #TEMPLATE_IMG_DIR = RESOURCE_DIR.joinpath('img', 'template')

        rarerityJudgeTable = {
            4: 'LEGEND',
            3: 'HERO',
            2: 'RARE',
            1: 'COMMON'
        }
        
        rarerityColor = {
            'LEGEND': clr.DARKYELLOW,
            'HERO'  : clr.MAGENTA,
            'RARE'  : clr.DARKCYAN,
            'COMMON': clr.DARKGRAY
        }
        # 旧レアリティ判別
        #rarerityMagicNumbers = {'LEGEND': 12, 'HERO'  : 9, 'RARE'  : 6, 'COMMON': 3 }
        #targetRarerity = max(tmpResult, key=tmpResult.get)
        
        targetRarerity = rarerityJudgeTable[len(detectResult)] #- 新レアリティ判別
        
        print(f"Target Rune rarerity is {rarerityColor[targetRarerity]}{targetRarerity}{clr.END} ")
        
        #強化を押す直前まで設定する。
        pag.click( GetClickPosition(debug=debugmode,**clcd.RepeatCheck) ) # 繰り返しメニューの選択  本番は有効に
        
        check = pag.click( GetClickPosition(debug=debugmode,**clcd.TargetLevelSelect(targetRarerity, confidence=0.9), falseThrough=True) ) # どこまで強化するか選択(本番用コード)
        # クリック時にNGだった場合。(すでにある程度強化されているやつを選択してしまったが、強化メニューに無く再検出を選択した時)
        if check == 'falseThrough':
            # 戻って次ルーンへ。
            pag.click( GetClickPosition(debug=debugmode,**clcd.ReturnLuneList) ); time.sleep(1)
            continue
        
        #-pag.click( GetClickPosition(debug=debugmode,**clcd.TargetLevelSelect(targetRarerity, confidence=0.9), falseThrough=True) ) #! どこまで強化するか選択(テストコード)
        pag.click( GetClickPosition(debug=debugmode,**clcd.SetCommonEnhance) ) # 一般強化の押下(念の為)
        
        # 強化開始のループ
        pag.click( GetClickPosition(debug=debugmode,**clcd.StartEnhance) ) # 本番は有効
        #TEMPLATE_IMG_DIR.joinpath('enhance',rarerityMagicNumbers[targetRarerity['rarerity']]
        
        # 現在の強化状態を確認してレアリティに即したレベルまで強化されている確認する。
        #+ 意外にも類似率はばらつきがあり、かつ95といった高い数値ではなかった。
        
        remainingMoney_templatepath = TEMPLATE_IMG_DIR.joinpath('enhance',f'remainingMoney.png').as_posix()
        remainingMoney_template = cv2.imread(remainingMoney_templatepath, 0)
        remainingMoney_trimedfile = WORKING_PICTURE_SAVE_DIR.joinpath('tmp_remainingMoney_trimed_area.png').as_posix()
        
        matchResult = None
        EnhanceStartTime = time.time()

        tools = pyocr.get_available_tools()
        tool  = tools[0]

        #強化回数を取得するようのテンプレート

        #正規表現条件を先に選択
        notNumber = re.compile(r'[^0-9]')

        startMoney = GetMoney()
        startMoney = startMoney.replace(".","").replace(",","")

        consumption = None
        
        if notNumber.search(startMoney) is None:
            try:
                consumption = int(startMoney) - int(startMoney)
            except:
                input(startMoney)
                consumption = 'unknown'
        else:
            startMoney  = 'unknown'
            consumption = 'Sorry. current cache could not detect well.'
        
        currentMoney = startMoney
        #input(startMoney)
        
        pyocrlang = 'jpn'
        pyocrbuilder = pyocr.builders.TextBuilder(tesseract_layout=6)
        
        #-  ##############################################################################################
        #!  public static void main()
        #-  ##############################################################################################
        MagicNumberTable = {
                'LEGEND': 12,
                'HERO': 9,
                'RARE': 6,
                'COMMON': 3
        }
        while True:
            
            # 監視間隔が密だと負荷が増えるため、sleepを置く
            print(f'Elapsed time: {int( time.time() - EnhanceStartTime)} sec, Consumption amount: {clr.RED}{consumption}{clr.END}')
            time.sleep(0.5)
            

            matchResult = tmpMatchTemplate(
                color='color', 
                template=TEMPLATE_IMG_DIR.joinpath('enhance',f'enhanced_{MagicNumberTable[targetRarerity]}.png').as_posix()
            )
            
           # トリミング
            currentMoney = GetMoney()
            currentMoney.replace(".","").replace(",","")
            
            # トリミング結果に更に数字以外のものが含まれていたら例外的な処理をする。
            if (currentMoney) is int:
                consumption = int(currentMoney) - int(startMoney)
            else:
                consumption = 'Sorry. current cache could not detect well.'
            
            #print(f"remaining money: {TEMPLATE_IMG_DIR.joinpath('enhance',f'enhanced_{MagicNumberTable[targetRarerity]}.png').as_posix()}, {matchResult}, {matchResult[1]}")
            
            if int( matchResult[1] * 100 ) >= 97:
                break
            else:
                continue
        print(f'Consumption amount: {clr.RED}{consumption}{clr.END}')
        
        pag.click( GetClickPosition(debug=debugmode,**clcd.ReturnLuneList) ); time.sleep(1) # 終了時は元の画面に戻る。sleepは調整用
        
        #+ ルーン強化後のサマリを取得
        #テンプレートマッチングで座標を取得。
        runeSummaryMatchResult = tmpMatchTemplate(color='color', template=clcd.GetSummarySpace['template'])
        #print(f'retval w: {coords_w} ')
        
        summary_width = GENYMOTION_FHD_DPI640_RUNESUMMARY_WIDTH
        summary_height = GENYMOTION_FHD_DPI640_RUNESUMMARY_HEIGHT
        
        runeSummaryCoords = [
            runeSummaryMatchResult[3][0],
            runeSummaryMatchResult[3][1],
            runeSummaryMatchResult[3][0] + summary_height,
            runeSummaryMatchResult[3][1] + summary_width
        ]
        
        with tempfile.NamedTemporaryFile(dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix='.jpg' ) as tmpf:
            # 画面全体のキャプチャを取得する
            remainingMoney = ScreenCapture()
            remainingMoney.grab(mode='color', filepath=tmpf.name)
            
            # 消費金額の状態によって変数の値を変更する。開始時点の金額が読み込めない場合、終了時も文字列が格納されるため。
            if type(consumption) is int:
                consumption *= -1
            else:
                consumption = "unknown"
            
            # 取得したキャプチャを読み込み、トリム、保存する。
            remainingMoney_origin = Image.open(tmpf.name)
            remainingMoney_origin.crop(runeSummaryCoords).save(RESULT_DIR.joinpath(
                    f"{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}-" + f'Position_{equipPosition}-{targetRarerity}-' +f'{startMoney}' + '.jpg'
                )
            )
