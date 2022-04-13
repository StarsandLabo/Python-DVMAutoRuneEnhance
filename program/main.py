#+ ######### init params #########
from dataclasses import replace
from hashlib import new
import pathlib, sys

from cv2 import cvtColor, reduce
PROJECT_DIR = pathlib.Path('/home/starsand/DVM-AutoRuneEnhance/')
sys.path.append(PROJECT_DIR.as_posix())
sys.path.append(PROJECT_DIR.joinpath('tools').as_posix())
sys.path.append(PROJECT_DIR.joinpath('lib', 'python3.10', 'site-packages').as_posix())

WORKING_DIR = PROJECT_DIR.joinpath('work')       
WORKING_PICTURE_SAVE_DIR = WORKING_DIR.joinpath('img')

RESOURCE_DIR = PROJECT_DIR.joinpath('resources')
TEMPLATE_IMG_DIR = RESOURCE_DIR.joinpath('img', 'template')

RESULT_DIR = PROJECT_DIR.joinpath('result')

# テンプレートマッチングでヒットした近い座標を削除する際、近い座標と範囲する値
permissiveRange = 10
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

#* My tools
from tools import colortheme as clr
from tools import reduce_overdetected as rod
from tools.clickcondition import ClickCondition as clcd
from tools.ScreenCapture_pillow import ScreenCapture
import pyscreeze as pysc
import pyocr

clr.colorTheme()   # initialize


#+++++++++++ main ++++++++++
debugmode = True

def tmpMatchTemplate(color, template, ocr=None):
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

# リストメニュを開き、ルーン画面遷移アイコンをクリックする。
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
                            buttons   = ['Exit', 'Retry']
            )
            if retval == 'Exit':
                sys.exit()
            else:
                return GetClickPosition(debug, **kwargs)
        else:
            pass



#+ 画面遷移
equipPosition = 1 # 装着箇所
#print(clcd.EnterRuneList, type(clcd.EnterRuneList))
#pag.click( GetClickPosition(debug=True, **clcd.OpenListMenu) ) # リストメニューを開く
#pag.click( GetClickPosition(debug=True, **clcd.EnterRuneManagement) ) # ルーン管理画面は入る
#pag.click( GetClickPosition(debug=True, **clcd.EnterRuneList) ) # ルーン一覧画面へ入る
#pag.click( GetClickPosition(debug=True, **clcd.OpenSortMenu) ) # ［整列］を開く
#pag.click( GetClickPosition(debug=True, **clcd.EnhanceInSortMenu,confidence=0.85) ) # [強化]を開く
#pag.click( GetClickPosition(debug=True, **clcd.Ascend) ) # 昇順へ変更する
#pag.click( GetClickPosition(debug=True, **clcd.EquipPosition(number=equipPosition, confidence=0.9) ) ) # 装着箇所を選択する(number引数で指定)

#+ 対象ルーンの検出と、近似座標の削除
#- 画面全体の画像を取得する。(完成版はtempfileでも良いかも) 余力ができたら取得する画面領域は絞る。
sc = ScreenCapture()

# グレースケール変換などを書ける画像のオリジナル。とそのパス
capFilepath = WORKING_PICTURE_SAVE_DIR.joinpath(f'pos{equipPosition}.png').as_posix()
posimg = sc.grab(mode='color', filepath=capFilepath)

# 判別に使用する画像
origin = cv2.imread(capFilepath)
gray   = cv2.cvtColor(origin, cv2.COLOR_BGR2GRAY)

# テンプレート画像を取得(templateはグレースケールに変換した、実際に使用する画像。)※条件によってはグレースケールでなくても良い。
templatePath = TEMPLATE_IMG_DIR.joinpath('runelist',f'frame{equipPosition}.png').as_posix()
template     = cv2.imread(templatePath, 0)

# テンプレート画像のサイズを取得
w, h = template.shape[::-1]

# テンプレートマッチング(グレースケールのオリジナル画像と、グレースケールのテンプレート画像のマッチング)
result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)

# マッチング結果が threshold と比較した値にマッチする範囲を取得
threshold = 0.695 ## 0.69付近で星6の画像で★6を取得できてる。(template2.png) / (0.695: template3.png)
locate = np.where(result >= threshold)

# 検出結果から近似の座標を間引くために、座標を配列に格納
posListIntermidiate = []
print(clr.DARKRED + f'(1) locateで取得できた値を、ひとつの配列にまとめる ' + clr.END) if debugmode == True else None
for pointx, pointy in zip(*locate[::-1]):
    #print(f'var point({len(locate[0])}): {pointx, pointy}')
    
    posListIntermidiate.append([pointx, pointy])

posListIntermidiate_count = len(posListIntermidiate)

if debugmode == True:
    print(f'[{clr.DARKGREEN}matchTemplateResult{clr.END}] count:{len(posListIntermidiate)}, threshold: {threshold}')

# 近似する値を削除していく。
masterCount = 0
reducedPositionList = rod.reduceOverDetectedCoordinates(masterPositionList=posListIntermidiate, count=masterCount, permissive=permissiveRange)

if debugmode == True:
    print(f'[{clr.DARKGREEN}reduceOverDetectedCoordinates{clr.END}] Result: {( len(reducedPositionList) - posListIntermidiate_count)  * -1 }item reduced.')

#+ +++++++++++ 配列に格納されている座標のルーンが、強化してもよいかどうか判別する。++++++++++++

#- 近似した値が削除された配列にテンプレート画像のw, hを加算し、トリミングする範囲をoriginから取得する。
"""
class GetArea:
    left    = None
    upper   = None
    right   = None
    lower   = None
    
    box     = []
    
    def __init__(self, template_w, template_h, startpoint_x, startpoint_y):
        print(template_w, template_h, startpoint_x, startpoint_y)
        self.left     = template_w
        self.upper    = template_h
        self.right    = startpoint_x + template_w
        self.lower    = startpoint_y + template_h
        
        self.box.append(startpoint_x)         # left
        self.box.append(startpoint_y)         # upper
        self.box.append(startpoint_x + template_w) # right
        self.box.append(startpoint_y + template_h) # lower
"""

def matchTemplate(originPath, templatePath):
    with tempfile.NamedTemporaryFile( dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix='.png' ) as tmpf:
        # cropように画像変換
        tmp = cv2.imread(capFilepath)
        # tmp = cv2.imread(capFilepath, 0) <- これでグレースケールで読み込めているがとりあえずこのループは様子見。治すならあとで
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
        """
        cv2.imshow(winname=f'{templatePath.split("/")[-1]}', mat=rectedimage)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        """
    return result


#- pillowでトリムする範囲を配列へ格納。whileでも良いかもしれない。
passedItems = []    # チェックを抜けた座標が格納される。

""" 強化画面へ遷移する際は、テストデータを予め用意しておいて対応。
for i, v in enumerate(reducedPositionList):
    print('-----------------------------------------')
    print(f'{clr.DARKRED}idx{clr.END}: {i}, {clr.DARKYELLOW}targetCoordinates{clr.END}:[{v[0]}, {v[1]}, {v[0] + w}, {v[1] + h}]')
    print('-----------------------------------------')
    #runePos = GetArea(w, h, v[0], v[1])
    arr = [v[0], v[1], (v[0] + w), (v[1] + h)]
    
    #- PIL でオリジナル画像のファイルパス capFilepathをopenする。
    
    #- 画像をトリミングし保存する。#capfilepathはRGB
    with tempfile.NamedTemporaryFile( dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix='.png' ) as tmpf:
        tmp = cv2.imread(capFilepath)
        # tmp = cv2.imread(capFilepath, 0) <- これでグレースケールで読み込めているがとりあえずこのループは様子見。治すならあとで
        cv2.imwrite(tmpf.name, cv2.cvtColor(tmp, cv2.COLOR_RGB2GRAY))
        
        #cv2.imshow(mat=tmp,winname='test')
        #cv2.waitKey(0)
        #cv2.destroyAllWindows()
        
        #input(arr)
        origin_gray_trimed = Image.open(tmpf.name)
        origin_gray_trimed.crop(arr).save(tmpf.name)
        
        #- トリムされた画像からテンプレート(鍵マーク)を検出する。
        #  トリムされた画像をcv2で開く(グレースケール)
        # TEMPLATE_IMG_DIR.joinpath('runelist','lock.png').as_posix()
        template_key  = Image.open(TEMPLATE_IMG_DIR.joinpath('runelist','lock.png').as_posix())
        
        template_key2 = np.array(template_key, dtype=np.uint8)
        template_key3  = cv2.cvtColor(template_key2, cv2.COLOR_RGB2GRAY)
        
        with tempfile.NamedTemporaryFile( dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix='.png' ) as tmptemplatef:
            cv2.imwrite(tmptemplatef.name, template_key3)
            template_key_gray = cv2.imread(tmptemplatef.name)
        
            # originのグレースケール画像を読み込む
            origin_gray_trimed = cv2.imread(tmpf.name)
            
            # テンプレートマッチングして、信頼度を比較する。
            result_key = cv2.minMaxLoc( cv2.matchTemplate(origin_gray_trimed, template_key_gray, cv2.TM_CCOEFF_NORMED) )
            
            if debugmode == True:
                #print(f'{clr.DARKGREEN}similarity Max{clr.END}: {clr.DARKYELLOW}{result_key[1:]}{clr.END}')
                print(f'{clr.DARKGREEN}Detection target{clr.END}: {templatePath.split("/")[-1]}: , {clr.DARKYELLOW}similarity Max{clr.END}: {result_key[1]}')
            
        # 鍵マークのwith を閉じる
        # 比較結果の信頼値が低い場合は continue する。
        if result_key[1] <= 0.9:
            if debugmode == True:
                print(f'{clr.DARKMAGENTA}Will not enhance{clr.END} {arr}: Key symbol check did not pass')
            continue
        

        #cv2.imshow(mat=origin_gray_trimed, winname='test1')
        #cv2.waitKey(0)
        #cv2.destroyAllWindows()

        
        result_plus = matchTemplate(originPath=capFilepath, templatePath=TEMPLATE_IMG_DIR.joinpath('runelist','plus6.png').as_posix())
        #input( cv2.minMaxLoc(result_plus) )
        
        if result_plus[1] >= 0.85:
            if debugmode == True:
                print(f'{clr.DARKMAGENTA}Will not enhance{clr.END} {arr}: Plus symbol check did not pass. maybe already enhanced.')
            continue
        
        result_plus = matchTemplate(originPath=capFilepath, templatePath=TEMPLATE_IMG_DIR.joinpath('runelist','plus9.png').as_posix())
        if result_plus[1] >= 0.85:
            if debugmode == True:
                print(f'{clr.DARKMAGENTA}Will not enhance{clr.END} {arr}: Plus symbol check failed. maybe already enhanced.')
            continue

        result_plus = matchTemplate(originPath=capFilepath, templatePath=TEMPLATE_IMG_DIR.joinpath('runelist','plus12.png').as_posix())
        if result_plus[1] >= 0.85:
            if debugmode == True:
                print(f'{clr.DARKMAGENTA}Will not enhance{clr.END} {arr}: Plus symbol check failed. maybe already enhanced.')
            continue
        
        print(f'{clr.CYAN}Runes proceed to the enhancement process.{clr.END}')
        
        #- 後ろの工程で利用する、強化対象ルーンの中心座標を追加(pyscreeze.center()関数)
        # pyscreeze モジュールに有るcenter関数を借りて、クリックしたいPoint(x, y)を得る。
        #def center(coords):
        #    
        #    Returns a `Point` object with the x and y set to an integer determined by the format of `coords`.
        #
        #    The `coords` argument is a 4-integer tuple of (left, top, width, height).
        arr.append( pysc.center( (arr[0], arr[1], w, h) ) )
    passedItems.append(arr)
    

if debugmode == True:
    for point in passedItems:
        cv2.rectangle(origin, (point[0], point[1]), (point[2], point[3]), (0, 0, 255),1 ) # test for dvm

#print(passedItems[0][-1])

"""

#pag.click( GetClickPosition(debug=True, **clcd.EquipPosition(number=equipPosition, confidence=0.9) ) ) # 装着箇所を選択する(number引数で指定)
#- moveToはテスト用。
#? テストデータ
#? 次の値は固定のテストデータなので、画面の位置が少しずれたら取り直す。
reducedPositionList = [571, 513], [691, 513], [811, 513], [931, 513], [1171, 513], [1291, 513], [1050, 631], [1171, 631], [1291, 632], [571, 633], [811, 751], [930, 751], [570, 871], [690, 871], [1291, 872], [811, 992], [931, 992], [571, 993], [1292, 993], [691, 994]
#? input(reducedPositionList[0])
arr = [reducedPositionList[0][0], reducedPositionList[0][1], (reducedPositionList[0][0] + w), (reducedPositionList[0][1] + h)]
arr.append( pysc.center( (arr[0], arr[1], w, h) ) )

passedItems.append(arr)

#pag.moveTo( passedItems[0][-1] ) # 装着箇所を選択する(number引数で指定)

def toTargetClick(point, sleeptime=3, debug=debugmode, sceneName=None):
    pag.click( point ) # 装着箇所を選択する(number引数で指定)
    
    if debugmode:
        print( "{0}".format(
                            f'[{sys._getframe().f_code.co_name} ({clr.DARKGREEN}Scene{clr.END}:{clr.DARKYELLOW}{sceneName}{clr.END})]: {point}'
                        )
        )
    
    time.sleep(sleeptime)

def rarerityCheck(): pass

for coord in passedItems:
    #toTargetClick(coord[-1], 0, debug=debugmode, sceneName='PassedItemSelect')
    
    # 強化画面に遷移する。テスト済み
    #pag.click( GetClickPosition(debug=debugmode,**clcd.EnterEnhance) )
    
    #レアリティ確認
    tmpResult = {}
    for rarerityName in ['LEGEND', 'HERO', 'RARE', 'COMMON']:
        template_rarerity = clcd.RarerityCheck(rarerityName)
        tmp = tmpMatchTemplate(color='color', template=template_rarerity['template'])
        tmpResult[rarerityName] = tmp[1]
        #GetClickPosition(debug=debugmode,**clcd.RarerityCheck(rarerityName, confidence=0.95), falseThrough=True)
        
    #- 取得された検出結果を比較してレアリティを確定する。
    #TEMPLATE_IMG_DIR = RESOURCE_DIR.joinpath('img', 'template')
    rarerityMagicNumbers = {
        'LEGEND': 12,
        'HERO'  : 9,
        'RARE'  : 6,
        'COMMON': 3
    }    
    targetRarerity = max(tmpResult, key=tmpResult.get)
    
    #強化を押す直前まで設定する。
    #!pag.click( GetClickPosition(debug=debugmode,**clcd.RepeatCheck) ) # 繰り返しメニューの選択  本番は有効に
    #!pag.click( GetClickPosition(debug=debugmode,**clcd.TargetLevelSelect(rarerityMagicNumbers[targetRarerity], confidence=0.9), falseThrough=False) ) # どこまで強化するか選択(本番用コード)
    #-pag.click( GetClickPosition(debug=debugmode,**clcd.TargetLevelSelect(rarerityMagicNumbers[targetRarerity], confidence=0.9), falseThrough=True) ) #! どこまで強化するか選択(テストコード)
    #!pag.click( GetClickPosition(debug=debugmode,**clcd.SetCommonEnhance) ) # 一般強化の押下(念の為)
    
    # 強化開始のループ
    #!pag.click( GetClickPosition(debug=debugmode,**clcd.StartEnhance) ) # 本番は有効
    #TEMPLATE_IMG_DIR.joinpath('enhance',rarerityMagicNumbers[targetRarerity['rarerity']]
    
    """
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
    """
    # 現在の強化状態を確認してレアリティに即したレベルまで強化されている確認する。
    #+ 意外にも類似率はばらつきがあり、かつ95といった高い数値ではなかった。
    #+ なので強化終了判定は、テンプレートマッチングの結果が一定回数同じであった時強化完了とみなす。
    
    remainingMoney_templatepath = TEMPLATE_IMG_DIR.joinpath('enhance',f'remainingMoney.png').as_posix()
    remainingMoney_template = cv2.imread(remainingMoney_templatepath, 0)
    remainingMoney_trimedfile = WORKING_PICTURE_SAVE_DIR.joinpath('tmp_remainingMoney_trimed_area.png').as_posix()
    
    matchResult = None
    EnhanceStartTime = time.time()

    tools = pyocr.get_available_tools()
    tool  = tools[0]

    #強化回数を取得するようのテンプレート
    def GetMoney():
        tools = pyocr.get_available_tools()
        tool  = tools[0]

        remainingMoney_templatepath = TEMPLATE_IMG_DIR.joinpath('enhance',f'remainingMoney.png').as_posix()
        remainingMoney_template = cv2.imread(remainingMoney_templatepath, 0)
        remainingMoney_trimedfile = WORKING_PICTURE_SAVE_DIR.joinpath('tmp_remainingMoney_trimed_area.png').as_posix()
        
        #強化開始時の所持金を取得する
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
            remainingMoney = ScreenCapture()
            remainingMoney.grab(mode='color', filepath=tmpf.name)
            
            # 取得したキャプチャを読み込み、トリム、保存する。
            remainingMoney_origin = Image.open(tmpf.name)
            remainingMoney_origin.crop(remainingMoney_target_coords).save(remainingMoney_trimedfile)
        
        # origin_gray_trimed.crop(arr).save(tmpf.name) crop の書式が不明だったから見本。
        # pyocr で画像を読み込む
        remainingMoney_display = tool.image_to_string( Image.open(remainingMoney_trimedfile), lang="jpn", builder=pyocr.builders.TextBuilder(tesseract_layout=6) )
        return remainingMoney_display

    #正規表現条件を先に選択
    notNumber = re.compile(r'[^0-9]')

    startMoney = GetMoney()
    print(startMoney)
    startMoney = startMoney.replace(".","")
    print(startMoney)
    #int( remainingMoney_display.replace(".","") )
    consumption = None
    
    if notNumber.search(startMoney) is None:
        consumption = int(startMoney) - int(startMoney)
    else:
        startMoney  = None
        consumption = 'Sorry. current cache could not detect well.'
    
    currentMoney = startMoney
    #input(startMoney)
    
    #-  ##############################################################################################
    #-  ##############################################################################################
    
    while True:
        
        # 監視間隔が密だと負荷が増えるため、sleepを置く
        print(f'Elapsed time: {int( time.time() - EnhanceStartTime)} sec, Consumption amount: {clr.RED}{consumption}{clr.END}')
        time.sleep(0.5)

        matchResult = tmpMatchTemplate(
            color='color', 
            template=TEMPLATE_IMG_DIR.joinpath('enhance',f'enhanced_{rarerityMagicNumbers[targetRarerity]}.png').as_posix()
        )
        
        remainingMoney = tmpMatchTemplate(
            color='color', 
            template=remainingMoney_templatepath
        )
        
        print('remainingMoney values', remainingMoney)
        
        if int( remainingMoney[1] * 100 ) > 90:
            remainingMoney_target_coords = [
                remainingMoney[3][0] + 50,
                remainingMoney[3][1] + 13,
                remainingMoney[3][0] + remainingMoney_template.shape[1],
                remainingMoney[3][1] + remainingMoney_template.shape[0] + 30
            ]
            
            print('remainingMoney_target_coords', remainingMoney_target_coords)
            
            with tempfile.NamedTemporaryFile(dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix='.jpg' ) as tmpf:
                remainingMoney = ScreenCapture()
                remainingMoney.grab(mode='color', filepath=tmpf.name)
                
                # 取得したキャプチャを読み込み、トリム、保存する。
                remainingMoney_origin = Image.open(tmpf.name)
                remainingMoney_origin.crop(remainingMoney_target_coords).save(remainingMoney_trimedfile)
            
            # origin_gray_trimed.crop(arr).save(tmpf.name) crop の書式が不明だったから見本。
            # pyocr で画像を読み込む
            remainingMoney_display = tool.image_to_string( Image.open(remainingMoney_trimedfile), lang="jpn", builder=pyocr.builders.TextBuilder(tesseract_layout=6) )
            
            # トリミング
            currentMoney = remainingMoney_display.replace(".","")
            
            # トリミング結果に更に数字以外のものが含まれていたら例外的な処理をする。
            if notNumber.search(currentMoney) is None:
                consumption = int(currentMoney) - int(startMoney)
            else:
                consumption = 'Sorry. current cache could not detect well.'
            
#           
        
        print(f"remaining money: {TEMPLATE_IMG_DIR.joinpath('enhance',f'enhanced_{rarerityMagicNumbers[targetRarerity]}.png').as_posix()}, {matchResult}, {matchResult[1]}")
        
        if int( matchResult[1] * 100 ) >= 97:
            break
        else:
            continue
    print(f'Consumption amount: {clr.RED}{consumption}{clr.END}')
    
    pag.click( GetClickPosition(debug=debugmode,**clcd.RepeatCheck) ) # 終了時は元の画面に戻る。
    
"""
testcodes
def tmpMatchTemplate(color, template, ocr=None):
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

rarerityMagicNumbers = {
    'LEGEND': 12,
    'HERO'  : 9,
    'RARE'  : 6,
    'COMMON': 3
}  

targetRarerity = 'LEGEND'
templatepath = TEMPLATE_IMG_DIR.joinpath('enhance',f'enhanced_{rarerityMagicNumbers[targetRarerity]}.png').as_posix()
template = cv2.imread(TEMPLATE_IMG_DIR.joinpath('enhance',f'enhanced_{rarerityMagicNumbers[targetRarerity]}.png').as_posix())

matchResult = tmpMatchTemplate(color='color', template=templatepath)

template.shape[0] # x
template.shape[1] # y

with tempfile.NamedTemporaryFile( dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix='.jpg' ) as tmpf:
    sc = ScreenCapture()
    sc.grab(mode='color', filepath=tmpf.name)
    # 
    cvtempimg = cv2.imread(tmpf.name)
    cv2.rectangle(cvtempimg, matchResult[3], (matchResult[3][0] + template.shape[1], matchResult[3][1] + template.shape[0]), (0, 0, 255),1 )
    
    cv2.imshow('matched list', cvtempimg)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

"""
"""
cv2.imshow('matched list', origin)
cv2.waitKey(0)
cv2.destroyAllWindows()
#cv2.imwrite('/home/starsand/choosed.png', origin)
        #sys.exit()


for point in reducedPositionList:
    cv2.rectangle(origin, point, (point[0] + w, point[1] + h), (0, 0, 255),1 ) # test for dvm

cv2.imshow('matched list', origin)
cv2.waitKey(0)
cv2.destroyAllWindows()
"""

sys.exit()


#  オリジナル画像を取得、グレースケール変換
origin  = cv2.imread(ORIGIN_PICTURE_DIR.joinpath('origin_rune_1.png').as_posix())
gray    = cv2.cvtColor(origin, cv2.COLOR_BGR2GRAY)

#  テンプレート画像ををグレースケールで取得。
templatepath = TEMPLATE_PICTURE_DIR.joinpath('template3.png')
template = cv2.imread(templatepath.as_posix(), 0)

#  テンプレート画像のサイズを取得。
w, h = template.shape[::-1]
print(f'image size in {templatepath.parent.as_posix()} : w = {w}, h = {h}')

#  テンプレートマッチング
result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
print(f'number of var result: {len(result)}')
print(f'var result: {result}')

#  マッチング結果が threshold と比較した値にマッチする範囲を取得
threshold = 0.695 ## 0.69付近で星6の画像で★6を取得できてる。(template2.png) / (0.695: template3.png)
locate = np.where(result >= threshold)
#print(f'threshold: {threshold}\nvar locate{locate}')

permissive = 10

newarr =[]
posListIntermidiate =[]

#+ (1) locateで取得できた値を、ひとつの配列にまとめる
print(clr.DARKRED + f'(1) locateで取得できた値を、ひとつの配列にまとめる ' + clr.END)
for pointx, pointy in zip(*locate[::-1]):
    #print(f'var point({len(locate[0])}): {pointx, pointy}')
    
    posListIntermidiate.append([pointx, pointy])

title = 'title'
masterCount = 0
r = rod.recursiveprocess(masterPositionList=posListIntermidiate, count=masterCount, permissive=permissive)

for pos in r:
    cv2.rectangle(origin, pos, (pos[0] + w, pos[1] + h), (0, 0, 255),1 ) # test for dvm


cv2.imshow(title, origin)
cv2.waitKey(0)
cv2.destroyAllWindows()
cv2.imwrite(TEMPLATE_PICTURE_DIR.joinpath('matchresult.png').as_posix(), origin)

