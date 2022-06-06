from concurrent.futures import ThreadPoolExecutor
from doctest import master
from fileinput import filename
import pathlib, sys
from tabnanny import check
from turtle import Screen

from cv2 import CAP_PROP_APERTURE, SparsePyrLKOpticalFlow_create, add, convertPointsFromHomogeneous, cvtColor, reduce
import pyperclip
PROJECT_DIR = pathlib.Path('/home/starsand/DVM-AutoRuneEnhance/')
sys.path.append(PROJECT_DIR.as_posix())
sys.path.append(PROJECT_DIR.joinpath('tools').as_posix())
sys.path.append(PROJECT_DIR.joinpath('lib', 'python3.10', 'site-packages').as_posix())

WORKING_DIR = PROJECT_DIR.joinpath('work')       
WORKING_PICTURE_SAVE_DIR = WORKING_DIR.joinpath('img')

RESOURCE_DIR = PROJECT_DIR.joinpath('resources')
TEMPLATE_IMG_DIR = RESOURCE_DIR.joinpath('img', 'template', 'summary', 'template')

RESULT_DIR = PROJECT_DIR.joinpath('result')

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
import pandas as pd
import pprint
import json
import ast
#* My tools
from tools import colortheme as clr
from tools import reduce_overdetected as rod
from tools.clickcondition import ClickCondition as clcd
from tools.ScreenCapture_pillow import ScreenCapture
from tools.GetUniqueCoordinates import GetUniqueCoordinates
from tools.RuneSummaryTemplates import Templates
from tools import ocr_remake
from tools import RebuildDictionary
from tools import OCR_rs_regex
clr.colorTheme()   # initialize

class regexes:
    import re
    no_plus                 = re.compile(r'(?<!\+)([1|t|l])([^\.,]+)')
    no_plus_mainonly        = re.compile(r'( (14)|(22)|(28)|(34)|(46)|(55) )(.+)')
    digit_three_noexists    = re.compile(r'([^\d])([2-9])(\d){2}')
    digit_four_noexists     = re.compile(r'([^\d])([2-9])(\d){3,}')
    digit_three_percent     = re.compile(r'([^\d])(1\d)(\d.)')
    digit_three_percent_96  = re.compile(r'([^\d])(196)')
    digit_four_percent      = re.compile(r'([^\d])(1\d)(\d){2,}')
    digit_two_noexists      = re.compile(r'([^\d])([2-9])(\d)([^\d])+')
    nine_percent_six        = re.compile(r'9%6$')
    one_zero_nine           = re.compile(r'109')
    double_percent          = re.compile(r'(%%)')
    add_percent             = re.compile(r'(?<!%)$')
    add_plus                = re.compile(r'^([^\+])')
    abilities_only          = re.compile( r'((HP)|(攻.[力|カ])|(防.[力|カ])|(攻..度)|(効果..)|(効..中)|(.リティ.ル率)|(命中)|(回.)|(.リテ..ル.メー.))' )
    operatorAndValue        = re.compile( r'(\+|\d)(\d.*$)' )
    percent_only            = re.compile( r'(攻..度)|(効果..)|(効..中)|(.リ...ル.)|(命中)|(回.)|(.リティ.ル.メー.)')
    abilities               = re.compile( r'((HP)|(攻.[力|カ])|(防.[力|カ])|(攻..度)|(効果..)|(効..中)|(.リティ.ル率)|(命中)|(回.)|(.リテ..ル.メー.)).+(%|\d)' )
    mainoption_tmpseparate  = re.compile( r'((HP)|(攻.[力|カ])|(防.[力|カ])|(攻..度)|(効果..)|(効..中)|(.リティ.ル率)|(命中)|(回.)|(.リテ..ル.メー.))(.+$)' )
    statName                = re.compile(r'^([^\+]+)')
    statValue               = re.compile(r'(\+?\d.+$)')
    position                = re.compile(r'\d番')
    attack                  = re.compile(r'攻.[力|カ]')
    defence                 = re.compile(r'防.[力|カ]')
    plus_and_percent        = re.compile(r'(HP)|(攻.[力|カ])|(防.[力|カ])')
    hp_digit_2_noexists     = re.compile(r'[^\d]?([2-9]).*')
    hp_digit_2_exists       = re.compile(r'[^\d](1\d).*')
    no_comma                = re.compile(r'(\d+)[^\d](\d+)')
    no_plus                 = re.compile(r'(?<!\+)([1|t|l])([^\.,]+)')
    checkIncludePuls        = re.compile(r'[^\+]+')
    speed                   = re.compile(r'攻..度')
    crit_d                  = re.compile(r'.リティ.ル.メー.')


class colorPrints():
    def red(self, coloredtext="",whitetext=""):
        return print(f'\033[38;2;239;41;41m{coloredtext}\033[0m{whitetext}')
    #
    def yellow(self, coloredtext="",whitetext=""):
        return print(f'\033[38;2;237;212;0m{coloredtext}\033[0m{whitetext}')
    #
    def green(self, coloredtext="",whitetext=""):
        return print(f'\033[38;2;138;226;52m{coloredtext}\033[0m{whitetext}')

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
                #arr[i][j] = [0, 0, 0]
            elif pix[0] >= border or pix[1] >= border or pix[2] >= border:
                arr[i][j] = [0, 0, 0]
                #arr[i][j] = [255, 255, 255]
    return Image.fromarray(arr)

def checkColor(image):
    arr = np.array(image)
    # x軸を読み込む
    for i in range(len(arr)):
        # y軸を走査する
        for j in range(len(arr[i])):
            # 対象ピクセルの座標
            pix = arr[i][j]
            if   ( pix[0] > 39 and pix[0] < 59 ):
                                            return 'COMMON'
            elif ( pix[0] > 0 and pix[0] < 18 ):
                                            return 'RARE'
            elif ( pix[0] > 56 and pix[0] < 76 ):
                                            return 'HERO'
            elif ( pix[0] > 72 and pix[0] < 92 ):
                                            return 'LEGEND'
            else:
                print(f'pixel ({i},{j}) color is {pix[0]} {pix[1]} {pix[2]}')
                continue
    """
    color balance(RGB)
    common = 49,53,49
    rare   =  8,32,82
    hero   = 66,12,82
    legend = 82,61, 8
    """
                #arr[i][j] = [255, 255, 255]


def log_pandas(title, titlecolor=clr.DARKYELLOW, **kwargs):
    record = []
    record.append("[")
    record.append(titlecolor + title + clr.END)
    record.append("]" )
    
    for key, value in kwargs.items():
        record.append(clr.MAGENTA + str(key) + ":" + clr.END)
        record.append( str(value) )
    
    df = pd.DataFrame([record])
    
    return df.to_string(index=False, header=False, )

def GetCoordinates(templatePath, check=False):
    with tempfile.NamedTemporaryFile(dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix='.png' ) as origin:
        # 現在の画面キャプチャを取得する
        sc = ScreenCapture()
        sc.grab(mode='color', filepath=origin.name)
        
        # cv2で取得した画面と、比較対象のテンプレートの画像を読み込む
        origin   = cv2.imread(origin.name)
        template = cv2.imread(templatePath)
        
        # テンプレートマッチングをし、MinMaxLocする。
        result = cv2.minMaxLoc( cv2.matchTemplate(origin, template, cv2.TM_CCOEFF_NORMED) )

        logMessages = [
            [
                "[",
                clr.DARKYELLOW + sys._getframe().f_code.co_name + clr.END,
                "]",
                clr.MAGENTA + "Result:" + clr.END,
                result,
                clr.MAGENTA + "TemplatePath:" + clr.END,
                pathlib.Path(templatePath).as_posix()
            ]
        ]
        print(pd.DataFrame(logMessages).to_string(index=False, header=False))
        if check == True:
            h, w = template.shape[0:2]
            cv2.rectangle(origin, result[3],(result[3][0] + w, result[3][1] + h), (0, 0, 255), 1)
            
            cv2.imshow(templatePath, origin)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            
    return result

def GetCoordinatesMulti(templatePath, threshold=0.8, check=False):
    with tempfile.NamedTemporaryFile(dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix='.png' ) as origin:
        # 現在の画面キャプチャを取得する
        sc = ScreenCapture()
        sc.grab(mode='color', filepath=origin.name)
        
        # cv2で取得した画面と、比較対象のテンプレートの画像を読み込む
        origin   = cv2.imread(origin.name)
        template = cv2.imread(templatePath)
        
        # テンプレートマッチングをし、MinMaxLocする。
        result = cv2.matchTemplate(origin, template, cv2.TM_CCOEFF_NORMED)
        locate = np.where(result >= threshold)
        
        logMessages = [
            [
                "[",
                clr.DARKYELLOW + sys._getframe().f_code.co_name + clr.END,
                "]",
                clr.MAGENTA + "Result:" + clr.END,
                clr.DARKRED + str( len(locate[0]) ) + clr.END + ' items found.',
                clr.MAGENTA + "TemplatePath:" + clr.END,
                pathlib.Path(templatePath).as_posix()
            ]
        ]
        
        print(pd.DataFrame(logMessages).to_string(index=False, header=False))
        if check == True:
            h, w = template.shape[0:2]
            for pointx, pointy in zip(*locate[::-1]):
                cv2.rectangle(origin, (pointx, pointy),(pointx + w, pointy + h), (0, 0, 255), 1)
            
            cv2.imshow(templatePath, origin)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            
    return locate


def GetRarerity(targetCoords, templatePath, originPath):
    
    # オリジンから座標を基に画像を切り出す。
    origin = Image.open(originPath)
    template = Image.open(templatePath)
    
    #切り出す領域の指定
    cropCoords = (
        targetCoords[0],
        targetCoords[1],
        targetCoords[0] + template.size[1],
        targetCoords[1] + template.size[0]
    )
    
    with tempfile.NamedTemporaryFile( dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix='.png' ) as trimmed:
        origin.crop(cropCoords).save(trimmed.name)
    
        # cropした画像を読み込み一番左上の画素の色を読み、しきい値かどうか確認する。
        # レアリティが合致しない場合は他のピクセルを読む
        trimmedImage = Image.open(trimmed.name)
        """
        color balance(RGB)
        common = 49,53,49
        rare   =  8,32,82
        hero   = 66,12,82
        legend = 82,61, 8
        """
        
        rarerity = checkColor(trimmedImage)
    
    rarerityColors = {
        'COMMON':'\033[38;2;49;53;49m',
        'RARE'  :'\033[38;2;8;32;82m',
        'HERO'  :'\033[38;2;66;12;82m',
        'LEGEND':'\033[38;2;82;61;8m',
    }
    
    logmessage = [
        [
            "[",
            clr.DARKYELLOW + sys._getframe().f_code.co_name + clr.END,
            "]",
            'Result:',
            rarerityColors[rarerity] + rarerity + clr.END,
        ]   
    ]
    
    print(pd.DataFrame(logmessage).to_string(index=False, header=False))
    
    return rarerity

#- テンプレートのパスを格納するクラス。
template = Templates()

#templatelist = template.list()


if __name__ == '__main__':

    # 先にインスタンスを作成しておく
    sc = ScreenCapture()
    cp = colorPrints()
    rex = regexes()
    pd.set_option('display.unicode.east_asian_width', True)

    #+ 先に取得できる座標を取得する
    #coords_summaryWindow = GetCoordinates(templatePath=template.summary_space['template'], check=False)[3] # サマリウィンドウ
    #- 予め 案内 -> 管理 の順番で画面を移動しておくと、サマリ取得画面に何も表示されないのでテスト時やその他の場面でスムーズに移行できる
    coords_composite     = pag.locateCenterOnScreen(template.composite['template']      , grayscale=False, confidence=0.9); print(log_pandas('locateCenterOnScreen', **{'Result': coords_composite, 'Template': template.composite['template']}) ) # サマリウィンドウ
    coords_guide         = pag.locateCenterOnScreen(template.guide['template']          , grayscale=False, confidence=0.9); print(log_pandas('locateCenterOnScreen', **{'Result': coords_guide, 'Template': template.guide['template']}) ) # サマリウィンドウ
    coords_management    = pag.locateCenterOnScreen(template.management['template']     , grayscale=False, confidence=0.9); print(log_pandas('locateCenterOnScreen', **{'Result': coords_management, 'Template': template.management['template']}) ) # サマリウィンドウ
    pag.click(coords_composite); time.sleep(1.5)
    pag.click(coords_guide); time.sleep(1.5)
    pag.click(coords_management); time.sleep(1.5)

    coords_summaryWindow = pag.locateCenterOnScreen(template.summary_space['template']  , grayscale=False, confidence=0.9); print(log_pandas('locateCenterOnScreen', **{'Result': coords_summaryWindow, 'Template': template.summary_space['template']}) ) # サマリウィンドウ
    coords_set           = pag.locateCenterOnScreen(template.set['template']            , grayscale=False, confidence=0.9); print(log_pandas('locateCenterOnScreen', **{'Result': coords_set, 'Template': template.set['template']}) ) # サマリウィンドウ
    coords_option        = pag.locateCenterOnScreen(template.option['template']         , grayscale=False, confidence=0.9); print(log_pandas('locateCenterOnScreen', **{'Result': coords_option, 'Template': template.option['template']}) ) # サマリウィンドウ

    #print(coords_summaryWindow, coords_set, coords_option)

    #- サマリウィンドウの切り取り範囲を確定する。
    tmpvar = GetCoordinates(template.summary_space['template'])[3]
    get_template_size = Image.open(template.summary_space['template'])
    
    default_value = True
    offcet = 645
    summrary_window_crop_area = (
        tmpvar[0],
        tmpvar[1], #取得位置を誤っていたので補正 -95があるべき値
        tmpvar[0] + get_template_size.size[0],
        tmpvar[1] + get_template_size.size[1]
        )
    
    #input(summrary_window_crop_area)
    #?sc.grab('color','./tmptestimage.png')
    #?testimage = cv2.imread('./tmptestimage.png')
    #?cv2.rectangle(testimage,
    #?              pt1= (summrary_window_crop_area[0], summrary_window_crop_area[1]),
    #?              pt2= (summrary_window_crop_area[2], summrary_window_crop_area[3]),
    #?              thickness=1,
    #?              color=(0, 0, 255)
    #?              )
    #?cv2.imshow('testimage', testimage)
    #?cv2.waitKey(0)
    #?cv2.destroyAllWindows()
    
    #? testcodes
    #? with tempfile.NamedTemporaryFile(dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix='_croparea.png' ,delete=False ) as test_croparea:
    #?    sc.grab(mode='color', filepath=test_croparea.name)
    #?    testcropimg = Image.open(test_croparea.name)
    #?    
    #?    with tempfile.NamedTemporaryFile(dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix='_croppedarea.png' ,delete=False ) as test_croppedarea:
    #?        testcropimg.crop(summrary_window_crop_area).save(test_croppedarea.name)
    #?        print()

    get_template_size.close()

    
    templatePaths =[
        template.pos1s['template'],
        template.pos2s['template'],
        template.pos3s['template'],
        template.pos4s['template'],
        template.pos5s['template'],
        template.pos6s['template']
    ]

    #?print( [ re.search(r'[0-9]',w).group() for w in [ pathlib.Path(v).name for v in templatePaths ] ] )
    
    testmode_2022_06_06 = True
    #testmode_20220603 = False
    coords_positions = []
    
    def ConcurrentTaskGetCoordinateEquipPosition(template):
        coords_positions.append([
            int(re.search(  r'[0-9]',pathlib.Path(template).name).group()),
                        pag.locateCenterOnScreen(template, grayscale=False, confidence=0.95
                    )
                ]
            )
    #- 装着箇所
    """
    tmpvar = pag.locateCenterOnScreen(template.pos1s['template'], grayscale=False, confidence=0.95) if not testmode_2022_06_06 == True else None
    coords_positions.append(tmpvar)
    print(log_pandas('locateCenterOnScreen', **{'Result': tmpvar, 'Template': template.pos1s['template']}) )
    tmpvar = pag.locateCenterOnScreen(template.pos2s['template'], grayscale=False, confidence=0.95) if not testmode_2022_06_06 == True else None
    coords_positions.append(tmpvar)
    print(log_pandas('locateCenterOnScreen', **{'Result': tmpvar, 'Template': template.pos2s['template']}) )
    #if testmode_20220603 == False:
    tmpvar = pag.locateCenterOnScreen(template.pos3s['template'], grayscale=False, confidence=0.95) if not testmode_2022_06_06 == True else None
    coords_positions.append(tmpvar)
    print(log_pandas('locateCenterOnScreen', **{'Result': tmpvar, 'Template': template.pos3s['template']}) )
    tmpvar = pag.locateCenterOnScreen(template.pos4s['template'], grayscale=False, confidence=0.95) if not testmode_2022_06_06 == True else None
    coords_positions.append(tmpvar)
    print(log_pandas('locateCenterOnScreen', **{'Result': tmpvar, 'Template': template.pos4s['template']}) )
    tmpvar = pag.locateCenterOnScreen(template.pos5s['template'], grayscale=False, confidence=0.95)
    coords_positions.append(tmpvar)
    print(log_pandas('locateCenterOnScreen', **{'Result': tmpvar, 'Template': template.pos5s['template']}) )
    tmpvar = pag.locateCenterOnScreen(template.pos6s['template'], grayscale=False, confidence=0.95) if not testmode_2022_06_06 == True else None
    coords_positions.append(tmpvar)
    print(log_pandas('locateCenterOnScreen', **{'Result': tmpvar, 'Template': template.pos6s['template']}) )
    """
    for templatePath in templatePaths:
        with ThreadPoolExecutor(max_workers=60) as executor:
            executor.submit(ConcurrentTaskGetCoordinateEquipPosition, templatePath)
    
    print(coords_positions)
    if testmode_2022_06_06 == True:
        del coords_positions[0:4]
        coords_positions.pop(-1)
    
    #+ セットをクリックする
    pag.click(coords_set); time.sleep(1.5)
    #print(pd.DataFrame([ ["LocateCenterOnScreen", coords_set] ]).to_string(index=False, header=False)); 

    print(log_pandas('locateCenterOnScreen', **{'Status': 'Getting coordinates(initialize)'}) )
    #- 座標を取得する
    coords_setnames = []
    coords_setnames_itempaths = [
        template.set_tairyoku['template'],
        template.set_kikai['template'],
        template.set_koukameityuu['template'],
        template.set_kengo['template'],
        template.set_koukateikou['template'],
        template.set_kyouretu['template'],
        template.set_damage['template'],
        template.set_kaisoku['template'],
        template.set_kyuuketu['template'],
        template.set_meisou['template'],
        template.set_hangeki['template'],
        template.set_seizon['template'],
        template.set_ketui['template'],
        template.set_shuunen['template']
    ]
    #if testmode_20220603 == False:
    def ConcurrentTaskGetCoordinateSetNames(template):
        coords_setnames.append(pag.locateCenterOnScreen(template, grayscale=False, confidence=0.95))
    """
    coords_setnames = (
    pag.locateCenterOnScreen(template.set_tairyoku['template'], grayscale=False, confidence=0.95),
    pag.locateCenterOnScreen(template.set_kikai['template'], grayscale=False, confidence=0.95),
    pag.locateCenterOnScreen(template.set_koukameityuu['template'], grayscale=False, confidence=0.95),
    pag.locateCenterOnScreen(template.set_kengo['template'], grayscale=False, confidence=0.95),
    pag.locateCenterOnScreen(template.set_koukateikou['template'], grayscale=False, confidence=0.95),
    pag.locateCenterOnScreen(template.set_kyouretu['template'], grayscale=False, confidence=0.95),
    pag.locateCenterOnScreen(template.set_damage['template'], grayscale=False, confidence=0.95),
    pag.locateCenterOnScreen(template.set_kaisoku['template'], grayscale=False, confidence=0.95),
    pag.locateCenterOnScreen(template.set_kyuuketu['template'], grayscale=False, confidence=0.95),
    pag.locateCenterOnScreen(template.set_meisou['template'], grayscale=False, confidence=0.95),
    pag.locateCenterOnScreen(template.set_hangeki['template'], grayscale=False, confidence=0.95),
    pag.locateCenterOnScreen(template.set_seizon['template'], grayscale=False, confidence=0.95),
    pag.locateCenterOnScreen(template.set_ketui['template'], grayscale=False, confidence=0.95),
    pag.locateCenterOnScreen(template.set_shuunen['template'], grayscale=False, confidence=0.95)
    )
    """
    for templatePath in coords_setnames_itempaths:
        with ThreadPoolExecutor(max_workers=24) as executor:
            executor.submit(ConcurrentTaskGetCoordinateSetNames, templatePath)
    print(coords_setnames)
#else:
    #    coords_setnames = (
    #        pag.locateCenterOnScreen(template.set_tairyoku['template'], grayscale=False, confidence=0.95),
    #        pag.locateCenterOnScreen(template.set_kikai['template'], grayscale=False, confidence=0.95),
    #        pag.locateCenterOnScreen(template.set_shuunen['template'], grayscale=False, confidence=0.95)
    #    )

    setnames = [
        '体力',
        '機会',
        '効果命中',
        '堅固',
        '効果抵抗', #if testmode_20220603 == False else None,
        '強烈', #if testmode_20220603 == False else None,
        'ダメージ', #if testmode_20220603 == False else None,
        '快速', #if testmode_20220603 == False else None,
        '吸血', #if testmode_20220603 == False else None,
        '瞑想', #if testmode_20220603 == False else None,
        '反撃', #if testmode_20220603 == False else None,
        '生存', #if testmode_20220603 == False else None,
        '決意', #if testmode_20220603 == False else None,
        '執念' #if testmode_20220603 == True else None,
    ]

    #? if testmode_20220603 == True:
    #?     del setnames[2:-2]
    
    #print(pd.DataFrame(coords_setnames).to_string())
    #pprint.pprint(coords_setnames)

    #- 閉じるボタン
    coords_close = pag.locateCenterOnScreen(template.close['template'], grayscale=False, confidence=0.95); print(log_pandas('locateCenterOnScreen', **{'Result': coords_close, 'Template': template.close['template']}) )
    #print(coords_close)
    pag.click(coords_close); time.sleep(1.5)

    # マスタのテーブルを作成する
    mastertable = []

    # ocr の事前準備
    tools = pyocr.get_available_tools()
    tool  = tools[0]

    #? ターゲットの画像を読み込む
    #targetImagePaths = [ p.as_posix() for p in list(RESULT_DIR.glob("**/*.png")) ] ここはtmpfileからヤル。
    #pprint.pprint(targetImagePath)

    #? target regex
    abilities_only = re.compile( r'((HP)|(攻.力)|(防.力)|(攻.速度)|(効果..)|(効果命中)|(クリティカル率)|(命中)|(回.)|(クリティカル.メー.))' )
    operatorAndValue = re.compile( r'(\+|\d)(\d.*$)' )
    percent_only   = re.compile( r'(攻.速度)|(効果..)|(効果命中)|(クリティカル率)|(命中)|(回.)|(クリティカル.メー.)')

    abilities = re.compile( r'((HP)|(攻.力)|(防.力)|(攻.速度)|(効果..)|(効果命中)|(クリティカル率)|(命中)|(回.)|(クリティカル.メー.)).+(%|\d)' )
    mainoption_tmpseparate = re.compile( r'((HP)|(攻.力)|(防.力)|(攻.速度)|(効果..)|(効果命中)|(クリティカル率)|(命中)|(回.)|(クリティカル.メー.))(.+$)' )
    statName  = re.compile(r'^([^\+]+)')
    statValue = re.compile(r'(\+?\d.+$)')
    position  = re.compile(r'\d番')



    # tsv出力ファイル名
    out_filename = WORKING_DIR.joinpath(f"ocr{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.tsv").as_posix()
    fixed_out_filename = WORKING_DIR.joinpath(f"fixed-ocr{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.tsv").as_posix()
    
    if not pathlib.Path(fixed_out_filename).exists():
        with open(fixed_out_filename, mode='x') as fp:
            fp.write("")
            fp.close()
    



    #! ループ開始
    #!for n, coords_position in enumerate(coords_positions): 本番はこっち
    for n, coords_position in coords_positions: #+ テスト用
        time_start_position = time.time()
        
        # レコード用の配列を用意し、現在の装着箇所を格納する。
        framebase = []
        #framebase.append(n + 1)
        
        logmessage = [
            [
                clr.RED + f'Position {n + 1}' + clr.END,
                'scan start'
            ]
        ]
        pag.click(coords_position)
        
        #! セットループ開始
        for j, coords_setname in enumerate(coords_setnames):
            time_start_set = time.time()
            
            #現在のセット名をレコードに格納する
            #framebase.append(setnames[j])
            
            pag.click(coords_set); time.sleep(2.0)
            pag.click(coords_setname); time.sleep(2.0)
            
            #後で使うセット内の画像を取得する
            with tempfile.NamedTemporaryFile(dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix='.png' ,delete=False ) as set_origin:
                img_set_origin = sc.grab(mode='color',filepath=set_origin.name)
            
            #プラスの位置を取得
            coords_plus = GetCoordinatesMulti(template.plus['template'], threshold=0.85, check=False)
            
            #- 過検出された座標を一つにまとめる。
            coords_plus_rebuilding = []
            for item in zip(*coords_plus[::-1]):
                coords_plus_rebuilding.append( [
                    item[0], item[1] ] )
                
            #- 検出された量が０の時は重複排除の関数に送らない(エラー対応ができてない)
            if len(coords_plus_rebuilding) != 0:
                coords_plus_reduce_overdetected = GetUniqueCoordinates(rootArray=coords_plus_rebuilding, templateImagePath=template.plus['template'], permissiveRate=50 )
            else:
                time_end_set = time.time()
                logmessage = [
                    [
                        "[",
                        clr.GREEN + f'Set {setnames[j]}' + clr.END,
                        "]",
                        'pass reduce over-detected coordinates. Because no scan items.',
                        clr.MAGENTA + 'time:' + clr.END,
                        f'{time_end_set - time_start_set}'
                    ]
                ]
                print(pd.DataFrame(logmessage).to_string(index=False, header=False))
                continue
                
            #! 検出された座標の色を取得して、レアリティを判別する。(データ取得ループ開始)
            #for coord in (coords_plus_reduce_overdetected):#! 本番はreversedなし
            for coord in reversed(coords_plus_reduce_overdetected):
                try:
                    AbilityValues = []
                except:
                    AbilityValues = []
                framebase = []
                framebase.append(n + 1) # 装着箇所
                framebase.append(setnames[j]) #セット名
                
                rarerity = GetRarerity(targetCoords=coord, templatePath=template.plus['template'], originPath=set_origin.name)

                # レアリティを格納する。
                try:
                    framebase.append(rarerity)
                except:
                    framebase.append('unknown')
                    print( log_pandas(title='Rarerity unknown', titlecolor=clr.DARKRED) )

                #- プラスの座標をクリックする
                pag.click(x=coord[0], y=coord[1]); time.sleep(0.5)
                #- サマリの画像を取得する。
                #* 画面全体を取得して、サマリの領域だけ切り取る。
                #* 切り取った画像はtmpfileで名前を付けて保存。
                def ConcurrentTaskCaptureAndBeforeSubstitute():
                    with tempfile.NamedTemporaryFile( dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix='tmporigin.png' ) as tmp_origin_file:
                        tmp_origin = sc.grab(mode='color', filepath=tmp_origin_file.name)
                        tmp_origin = Image.open(tmp_origin_file.name)
                        
                        
                        #サマリウィンドウをテンポラリファイルとして保存
                        with tempfile.NamedTemporaryFile( dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix='_summary.png', delete=False ) as tmp_summary:
                            tmp_origin.crop(summrary_window_crop_area).save(tmp_summary.name)
                            
                            #?test = cv2.imread(tmp_summary.name)
                            #?cv2.imshow('',test)
                            #?cv2.waitKey(0)
                            #?cv2.destroyAllWindows()
                    
                    
                    AbilityValues = ocr_remake.main( [tmp_summary.name] )
                    #print('after ocr_remake.main():', AbilityValues)
                    
                    #データベースを意識して不足しているオプションを補う。(表も見やすくする。)
                    #AbilityValuesの[0]が数値(re.compile(r'[0-9]')の時配列に格納する。
                    #配列に格納されている値のMaxと4を比較して足りない分を足していく。(型を間違わないように)

                    AbilityValues_Rebuilded = RebuildDictionary.relation(AbilityValues[-1])
                    
                    print(clr.BLUE,AbilityValues[-1],clr.END)
                    
                    while max( [ int(i[0]) for i in AbilityValues_Rebuilded if re.search(r'[0-9]', i[0]) ] ) < 4:
                        AbilityValues_Rebuilded.append([
                            str( 1 + max( 
                                            [ int(i[0]) for i in AbilityValues_Rebuilded if re.search(r'[0-9]', i[0]) ] 
                                        )
                            ),
                            None,
                            None
                        ])
                    
                    print(clr.RED,AbilityValues_Rebuilded,clr.END)
                    
                    #AbilityValues_Rebuilded_Str = str(RebuildDictionary.relation(AbilityValues[-1]))
                    #AbilityValues_Rebuilded_Str = str(RebuildDictionary.relation(AbilityValues_Rebuilded))
                    #print(AbilityValues_Rebuilded_Str, type(AbilityValues_Rebuilded_Str))
                    
                    def rexcheck(string):
                        string = OCR_rs_regex.Substitute_crit_d(string)
                        string = OCR_rs_regex.Substitute_others(string)
                        string = OCR_rs_regex.Substitute_att_def(string)
                        return string

                    SubstitutedLine = rexcheck(str(AbilityValues_Rebuilded))
                    #tmplist = AbilityValues_Rebuilded_Str.replace("'",'"')
                    #tmplist = list(AbilityValues_Rebuilded_Str)
                    #tmplist.insert(0,"'")
                    #tmplist.insert(-1,"'")
                    #print(json.loads(tmplist))
                    #print(json.loads("".join(tmplist)))
                    with open(fixed_out_filename, mode='a') as fp:
                        fp.write(SubstitutedLine)
                    #print(ast.literal_eval(AbilityValues_Rebuilded_Str), type(ast.literal_eval(AbilityValues_Rebuilded_Str)))
                    
                    framebase.append(SubstitutedLine)
                    #framebase.append(AbilityValues_Rebuilded_Str)
                    
                    recordresult = []
                    recordresult.append(framebase)
                    
                    df_record = pd.DataFrame(recordresult)
                    print( df_record.to_string(index=False, header=False) )            
                    
                    df_record.to_csv(out_filename, mode='a', header=False, sep="\t")
                
                ConcurrentTaskCaptureAndBeforeSubstitute()
                
                #with ThreadPoolExecutor(max_workers=1000) as executor:
                #    executor.submit(ConcurrentTaskCaptureAndBeforeSubstitute)
                
                
                #+  レコードをマスタテーブルへ追加
                mastertable.append(framebase)
                #df = pd.DataFrame(mastertable)
                #print( df.to_string(index=False, header=False) )
                #! サブオプションのループ(終了) ##########################################################################################
                
            #! 【end】検出された座標の色を取得して、レアリティを判別する。(データ取得ループ)
            
            #一時ファイル群を削除
            #pathlib.Path(tmp_sub.name).unlink(missing_ok=True)#scaned = cv2.imread(tmpf.name)
            #pathlib.Path(tmpf.name).unlink(missing_ok=True)
            #pathlib.Path(tmp_summary.name).unlink(missing_ok=True)
            pathlib.Path(set_origin.name).unlink(missing_ok=True)
            
            #- 結果の印字
            df = pd.DataFrame(mastertable)
            print( df.to_string(index=False, header=False) )
            #print(retval_mainoption)
            
            #+ CSVファイルに追記
            #df.to_csv(out_filename, mode='a', header=False, sep="\t")
            #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            time_end_set = time.time()
            
            logmessage = [
                [
                    "[",
                    clr.GREEN + f'Set {setnames[j]}' + clr.END,
                    "]",
                    'scan end',
                    clr.MAGENTA + 'time:' + clr.END,
                    f'{time_end_set - time_start_set}'
                ]
            ]
            print(pd.DataFrame(logmessage).to_string(index=False, header=False))
            
        #! 【end】セットループ終了
        time_end_position = time.time()
        
        logmessage = [
            [   
                "[",
                clr.RED + f'Position {n + 1}' + clr.END,
                "]",
                'scan end',
                clr.MAGENTA + 'time:' + clr.END,
                f'{time_end_position - time_start_position}'
            ]
        ]
        print(pd.DataFrame(logmessage).to_string(index=False, header=False))
        n += 1

pathlib.Path(out_filename).unlink(missing_ok=True)


