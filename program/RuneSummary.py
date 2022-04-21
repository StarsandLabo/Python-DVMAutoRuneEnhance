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

#* My tools
from tools import colortheme as clr
from tools import reduce_overdetected as rod
from tools.clickcondition import ClickCondition as clcd
from tools.ScreenCapture_pillow import ScreenCapture
from tools.GetUniqueCoordinates import GetUniqueCoordinates
from tools.RuneSummaryTemplates import Templates
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

def additional_percent_and_plus(value):
    inputvalue = value
    rex = regexes()
    
    if  rex.add_percent.search(value):
                        value = re.sub(rex.add_percent, '%', value)
                        #cp.yellow('point: over add_percent 246', value)
                        print( log_pandas(title='RegexFilter', **{'Input': inputvalue, 'Result': value , 'FilterName': 'add_percent', 'Pattern': str(rex.add_percent)}) )
    if  rex.add_plus.search(value):
                        value = re.sub(rex.add_plus, r'+\1', value)
                        #cp.yellow('point: over add_plus 246', value)
                        print( log_pandas(title='RegexFilter', **{'Input': inputvalue, 'Result': value , 'FilterName': 'add_plus', 'Pattern': str(rex.add_plus)}) )

    return value

def abilitynameCheck(abilityName):
    inputvalue = abilityName
    rex = regexes()
    
    if  rex.attack.search(abilityName):
                                abilityName = re.sub(rex.attack,'攻撃力', abilityName)
                                print( log_pandas(title='RegexFilter', **{'Input': inputvalue, 'Result': abilityName, 'FilterName': 'attack','Pattern': str(rex.attack)}) )
    elif rex.defence.search(abilityName):
                                abilityName = re.sub(rex.defence,'防御力', abilityName)
                                print( log_pandas(title='RegexFilter', **{'Input': inputvalue, 'Result': abilityName, 'FilterName': 'defence','Pattern': str(rex.defence)}) )
    elif rex.speed.search(abilityName):
                                abilityName = re.sub(rex.speed,'攻撃速度', abilityName)
                                print( log_pandas(title='RegexFilter', **{'Input': inputvalue, 'Result': abilityName, 'FilterName': 'speed','Pattern': str(rex.speed)}) )
    elif rex.crit_d.search(abilityName):
                                abilityName = re.sub(rex.crit_d,'クリティカルダメージ', abilityName)
                                print( log_pandas(title='RegexFilter', **{'Input': inputvalue, 'Result': abilityName, 'FilterName': 'crit_d','Pattern': str(rex.crit_d)}) )
    else:
        pass
    return abilityName

def valuechecks(value):
    #
    inputvalue = value
    regex = regexes()
    #
    testmode = False
    cp = colorPrints()
    
    cp.red(sys._getframe().f_code.co_name + ": ", 'start') if testmode == True else None
    if regex.no_plus.search(value):
        value = re.sub(regex.no_plus, r'+\2', value)
        #cp.yellow('point: over no_plus', value)
        print( log_pandas(title='RegexFilter', **{'Input': inputvalue, 'Result': value , 'FilterName': 'no_plus', 'Pattern': str(regex.no_plus)}) )
        
        #
        input(value) if testmode == True else None
        
        if regex.no_plus_mainonly.search(value):
            value = re.sub(regex.no_plus_mainonly, r'\1', value)
            #cp.yellow('point: over no_plus_mainonly', value)
            print( log_pandas(title='RegexFilter', **{'Input': inputvalue, 'Result': value , 'FilterName': 'no_plus_mainonly', 'Pattern': str(regex.no_plus_mainonly)}) )
            
            input(value) if testmode == True else None
    #* 上記+がない時の処理が済みの前提
    elif regex.no_plus_mainonly.search(value):
                        value = re.sub(regex.no_plus_mainonly, r'\1', value)
                        #cp.yellow('point: over no_plus_mainonly ', value)
                        print( log_pandas(title='RegexFilter', **{'Input': inputvalue, 'Result': value , 'FilterName': 'no_plus_mainonly', 'Pattern': str(regex.no_plus_mainonly)}) )
                        input(value) if testmode == True else None
    #- 特定の9%6で終わる値はそれを%に置換する   
    elif regex.nine_percent_six.search(value):
                        value = re.sub(regex.nine_percent_six, r'%', value)
                        #cp.yellow('point: over 9%6 ', value)
                        print( log_pandas(title='RegexFilter', **{'Input': inputvalue, 'Result': value , 'FilterName': 'nine_percent_six', 'Pattern': str(regex.nine_percent_six)}) )
                        input(value) if testmode == True else None
    #- 特定の109で終わる値はそれを10%に置換する   
    elif regex.one_zero_nine.search(value):
                        value = re.sub(regex.one_zero_nine, r'10', value)
                        #cp.yellow('point: over 109 ', value)
                        print( log_pandas(title='RegexFilter', **{'Input': inputvalue, 'Result': value , 'FilterName': 'one_zero_nine', 'Pattern': str(regex.one_zero_nine)}) )
                        input(value) if testmode == True else None
    #- +1の直後が1意外で4桁(存在し得ない数値)
    elif regex.digit_four_noexists.search(value):
                        value = re.sub(regex.digit_four_noexists, r'\1\2', value)
                        #cp.yellow('point: over digit_4_nx ', value)
                        print( log_pandas(title='RegexFilter', **{'Input': inputvalue, 'Result': value , 'FilterName': 'digit_four_noexists', 'Pattern': str(regex.digit_four_noexists)}) )
                        input(value) if testmode == True else None
    #- +1の直後が1で4桁(存在し得る数値)。の時は末尾2桁を消す。
    elif regex.digit_four_percent.search(value):
                        value = re.sub(regex.digit_four_percent, r'\1\2', value)
                        #cp.yellow('point: over digit_4_p ', value)
                        print( log_pandas(title='RegexFilter', **{'Input': inputvalue, 'Result': value , 'FilterName': 'digit_four_percent', 'Pattern': str(regex.digit_four_percent)}) )
                        input(value) if testmode == True else None
    #- +1の直後が1以外で3桁(存在し得ない数値)。の時は末尾2桁を消す。
    elif regex.digit_three_noexists.search(value):
                        value = re.sub(regex.digit_three_noexists, r'\1\2', value)
                        #cp.yellow('point: over digit_3_nx ', value)
                        print( log_pandas(title='RegexFilter', **{'Input': inputvalue, 'Result': value , 'FilterName': 'digit_three_noexists', 'Pattern': str(regex.digit_three_noexists)}) )
                        input(value) if testmode == True else None
    #- +1の直後が1で3桁だが、後ろ２文字が96のときは%に変換する。
    elif regex.digit_three_percent_96.search(value):
                        value = re.sub(regex.digit_three_percent_96, r'1%', value)
                        #cp.yellow('point: over digit_3_p_96', value)
                        print( log_pandas(title='RegexFilter', **{'Input': inputvalue, 'Result': value , 'FilterName': 'digit_three_percent_96', 'Pattern': str(regex.digit_three_percent_96)}) )
                        input(value) if testmode == True else None
    #- +1の直後が1で3桁+%(存在し得る数値)
    elif regex.digit_three_percent.search(value):
                        value = re.sub(regex.digit_three_percent, r'\1\2', value)
                        #cp.yellow('point: over digit_3_p ', value)
                        print( log_pandas(title='RegexFilter', **{'Input': inputvalue, 'Result': value , 'FilterName': 'digit_three_percent', 'Pattern': str(regex.digit_three_percent)}) )
                        input(value) if testmode == True else None
    #- 2桁だが、存在しない数。
    elif regex.digit_two_noexists.search(value):
                        value = re.sub(regex.digit_two_noexists, r'\1\2\4', value)
                        #cp.yellow('point: over digit_2_nx ', value)
                        print( log_pandas(title='RegexFilter', **{'Input': inputvalue, 'Result': value , 'FilterName': 'digit_two_noexists', 'Pattern': str(regex.digit_two_noexists)}) )

    #- %%
    elif regex.double_percent.search(value):
                        value = re.sub(regex.double_percent, r'', value)
                        #cp.yellow('point: over double_percent ', value)
                        print( log_pandas(title='RegexFilter', **{'Input': inputvalue, 'Result': value , 'FilterName': 'over_double_percent', 'Pattern': str(regex.double_percent)}) )
                        input(value) if testmode == True else None
    return value

def Detect_hp_attack_defence(abilityName, value):
    inputvalue = value
    #* HPか攻撃力か防御区緑化を見極める
    rex = regexes()
    if  re.search(r'HP',abilityName) or \
        rex.attack.search(abilityName)   or \
        rex.defence.search(abilityName):
        
        #* 攻撃か防御だったら正規表現のフィルタを通す
        if rex.attack.search(abilityName) or rex.defence.search(abilityName):
            #print('attack/defence to valuechecks')
            value = valuechecks(value)
            print( log_pandas(title='RegexFilter', **{'Input': inputvalue, 'Result': value , 'FilterName': 'no_plus_mainonly', 'Pattern': str(rex.attack), 'Pattern': str(rex.defence)}) )
        
        #* 以降はHPの処理。
        else:
            #* valueの数値が2桁でかつ181以上だったらpass
            try:
                int( re.search(r'\d{2,}', value).group() ) > 181
            except AttributeError:
                pass
            else:
                if int( re.search(r'\d{2,}', value).group() ) > 181:
                    pass
                else:
                    #* 残りはHPかつ181未満となり、出現する数値はパーセントのものとして考える。
                    value = valuechecks(value)
                    #input(f'line 517: {value}')
                    
                    #- HPのみ特別に対応する。+7xのような2桁かつ3~%になるような値は存在し得ない。
                    if rex.hp_digit_2_noexists.search(value):
                                    value = re.sub(rex.hp_digit_2_noexists, r'\1', value)
                                    print( log_pandas(title='RegexFilter', **{'Input': inputvalue, 'Result': value , 'FilterName': 'hp_digit_2_noexists', 'Pattern': str(rex.hp_digit_2_noexists)}) )
                    #print(value)
                    #
                    if rex.hp_digit_2_exists.search(value):
                                    value = re.sub(rex.hp_digit_2_exists, r'\1', value)
                                    print( log_pandas(title='RegexFilter', **{'Input': inputvalue, 'Result': value , 'FilterName': 'hp_digit_2_exists', 'Pattern': str(rex.hp_digit_2_exists)}) )
                    
                    #input(f'line 511: {value}')
                    pass
    else:
        # クリティカル率などの、数値が％しか無いものは正規表現フィルタを通す。
        if rex.percent_only.search(tmp_abilityName):
            #cp.yellow('point: over percentOnly 246', tmp_abilityName)
            value = valuechecks(value)
            #log_pandas(title='RegexFilter', **{'Input': inputvalue, 'Result': value , 'FilterName': 'hp_digit_2_noexists', 'Pattern': str(rex.hp_digit_2_noexists)})

    return value

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
summrary_window_crop_area = (
    tmpvar[0],
    tmpvar[1] - 95, #取得位置を誤っていたので補正
    tmpvar[0] + get_template_size.size[0],
    tmpvar[1] + get_template_size.size[1]
)
#? testcodes
#? with tempfile.NamedTemporaryFile(dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix='_croparea.png' ,delete=False ) as test_croparea:
#?    sc.grab(mode='color', filepath=test_croparea.name)
#?    testcropimg = Image.open(test_croparea.name)
#?    
#?    with tempfile.NamedTemporaryFile(dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix='_croppedarea.png' ,delete=False ) as test_croppedarea:
#?        testcropimg.crop(summrary_window_crop_area).save(test_croppedarea.name)
#?        print()

get_template_size.close()

#- 装着箇所
coords_positions = []
tmpvar = pag.locateCenterOnScreen(template.pos1s['template'], grayscale=False, confidence=0.95)
coords_positions.append(tmpvar)
print(log_pandas('locateCenterOnScreen', **{'Result': tmpvar, 'Template': template.pos1s['template']}) )
tmpvar = pag.locateCenterOnScreen(template.pos2s['template'], grayscale=False, confidence=0.95)
coords_positions.append(tmpvar)
print(log_pandas('locateCenterOnScreen', **{'Result': tmpvar, 'Template': template.pos2s['template']}) )
tmpvar = pag.locateCenterOnScreen(template.pos3s['template'], grayscale=False, confidence=0.95)
coords_positions.append(tmpvar)
print(log_pandas('locateCenterOnScreen', **{'Result': tmpvar, 'Template': template.pos3s['template']}) )
tmpvar = pag.locateCenterOnScreen(template.pos4s['template'], grayscale=False, confidence=0.95)
coords_positions.append(tmpvar)
print(log_pandas('locateCenterOnScreen', **{'Result': tmpvar, 'Template': template.pos4s['template']}) )
tmpvar = pag.locateCenterOnScreen(template.pos5s['template'], grayscale=False, confidence=0.95)
coords_positions.append(tmpvar)
print(log_pandas('locateCenterOnScreen', **{'Result': tmpvar, 'Template': template.pos5s['template']}) )
tmpvar = pag.locateCenterOnScreen(template.pos6s['template'], grayscale=False, confidence=0.95)
coords_positions.append(tmpvar)
print(log_pandas('locateCenterOnScreen', **{'Result': tmpvar, 'Template': template.pos6s['template']}) )

def keep3():
    coords_positions = [
        pag.locateCenterOnScreen(template.pos1s['template'], grayscale=False, confidence=0.95),         # 1ポジ目。こんな感じのをforで回す。conficenceを高めに指定しないと取れないかも
        pag.locateCenterOnScreen(template.pos2s['template'], grayscale=False, confidence=0.95),
        pag.locateCenterOnScreen(template.pos3s['template'], grayscale=False, confidence=0.95),
        pag.locateCenterOnScreen(template.pos4s['template'], grayscale=False, confidence=0.95),
        pag.locateCenterOnScreen(template.pos5s['template'], grayscale=False, confidence=0.95),
        pag.locateCenterOnScreen(template.pos6s['template'], grayscale=False, confidence=0.95)
    ]
    print(pd.DataFrame(coords_positions).to_string())

#+ セットをクリックする
pag.click(coords_set); time.sleep(1.5)
#print(pd.DataFrame([ ["LocateCenterOnScreen", coords_set] ]).to_string(index=False, header=False)); 

print(log_pandas('locateCenterOnScreen', **{'Status': 'Getting coordinates(initialize)'}) )
#- 座標を取得する
coords_setnames = [
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
]

setnames = [
    '体力',
    '機会',
    '効果命中',
    '堅固',
    '効果抵抗',
    '強烈',
    'ダメージ',
    '快速',
    '吸血',
    '瞑想',
    '反撃',
    '生存',
    '決意',
    '執念',
]

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

#! ループ開始
for n, coords_position in enumerate(coords_positions):
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
        for coord in coords_plus_reduce_overdetected:
            framebase = []
            framebase.append(n + 1) # 装着箇所
            framebase.append(setnames[j]) #セット名
            
            rarerity = GetRarerity(targetCoords=coord, templatePath=template.plus['template'], originPath=set_origin.name)

            # レアリティを格納する。
            try:
                framebase.append(rarerity)
            except:
                framebase.append('unknown')

            #- プラスの座標をクリックする
            pag.click(x=coord[0], y=coord[1]); time.sleep(2.5)
            
            #- サマリの画像を取得する。
            #* 画面全体を取得して、サマリの領域だけ切り取る。
            #* 切り取った画像はtmpfileで名前を付けて保存。
            with tempfile.NamedTemporaryFile( dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix='tmporigin.png' ) as tmp_origin_file:
                tmp_origin = sc.grab(mode='color', filepath=tmp_origin_file.name)
                tmp_origin = Image.open(tmp_origin_file.name)
                
                #サマリウィンドウをテンポラリファイルとして保存
                with tempfile.NamedTemporaryFile( dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix='_summary.png', delete=False ) as tmp_summary:
                    tmp_origin.crop(summrary_window_crop_area).save(tmp_summary.name)
            
            #一時オリジンを削除する
            pathlib.Path(tmp_origin_file.name).unlink(missing_ok=True)
            #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            # 画像を読み込みリサイズする。
            img = Image.open(tmp_summary.name)
            
            if False == True:
                with tempfile.NamedTemporaryFile(dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix='.png' ) as big:
                    img = img.resize( (img.width * 2 , img.height * 2 ), resample=Image.LANCZOS ).save(big.name)
                    cv2.imshow(template.summary_space['template'], cv2.imread(big.name))
                    cv2.waitKey(0)
                    cv2.destroyAllWindows()
        
            img = img.resize( (img.width * 2 , img.height * 2 ), resample=Image.LANCZOS )#.save(big.name)
            
            #+ メインオプションのみ取得する。###############################################################################
            with tempfile.NamedTemporaryFile(dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix='.png' ) as tmpf:
    
                #- 対象画像メインオプションだけ異なるフィルタリングをする（フォントの太さがあまりにも違うため、同じフィルタで適用しないほうが良いと判断)
                img_optimized_mainoption = optimize(img, border=200) # for jpg
                img_optimized_mainoption.save(tmpf.name)
                
                #? cv2.imshow(tmpf.name, cv2.imread(tmpf.name))
                #? cv2.waitKey(0)
                #? cv2.destroyAllWindows()
                
                #- 画像から文字を取得する
                retval_mainoption = tool.image_to_string( Image.open(tmpf.name), lang='jpn', builder=pyocr.builders.TextBuilder(tesseract_layout=6) ).split("\n")
                
                #? print(retval_mainoption, type(retval_mainoption))
                
                #- メインオプションは1行目に来るので、メインオプションだけ取得する
                for i, p in enumerate(retval_mainoption):
                    if p is not None:
                        r_main = rex.mainoption_tmpseparate.search(p)
                        
                        if r_main is not None:
                            #print(r_main, type(r_main))
                            break
                        
                #- メインオプションが正しく取得されていれば以降の処理で修正する。######################################################################
                try:
                    r_main.group()
                except AttributeError:
                    print( log_pandas(title='AttributeError', titlecolor=clr.DARKRED, **{'Type': 'Main', 'message': 'option not found'}) )
                    pass
                else:
                    #- まず何番ルーンか取得する。
                    for item in retval_mainoption:
                        if rex.position.search(item) is not None:
                            equipPosition = int( position.search(item).group()[0] )

                    #- key, value の取得
                    try:
                        tmp_abilityName = rex.abilities_only.search( r_main.group() ).group()
                    except:
                        print( log_pandas(title='NameError', titlecolor=clr.DARKRED, **{'Type': 'Main', 'message': 'abilityname not detected'}) )
                        tmp_abilityName = 'unknown'
                    
                    try:
                        tmp_value       = rex.operatorAndValue.search( r_main.group() ).group()
                    except:
                        print( log_pandas(title='NameError', titlecolor=clr.DARKRED, **{'Type': 'Main', 'message': 'abilityValue not detected'}) )
                        tmp_value       = 'unknown'
                    
                    
                    print( log_pandas(title='Scaned Key Value', titlecolor=clr.GREEN , **{'AbilityName': tmp_abilityName, 'AbilityValue': tmp_value}) )
                    
                    #? print(
                    #?    tmp_abilityName,
                    #?    type(tmp_abilityName),
                    #?    type(rex.abilities_only.search( r_main.group() ).group() )
                    #?    )
                    
                    #* 【共通処理】【key】防御力、攻撃力、攻撃速度、クリティカルダメージという名称ゆらぎを修正。
                    #* 強制的に上書きしてもよいが、例外的なパターンを見てみたい。
                    tmp_abilityname = abilitynameCheck(tmp_abilityName)
                    
                    #cp.yellow('point: over_abilityName', tmp_abilityName)
                    
                    #+ Key, valueの修正。1,3,5盤ルーンの時 ###########################################################################
                    if equipPosition % 2 == 1:
                        
                        #* 【value】,がない時。カンマに修正する。
                        if rex.no_comma.search(tmp_value):
                                    inputvalue = tmp_value
                                    tmp_value = re.sub(rex.no_comma, r'\1,\2', tmp_value)
                                    print( log_pandas(title='RegexFilter', **{'Input': inputvalue, 'Result': tmp_value, 'FilterName': 'no_comma', 'Pattern': str(rex.no_comma)}) )
                        
                        #cp.yellow('point: over no_comma 135', tmp_value)
                        
                        #* 【value】+が無い時。例外出てきそうだけど、とりあえず現状確認できてるのと類似しそうなパターンのみで
                        if rex.no_plus.search(tmp_value):
                                    inputvalue = tmp_value
                                    tmp_value = re.sub(rex.no_plus, r'+\2', tmp_value)
                                    print( log_pandas(title='RegexFilter', **{'Input': inputvalue, 'Result': tmp_value, 'FilterName': 'no_plus', 'Pattern': str(rex.no_plus)}) )
                                    
                        #cp.yellow('point: over no_plus 135', tmp_value)
                        
                    #+ 2,4,6番ルーンの時 ##################################################################################################
                    elif equipPosition % 2 == 0:
                        
                        # アビリティ名が攻撃、防御、HPに該当する時の処理
                        if  re.search(r'HP',tmp_abilityName) or \
                            rex.attack.search(tmp_abilityName)   or \
                            rex.defence.search(tmp_abilityName):
                                
                            # アビリティの数値は3桁かどうか確認。
                            try:
                                # アビリティの値が181よりも小さい時はContinue / ?なぜ
                                if int( re.search(r'\d{3,}', tmp_value).group() ) < 181:
                                    continue
                            except AttributeError:
                                print( log_pandas(title='AttributeError (main option)', titlecolor=clr.DARKRED, **{'message': 'ability value error'}) )
                                pass
                            
                            # 攻撃が防御に該当した時の処理(正規表現群フィルタを通す)
                            if rex.attack.search(tmp_abilityName) or rex.defence.search(tmp_abilityName):
                                #print('attack/defence to valuechecks')
                                tmp_value = valuechecks(tmp_value)
                            else:
                                # HPの時は特定の％に該当した時置換する(後ろの文字などを削除したい)
                                if rex.no_plus_mainonly.search(tmp_value):
                                    inputvalue = tmp_value
                                    #cp.yellow('point: over hp > 181', tmp_value)
                                    tmp_value = re.sub(rex.no_plus_mainonly, r'\1', tmp_value)
                                    print( log_pandas(title='RegexFilter', **{'Input': inputvalue, 'Result': tmp_value, 'FilterName': 'no_plus_mainonly', 'Pattern': str(rex.no_plus_mainonly)}) )
                                    #cp.yellow('point: HP over no_plus_mainonly 246', tmp_value)
                                    
                        # アビリティ名が％でしか出現しないものは正規表現フィルタ群を通す
                        else:
                            if rex.percent_only.search(tmp_abilityName):
                                #cp.yellow('point: over percentOnly 246', tmp_abilityName)
                                tmp_value = valuechecks(tmp_value)                        
                                
                        #- 末尾に％や＋がない時はつける
                        if  rex.add_percent.search(tmp_value):
                                            inputvalue = tmp_value
                                            tmp_value = re.sub(rex.add_percent, '%', tmp_value)
                                            #cp.yellow('point: over add_percent 246', tmp_value)
                                            print( log_pandas(title='RegexFilter', **{'Input': inputvalue, 'Result': tmp_value, 'FilterName': 'add_perccent', 'Pattern': str(rex.add_percent)}) )
                        if  rex.add_plus.search(tmp_value):
                                            inputvalue = tmp_value
                                            tmp_value = re.sub(rex.add_plus, r'+\1', tmp_value)
                                            #cp.yellow('point: over add_plus 246', tmp_value)
                                            print( log_pandas(title='RegexFilter', **{'Input': inputvalue, 'Result': tmp_value, 'FilterName': 'add_plus', 'Pattern': str(rex.add_plus)}) )
                                            
                #+ データフレームへの格納処理   ##########################################################################
                    #- メインオプションがいずれにも該当しない時(マッチしたが、規定のパターンに該当しなかった時、番号を取得できなかったなど)そのまま値を格納する。
                    else:
                        framebase.append( rex.checkIncludePuls.findall( r_main.group() )[0] )
                        framebase.append( rex.checkIncludePuls.findall( r_main.group() )[1] )
                        print( log_pandas(title='No match regex(main option)', titlecolor=clr.DARKRED, **{'Value': rex.checkIncludePuls.findall( r_main.group() )[0], 'Value': rex.checkIncludePuls.findall( r_main.group() )[1] }) )
                
                #- メインオプションの名前と値がNameError(正規表現にマッチしなかった時)は空白を代入する
                try:
                    tmp_abilityName
                except NameError:
                    print( log_pandas(title='NameError', titlecolor=clr.DARKRED, **{'Type': 'Main', 'Type': 'AbilityName'}) )
                    tmp_abilityName = ""
                
                try:
                    tmp_value
                except NameError:
                    print( log_pandas(title='NameError', titlecolor=clr.DARKRED, **{'Type': 'Main', 'Type': 'AbilityValue'}) )
                    tmp_value = ""

                framebase.append(tmp_abilityName)
                framebase.append(tmp_value)
                
                #* ログ出力
                #?logmessage = [
                #?    [
                #?        "[",
                #?        clr.CYAN + "Append DataFrame" + clr.END,
                #?        "]",
                #?        clr.MAGENTA + "Type:" + clr.END,
                #?        clr.DARKRED + 'Main' + clr.END,
                #?        clr.MAGENTA + "Bonus Name:" + clr.END,
                #?        tmp_abilityName,
                #?       clr.MAGENTA + "Bonus Value:" + clr.END,
                #?        tmp_value,
                #?    ]
                #?]
                
                #? print(pd.DataFrame(logmessage).to_string(index=False, header=False))
                
            #+ サブオプションの取得 ###############################################################################
            with tempfile.NamedTemporaryFile(dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix='.png' ) as tmp_sub:
                
                print( log_pandas(title='Sub option Check', titlecolor=clr.CYAN, **{'message': 'sub option scan start'}) )
                
                #- 画像の二値化(サブオプション用)
                img_optimized_suboption = optimize(img, border=80) # for jpg
                img_optimized_suboption.save(tmp_sub.name)
                
                # 画像から文字を取得する
                retval_suboption = tool.image_to_string( Image.open(tmp_sub.name), lang='jpn', builder=pyocr.builders.TextBuilder(tesseract_layout=6) ).split("\n")
                
                #- メインオプションは飛ばして取得する
                sub_n = 1
                r_sub = []
                for i, p in enumerate(retval_suboption):
                    if p is not None:
                        r_sub_p = rex.abilities.search(p)
                        
                        #print(r_sub)
                        if type(r_sub_p) == re.Match:
                            if sub_n == 1:
                                sub_n += 1
                                pass
                            else:
                                r_sub.append(r_sub_p.group())
                                sub_n += 1
                                
                #+ 正規表現による修正群 ################################################################################33
                #- 存在確認をして以降の処理を行う
                #pprint.pprint(r_sub)
                try:
                    r_sub_p.group()
                except AttributeError:
                    print( log_pandas(title='AttributeError', titlecolor=clr.DARKRED, **{'Type': 'Sub', 'message': 'option not found'}) )
                    pass
                else:
                    
                    #- まず何番ルーンか取得する。
                    for item in retval_suboption:
                        if rex.position.search(item) is not None:
                            equipPosition = int( rex.position.search(item).group()[0] )
                    #
                    #cp.red(f'{tmp_abilityName, tmp_value, equipPosition}')
                    
                    #cp.green(f'{r_sub}, {equipPosition}')
                    
                    #! サブオプションのループ ##########################################################################################
                    for word in r_sub:
                        
                        #- key, value の取得。取得できない時はunknownとする。
                        try:
                            tmp_abilityName = rex.abilities_only.search( word ).group()
                        except:
                            print( log_pandas(title='NameError', titlecolor=clr.DARKRED, **{'Type': 'Sub', 'message': 'abilityname not detected'}) )
                            tmp_abilityName = 'unknown'
                        
                        try:
                            tmp_value       = rex.operatorAndValue.search( word ).group()
                        except:
                            print( log_pandas(title='NameError', titlecolor=clr.DARKRED, **{'Type': 'Sub', 'message': 'abilityvalue not detected'}) )
                            tmp_value       = 'unknown'
                            
                        #- tmp_abilityName が有る時は正規表現フィルタを通す
                        if tmp_abilityName != 'unknown': tmp_abilityName = abilitynameCheck(tmp_abilityName) 

                        #+ 装着箇所が奇数の時 ##########################################################################
                        
                        if equipPosition % 2 == 1:
                            #* 【value】,がない時。コレも矯正せず、例外的なパターンを見てみたい
                            if rex.no_comma.search(tmp_value):
                                        inputvalue = tmp_value
                                        tmp_value = re.sub(rex.no_comma, r'\1,\2', tmp_value)
                                        print( log_pandas(title='RegexFilter', **{'Input': inputvalue, 'Result': tmp_value, 'FilterName': 'no_comma', 'Pattern': str(rex.no_comma)}) )
                            
                            #* 【value】+が無い時。例外出てきそうだけど、とりあえず現状確認できてるのと類似しそうなパターンのみで
                            if rex.no_plus.search(tmp_value):
                                        inputvalue = tmp_value
                                        tmp_value = re.sub(rex.no_plus, r'+\2', tmp_value)
                                        print( log_pandas(title='RegexFilter', **{'Input': inputvalue, 'Result': tmp_value, 'FilterName': 'no_plus', 'Pattern': str(rex.no_plus)}) )
                            
                            #* 全体的なvalueの修正。
                            tmp_value = Detect_hp_attack_defence(tmp_abilityName, tmp_value)
                            
                            #* アビリティ名が％でしか提供されないものであれば数値を確認してプラスやパーセントを付与する。
                            if rex.percent_only.search(tmp_abilityName):
                                # とりあえずアビリティの数値を取得する
                                try:
                                    ability_value = re.search(r'\d+', tmp_value).group()
                                except:
                                    pass
                                else:
                                    if re.search(rex.hp_digit_2_noexists, ability_value):
                                        inputvalue = ability_value
                                        ability_value = re.sub(rex.hp_digit_2_noexists, r'\1', ability_value)
                                        tmp_value = re.sub(r'\d+', ability_value, tmp_value)
                                        print( log_pandas(title='RegexFilter', **{'Input': inputvalue, 'Result': tmp_value , 'FilterName': 'hp_digit_2_noexists', 'Pattern': str(rex.hp_digit_2_noexists)}) )
                                    elif re.search(rex.hp_digit_2_exists, ability_value):
                                        inputvalue = ability_value
                                        ability_value = re.sub(rex.hp_digit_2_exists, r'\1', ability_value)
                                        tmp_value = re.sub(r'\d+', ability_value, tmp_value)
                                        print( log_pandas(title='RegexFilter', **{'Input': inputvalue, 'Result': tmp_value , 'FilterName': 'hp_digit_2_exists', 'Pattern': str(rex.hp_digit_2_exists)}) )
                                tmp_value = additional_percent_and_plus(tmp_value)
                            
                            #* ％以外のものであれば、以下の数値で判断する。
                            #- 攻撃力、防御力...3~25の範囲はグレーゾーンなのでここでは一旦無視する。（あとで再度framebaseの中身を見て判別し直す）
                            #- HP...181以上の数値は固定値
                            elif rex.attack.search(tmp_abilityName) or rex.defence.search(tmp_abilityName):
                                try:
                                    tmp_value_int_part = int(re.search( (r'\d+'),tmp_value).group() )
                                except:
                                    cp.red('error now tmp_value: ', tmp_value)
                                    
                                if tmp_value_int_part < 3 or tmp_value_int_part > 25:
                                    tmp_value = additional_percent_and_plus(tmp_value)
                                else:
                                    pass
                            elif re.search(r'HP', tmp_abilityName):
                                try:
                                    tmp_value_int_part = int(re.search( (r'\d+'),tmp_value).group() )
                                except:
                                    cp.red('error now tmp_value: ', tmp_value)
                                    
                                if tmp_value_int_part < 181:
                                    tmp_value = additional_percent_and_plus(tmp_value)
                                else:
                                    if  rex.add_plus.search(tmp_value):
                                        tmp_value = re.sub(rex.add_plus, r'+\1', tmp_value)
                                        cp.yellow('point: over add_plus', tmp_value)
                            cp.yellow('point: over no_plus 135', tmp_value)
                        
                        #- ルーンの番号が2の倍数
                        elif equipPosition % 2 == 0:
                            
                            tmp_value = Detect_hp_attack_defence(tmp_abilityName,tmp_value)
                            
                            #* プラスや％の付与。
                            #* アビリティ名を見て攻撃力、防御力、HPだったら更に条件判定する。
                            #input(f'{type(tmp_value)}, {tmp_value}, {tmp_abilityName}')
                            #input(f'{tmp_value}, {type(tmp_value)}')
                            #- まずは攻撃、防御力
                            if rex.attack.search(tmp_abilityName) or rex.defence.search(tmp_abilityName):
                                try:
                                    int( re.search(r'\d+',tmp_value).group() )< 3 or int( re.search(r'\d+', tmp_value).group() ) > 25
                                except ValueError:
                                    cp.yellow(f'exception: ValueError statement. tmp_value is ', f'{tmp_value}')
                                    pass
                                else:
                                    # 3~25の範囲外は％とプラスを付与する。
                                    if int( re.search(r'\d+',tmp_value).group() )< 3 or int( re.search(r'\d+', tmp_value).group() ) > 25:
                                        if  rex.add_percent.search(tmp_value):
                                                            tmp_value = re.sub(rex.add_percent, '%', tmp_value)
                                                            cp.yellow('point: over add_percent 246', tmp_value)
                                        if  rex.add_plus.search(tmp_value):
                                                            tmp_value = re.sub(rex.add_plus, r'+\1', tmp_value)
                                                            cp.yellow('point: over add_plus 246', tmp_value)
                                                            
                                    # それ以外の時は暫定的にプラスと判断する。
                                    else:
                                        if  rex.add_plus.search(tmp_value):
                                                            tmp_value = re.sub(rex.add_plus, r'+\1', tmp_value)
                                                            cp.yellow('point: over add_plus 246', tmp_value)
                            #- HPの時の処理。
                            elif re.search(r'HP', tmp_abilityName):
                                    # 181未満は％のものと判断して処理、それ以外はプラスと判断。
                                    if int( re.search(r'\d+',tmp_value).group() ) < 181:
                                        if  rex.add_percent.search(tmp_value):
                                                            tmp_value = re.sub(rex.add_percent, '%', tmp_value)
                                                            cp.yellow('point: over add_percent 246', tmp_value)
                                        if  rex.add_plus.search(tmp_value):
                                                            tmp_value = re.sub(rex.add_plus, r'+\1', tmp_value)
                                                            cp.yellow('point: over add_plus 246', tmp_value)
                                    else:
                                        if  rex.add_plus.search(tmp_value):
                                                            tmp_value = re.sub(rex.add_plus, r'+\1', tmp_value)
                                                            cp.yellow('point: over add_plus 246', tmp_value)
                            else:
                                tmp_value = additional_percent_and_plus(tmp_value)
                        #- いずれのフィルタにもかからなかったものはunknownとする。（ファイル名から画像は追えるので情報は付加しない）
                                
                        else:
                            try:
                                tmp_abilityName = rex.abilities_only.search( word ).group()
                            except NameError:
                                tmp_abilityName = ""

                            try:
                                tmp_value = rex.statValue.search( word ).group()
                            except NameError:
                                tmp_value = ""
                                
                            framebase.append(
                                [ tmp_abilityName, tmp_value ]
                            )
                        
                        #+ レコードに追加する。######################################
                        framebase.append(tmp_abilityName)
                        framebase.append(tmp_value)
            
            #+ 【end】サブオプションの取得 ###############################################################################
            
            #- 見た目を揃えたい。オプションの数は一定ではないので、一定の数に到達していない時は空白を追加する。
            while len(framebase) < 15:
                framebase.append("")
            #- 取得時刻を追記
            framebase.append( datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S') )
            #- 画像ファイルのパスを追記
            framebase.append( tmp_summary.name )
            # framebase.append(imagePath) # 過去ファイル名を記載していた時のもの]
            
            recordresult = []
            recordresult.append(framebase)
            
            df_record = pd.DataFrame(recordresult)
            print( df_record.to_string(index=False, header=False) )            
            
            df_record.to_csv(out_filename, mode='a', header=False, sep="\t")
            
            #+  レコードをマスタテーブルへ追加
            mastertable.append(framebase)
            #df = pd.DataFrame(mastertable)
            #print( df.to_string(index=False, header=False) )
            #! サブオプションのループ(終了) ##########################################################################################
            
        #! 【end】検出された座標の色を取得して、レアリティを判別する。(データ取得ループ)
        
        #一時ファイル群を削除
        pathlib.Path(tmp_sub.name).unlink(missing_ok=True)#scaned = cv2.imread(tmpf.name)
        pathlib.Path(tmpf.name).unlink(missing_ok=True)
        pathlib.Path(tmp_summary.name).unlink(missing_ok=True)
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

def keep ():
    for imagePath in targetImagePaths:

        img = Image.open(tmp_summary.name)
        if False == True:
            with tempfile.NamedTemporaryFile(dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix='.png' ) as big:
                img = img.resize( (img.width * 2 , img.height * 2 ), resample=Image.LANCZOS ).save(big.name)
                cv2.imshow(template.summary_space['template'], cv2.imread(big.name))
                cv2.waitKey(0)
                cv2.destroyAllWindows()

        img = img.resize( (img.width * 2 , img.height * 2 ), resample=Image.LANCZOS )#.save(big.name)    
        #framebase = [] #- for Pandas data frame.
        
        #"""mainoptions
        with tempfile.NamedTemporaryFile(dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix='.jpg' ) as tmpf:
            
            #- 対象画像メインオプションだけ異なるフィルタリングをする（フォントの太さがあまりにも違うため、同じフィルタで適用しないほうが良いと判断)
            img_optimized_mainoption = optimize(img, border=200) # for jpg
            #img_optimized = optimize(img, border=82) # for jpg
            img_optimized_mainoption.save(tmpf.name)
            
            
            #cv2.imshow(tmpf.name, cv2.imread(tmpf.name))
            #cv2.waitKey(0)
            #cv2.destroyAllWindows()
            
            
            # 画像から文字を取得する
            retval_mainoption = tool.image_to_string( Image.open(tmpf.name), lang='jpn', builder=pyocr.builders.TextBuilder(tesseract_layout=6) ).split("\n")
            
            print(retval_mainoption, type(retval_mainoption))
            
            # メインオプションは1行目に来るので、メインオプションだけ取得する
            for i, p in enumerate(retval_mainoption):
                if p is not None:
                    r_main = mainoption_tmpseparate.search(p)
                    
                    if r_main is not None:
                        #print(r_main, type(r_main))
                        break
            
            # メインオプションがある程度正しい形で取得できているか判別し、修正できるパターンであれば修正する。(+を付けたいが、必ずしも+で良いか不明のため。)
            try:
                r_main.group()
            except AttributeError:
                pass
            else:
                #+ 正規表現による修正群
                #- まず何番ルーンか取得する。
                for item in retval_mainoption:
                    if position.search(item) is not None:
                        equipPosition = int( position.search(item).group()[0] )

                #- key, value の取得
                tmp_abilityName = abilities_only.search( r_main.group() ).group()
                tmp_value       = operatorAndValue.search( r_main.group() ).group()
                
                cp.red(f'{tmp_abilityName, tmp_value}')
                
                print(
                    tmp_abilityName,
                    type(tmp_abilityName),
                    type(abilities_only.search( r_main.group() ).group() )
                    )
                
                #* 【共通処理】【key】防御力、攻撃力、攻撃速度、クリティカルダメージの修正。強制的に上書きしてもよいが、例外的なパターンを見てみたい。
                abilitynameCheck(tmp_abilityName)
                
                cp.yellow('point: over_abilityName', tmp_abilityName)
                
                #+ Key, valueの修正。1,3,5盤ルーンの時
                if equipPosition % 2 == 1:
                    #* 【value】,がない時。コレも矯正せず、例外的なパターンを見てみたい
                    no_comma = re.compile(r'(\d+)[^\d](\d+)')
                    if no_comma.search(tmp_value):
                                tmp_value = re.sub(no_comma, r'\1,\2', tmp_value)
                    
                    cp.yellow('point: over no_comma 135', tmp_value)
                    
                    #* 【value】+が無い時。例外出てきそうだけど、とりあえず現状確認できてるのと類似しそうなパターンのみで
                    no_plus = re.compile(r'(?<!\+)([1|t|l])([^\.,]+)')
                    if no_plus.search(tmp_value):
                                tmp_value = re.sub(no_plus, r'+\2', tmp_value)
                                
                    cp.yellow('point: over no_plus 135', tmp_value)
                #+ 2,4,6盤ルーンの時
                elif equipPosition % 2 == 0:
                    no_plus                 = re.compile(r'(?<!\+)([1|t|l])([^\.,]+)')
                    no_plus_mainonly        = re.compile(r'( (14)|(22)|(28)|(34)|(46)|(55) )(.+)')
                    digit_three_noexists    = re.compile(r'([^\d])([2-9])(\d){2}')
                    digit_four_noexists     = re.compile(r'([^\d])(1\d)(\d){2}')
                    digit_three_percent     = re.compile(r'([^\d])([1\d])(\d.)')
                    digit_four_percent      = re.compile(r'([^\d])([2-9])(.+)')
                    double_percent          = re.compile(r'(%%)')
                    add_percent             = re.compile(r'(?<!%)$')
                    add_plus                = re.compile(r'^([^\+])')

                    # HPは別途対応
                    attack  = re.compile(r'攻.力')
                    defence = re.compile(r'防..?')

                    if  re.search(r'HP',tmp_abilityName) or \
                        attack.search(tmp_abilityName)   or \
                        defence.search(tmp_abilityName):
                        try:
                            if int( re.search(r'\d{3,}', tmp_value).group() ) < 181:
                                continue
                        except AttributeError:
                            pass
                        
                        if attack.search(tmp_abilityName) or defence.search(tmp_abilityName):
                            print('attack/defence to valuechecks')
                            tmp_value = valuechecks(tmp_value)
                        else:
                            if no_plus_mainonly.search(tmp_value):
                                cp.yellow('point: over hp > 181', tmp_value)
                                tmp_value = re.sub(no_plus_mainonly, r'\1', tmp_value)
                                cp.yellow('point: HP over no_plus_mainonly 246', tmp_value)
                    else:
                        if percent_only.search(tmp_abilityName):
                            cp.yellow('point: over percentOnly 246', tmp_abilityName)
                            tmp_value = valuechecks(tmp_value)                        
                            
                            #+ ％オンリーのオプションでない時は無視する。（HP意外はメインとサブ両方見ないと区別がつかない事が有る)
                            
                            #- 上記の場合、+220となるが、このまま以下のルールに当てはめるとおかしいことになる。
                            #- 22や46といった固定の数値は除外する必要が有るかも（r'(\+|t|l)(22|34|46)') のようなのはありかも。機数はない
                            #? ----多すぎて、とりあえず％付けない形で消すだけ消して、最後に％まとめてつける-------
                            #- +1の直後が1以外で3桁(存在し得ない数値)。の時は末尾2桁を消す。
                            #* クリティカル率           +206
                            #* クリティカル率           +696
                            #? ----------------------------------
                            #- +1の直後が1で4桁(存在し得る数値)。の時は末尾2桁を消す。
                            #* クリティカルダメージ     +1096
                            #? ----------------------------------
                            #- +1の直後が1以外で4桁(存在し得ない数値)。の時は末尾3桁を消す。
                            #* クリティカルダメージ     +4096
                            #? ----------------------------------
                            #- +1の直後が1で2桁以上+%(存在し得る数値)
                            #* クリティカル率           +109%
                            #? ----------------------------------
                            #- +1の直後が1意外で2桁以上+%(存在し得ない数値)
                            #* 効果抵抗                 +59%6
                            #* クリティカル率           +39%
                            #? ----------------------------------
                            #* 効果命中                 +3%%
                            #* HP                       +229    ※2,4,6版のメインオプションはHPで固定の＋の値は無い。この場合9が％になってる。
                            #? -----------------------------------------------------------------------------------
                            #* 防御力   +22 # 末尾に％がない時は付与する。数値意外の時はその文字を変更する。(コレ一番最後に処理しないとダメ)
                            

                    #* +の値がない時。#* 攻撃力                   1220
                            
                    #+ 末尾に％がない時はつける
                    if  add_percent.search(tmp_value):
                                        tmp_value = re.sub(add_percent, '%', tmp_value)
                                        cp.yellow('point: over add_percent 246', tmp_value)
                    if  add_plus.search(tmp_value):
                                        tmp_value = re.sub(add_plus, r'+\1', tmp_value)
                                        cp.yellow('point: over add_plus 246', tmp_value)
                            
                else:
                    framebase.append(
                        [
                            rex.checkIncludePuls.findall( r_main.group() )[0],
                            "+" + rex.checkIncludePuls.findall( r_main.group() )[1]
                        ]
                    )
            try:
                tmp_abilityName
            except NameError:
                tmp_abilityName = ""
            
            try:
                tmp_value
            except NameError:
                tmp_value = ""

            framebase.append(tmp_abilityName)
            framebase.append(tmp_value)
            #"""
        with tempfile.NamedTemporaryFile(dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix='.jpg' ) as tmp_sub:
            
            #- 対象画像メインオプションだけ異なるフィルタリングをする（フォントの太さがあまりにも違うため、同じフィルタで適用しないほうが良いと判断)
            img_optimized_suboption = optimize(img, border=80) # for jpg
            #img_optimized = optimize(img, border=82) # for jpg
            img_optimized_suboption.save(tmp_sub.name)
            
            # 画像から文字を取得する
            retval_suboption = tool.image_to_string( Image.open(tmp_sub.name), lang='jpn', builder=pyocr.builders.TextBuilder(tesseract_layout=6) ).split("\n")
            
            #- メインオプションは飛ばして取得する
            n = 1
            r_sub = []
            for i, p in enumerate(retval_suboption):
                if p is not None:
                    r_sub_p = abilities.search(p)
                    
                    #print(r_sub)
                    if type(r_sub_p) == re.Match:
                        if n == 1:
                            n += 1
                            pass
                        else:
                            r_sub.append(r_sub_p.group())
                            n += 1
            
            #pprint.pprint(r_sub)
            try:
                r_sub_p.group()
            except AttributeError:
                pass
            else:
                #+ 正規表現による修正群
                #- まず何番ルーンか取得する。
                for item in retval_suboption:
                    if position.search(item) is not None:
                        equipPosition = int( position.search(item).group()[0] )
                #
                #cp.red(f'{tmp_abilityName, tmp_value, equipPosition}')
                
                cp.green(f'{r_sub}, {equipPosition}')
            for word in r_sub:
                #- key, value の取得
                try:
                    tmp_abilityName = abilities_only.search( word ).group()
                except:
                    tmp_abilityName = 'unknown'
                
                try:
                    tmp_value       = operatorAndValue.search( word ).group()
                except:
                    tmp_value       = 'unknown'
                    
                #- tmp_abilityName が有る時は正規表現フィルタを通す
                if tmp_abilityName != 'unknown': tmp_abilityName = abilitynameCheck(tmp_abilityName) 

                if equipPosition % 2 == 1:
                    #* 【value】,がない時。コレも矯正せず、例外的なパターンを見てみたい
                    no_comma = re.compile(r'(\d+)[^\d%](\d+)')
                    if no_comma.search(tmp_value):
                                tmp_value = re.sub(no_comma, r'\1,\2', tmp_value)
                    
                    cp.yellow('point: over no_comma 135', tmp_value)
                    
                    #* 【value】+が無い時。例外出てきそうだけど、とりあえず現状確認できてるのと類似しそうなパターンのみで
                    no_plus = re.compile(r'(?<!\+)([1|t|l])([^\.,]+)')
                    if no_plus.search(tmp_value):
                                tmp_value = re.sub(no_plus, r'+\2', tmp_value)
                    
                    #* 全体的なvalueの修正。
                    tmp_value = Detect_hp_attack_defence(tmp_abilityName, tmp_value)
                    
                    #ステータスが％のものは、％がついていない時付与する。
                    #* アビリティ名が％でしか提供されないものであれば数値を確認してプラスやパーセントを付与する。
                    if rex.percent_only.search(tmp_abilityName):
                        # とりあえずアビリティの数値を取得する
                        try:
                            ability_value = re.search(r'\d+', tmp_value).group()
                        except:
                            pass
                        else:
                            if re.search(rex.hp_digit_2_noexists, ability_value):
                                ability_value = re.sub(rex.hp_digit_2_noexists, r'\1', ability_value)
                                tmp_value = re.sub(r'\d+', ability_value, tmp_value)
                            elif re.search(rex.hp_digit_2_exists, ability_value):
                                ability_value = re.sub(rex.hp_digit_2_exists, r'\1', ability_value)
                                tmp_value = re.sub(r'\d+', ability_value, tmp_value)
                        tmp_value = additional_percent_and_plus(tmp_value)
                    
                    #* ％以外のものであれば、以下の数値で判断する。
                    #- 攻撃力、防御力...3~25の範囲はグレーゾーンなのでここでは一旦無視する。（あとで再度framebaseの中身を見て判別し直す）
                    #- HP...181以上の数値は固定値
                    elif rex.attack.search(tmp_abilityName) or rex.defence.search(tmp_abilityName):
                        try:
                            tmp_value_int_part = int(re.search( (r'\d+'),tmp_value).group() )
                        except:
                            cp.red('error now tmp_value: ', tmp_value)
                            
                        if tmp_value_int_part < 3 or tmp_value_int_part > 25:
                            tmp_value = additional_percent_and_plus(tmp_value)
                        else:
                            pass
                    elif re.search(r'HP', tmp_abilityName):
                        try:
                            tmp_value_int_part = int(re.search( (r'\d+'),tmp_value).group() )
                        except:
                            cp.red('error now tmp_value: ', tmp_value)
                            
                        if tmp_value_int_part < 181:
                            tmp_value = additional_percent_and_plus(tmp_value)
                        else:
                            if  rex.add_plus.search(tmp_value):
                                tmp_value = re.sub(rex.add_plus, r'+\1', tmp_value)
                                cp.yellow('point: over add_plus', tmp_value)
                    cp.yellow('point: over no_plus 135', tmp_value)
                
                #- ルーンの番号が2の倍数
                elif equipPosition % 2 == 0:
                    attack  = re.compile(r'攻.力')
                    defence = re.compile(r'防..?')
                    
                    tmp_value = Detect_hp_attack_defence(tmp_abilityName,tmp_value)
                    
                    #* プラスや％の付与。
                    #* アビリティ名を見て攻撃力、防御力、HPだったら更に条件判定する。
                    #input(f'{type(tmp_value)}, {tmp_value}, {tmp_abilityName}')
                    #input(f'{tmp_value}, {type(tmp_value)}')
                    if rex.attack.search(tmp_abilityName) or rex.defence.search(tmp_abilityName):
                        # Value Errorはすでに正規の形 +1% などのためパスで良い
                        try:
                            int( re.search(r'\d+',tmp_value).group() )< 3 or int( re.search(r'\d+', tmp_value).group() ) > 25
                        except ValueError:
                            cp.yellow(f'exception: ValueError statement. tmp_value is ', f'{tmp_value}')
                            pass
                        else:
                            if int( re.search(r'\d+',tmp_value).group() )< 3 or int( re.search(r'\d+', tmp_value).group() ) > 25:
                                if  rex.add_percent.search(tmp_value):
                                                    tmp_value = re.sub(rex.add_percent, '%', tmp_value)
                                                    cp.yellow('point: over add_percent 246', tmp_value)
                                if  rex.add_plus.search(tmp_value):
                                                    tmp_value = re.sub(rex.add_plus, r'+\1', tmp_value)
                                                    cp.yellow('point: over add_plus 246', tmp_value)
                            else:
                                if  rex.add_plus.search(tmp_value):
                                                    tmp_value = re.sub(rex.add_plus, r'+\1', tmp_value)
                                                    cp.yellow('point: over add_plus 246', tmp_value)
                    elif re.search(r'HP', tmp_abilityName):
                            if int( re.search(r'\d+',tmp_value).group() ) < 181:
                                if  rex.add_percent.search(tmp_value):
                                                    tmp_value = re.sub(rex.add_percent, '%', tmp_value)
                                                    cp.yellow('point: over add_percent 246', tmp_value)
                                if  rex.add_plus.search(tmp_value):
                                                    tmp_value = re.sub(rex.add_plus, r'+\1', tmp_value)
                                                    cp.yellow('point: over add_plus 246', tmp_value)
                            else:
                                if  rex.add_plus.search(tmp_value):
                                                    tmp_value = re.sub(rex.add_plus, r'+\1', tmp_value)
                                                    cp.yellow('point: over add_plus 246', tmp_value)
                    else:
                        tmp_value = additional_percent_and_plus(tmp_value)
                #- いずれのフィルタにもかからなかったものはunknownとする。（ファイル名から画像は追えるので情報は付加しない）
                        
                else:
                    try:
                        tmp_abilityName = rex.abilities_only.search( word ).group()
                    except NameError:
                        tmp_abilityName = ""

                    try:
                        tmp_value = rex.statValue.search( word ).group()
                    except NameError:
                        tmp_value = ""
                        
                    framebase.append(
                        [ tmp_abilityName, tmp_value ]
                    )
                    
                framebase.append(tmp_abilityName)
                framebase.append(tmp_value)
                
            while len(framebase) < 12:
                framebase.append("")
            framebase.append(imagePath)
        mastertable.append(framebase)
                #cv2.imshow(tmp_sub.name, cv2.imread(tmp_sub.name))
                #cv2.waitKey(0)
                #cv2.destroyAllWindows()
                
                # メインオプションがある程度正しい形で取得できているか判別し、修正できるパターンであれば修正する。(+を付けたいが、必ずしも+で良いか不明のため。)
                
                #? testcodes for Suboption
                #cv2.imshow(imagePath, cv2.imread(tmpf.name))
                #cv2.waitKey(0)
                #cv2.destroyAllWindows()
            
            # 文字列を取得するが、正規表現とマッチした時は加工する。
            

        #一時ファイル群を削除
        pathlib.Path(tmp_sub.name).unlink(missing_ok=True)#scaned = cv2.imread(tmpf.name)
        pathlib.Path(tmpf.name).unlink(missing_ok=True)
        pathlib.Path(tmp_summary.name).unlink(missing_ok=True)
        
        clr.cprint(imagePath,clr.DARKYELLOW)
        columns = ['Main','value_Main','1st','value_1st','2nd','value_2nd','3rd','value_3rd','4th','value_4th','5th','value_5th','Path']
        df = pd.DataFrame(mastertable,columns=columns)
        print( df )
        #print(retval_mainoption)
        
    df.to_csv(out_filename, mode='a', header=False, sep="\t")

def keep2():
    pass
    #pprint.pprint(retval_suboption)
    #cv2.imshow(tmpf.name, cv2.imread(tmpf.name))
    #cv2.imshow(tmp_sub.name, cv2.imread(tmp_sub.name))
    #cv2.waitKey(0)
    #cv2.destroyAllWindows()

    #+ ％オンリーのオプションでない時は無視する。（HP意外はメインとサブ両方見ないと区別がつかない事が有る)
    
    #- 上記の場合、+220となるが、このまま以下のルールに当てはめるとおかしいことになる。
    #- 22や46といった固定の数値は除外する必要が有るかも（r'(\+|t|l)(22|34|46)') のようなのはありかも。機数はない
    #? ----多すぎて、とりあえず％付けない形で消すだけ消して、最後に％まとめてつける-------
    #- +1の直後が1以外で3桁(存在し得ない数値)。の時は末尾2桁を消す。
    #* クリティカル率           +206
    #* クリティカル率           +696
    #? ----------------------------------
    #- +1の直後が1で4桁(存在し得る数値)。の時は末尾2桁を消す。
    #* クリティカルダメージ     +1096
    #? ----------------------------------
    #- +1の直後が1以外で4桁(存在し得ない数値)。の時は末尾3桁を消す。
    #* クリティカルダメージ     +4096
    #? ----------------------------------
    #- +1の直後が1で2桁以上+%(存在し得る数値)
    #* クリティカル率           +109%
    #? ----------------------------------
    #- +1の直後が1意外で2桁以上+%(存在し得ない数値)
    #* 効果抵抗                 +59%6
    #* クリティカル率           +39%
    #? ----------------------------------
    #* 効果命中                 +3%%
    #* HP                       +229    ※2,4,6版のメインオプションはHPで固定の＋の値は無い。この場合9が％になってる。
    #? -----------------------------------------------------------------------------------
    #* 防御力   +22 # 末尾に％がない時は付与する。数値意外の時はその文字を変更する。(コレ一番最後に処理しないとダメ)