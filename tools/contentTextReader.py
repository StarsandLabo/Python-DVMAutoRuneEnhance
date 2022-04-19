import pathlib, sys

from cv2 import CAP_PROP_APERTURE, SparsePyrLKOpticalFlow_create, add, convertPointsFromHomogeneous, cvtColor, reduce
from pkg_resources import resource_exists
import pyperclip
PROJECT_DIR = pathlib.Path('/home/starsand/DVM-AutoRuneEnhance/')
sys.path.append(PROJECT_DIR.as_posix())
sys.path.append(PROJECT_DIR.joinpath('tools').as_posix())
sys.path.append(PROJECT_DIR.joinpath('lib', 'python3.10', 'site-packages').as_posix())

WORKING_DIR = PROJECT_DIR.joinpath('work')       
WORKING_PICTURE_SAVE_DIR = WORKING_DIR.joinpath('img')

RESOURCE_DIR = PROJECT_DIR.joinpath('resources')
TEMPLATE_IMG_DIR = RESOURCE_DIR.joinpath('img', 'template')

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
from tqdm import tqdm
import pandas as pd
import pprint

#* My tools
from tools import colortheme as clr
from tools import reduce_overdetected as rod
from tools.clickcondition import ClickCondition as clcd
from tools.ScreenCapture_pillow import ScreenCapture
from tools.GetUniqueCoordinates import GetUniqueCoordinates
clr.colorTheme()   # initialize

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

def additional_percent_and_plus(value):
    rex = regexes()
    
    if  rex.add_percent.search(value):
                        value = re.sub(rex.add_percent, '%', value)
                        cp.yellow('point: over add_percent 246', value)
    if  rex.add_plus.search(value):
                        value = re.sub(rex.add_plus, r'+\1', value)
                        cp.yellow('point: over add_plus 246', value)
    return value


def abilitynameCheck(abilityName):
    attack  = re.compile(r'攻.(力)')
    defence = re.compile(r'防.(力)?')
    speed   = re.compile(r'攻..度')
    crit_d  = re.compile(r'クリティカル.メー.')
    if  attack.search(abilityName):
                                abilityName = re.sub(attack,'攻撃力', abilityName)
    elif defence.search(abilityName):
                                abilityName = re.sub(defence,'防御力', abilityName)
    elif speed.search(abilityName):
                                abilityName = re.sub(speed,'攻撃速度', abilityName)
    elif crit_d.search(abilityName):
                                abilityName = re.sub(crit_d,'クリティカルダメージ', abilityName)
    else:
        pass
    return abilityName

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
    abilities_only          = re.compile( r'((HP)|(攻.力)|(防.力)|(攻.速度)|(効果..)|(効果命中)|(クリティカル率)|(命中)|(回.)|(クリティカル.メー.))' )
    operatorAndValue        = re.compile( r'(\+|\d)(\d.*$)' )
    percent_only            = re.compile( r'(攻.速度)|(効果..)|(効果命中)|(クリティカル率)|(命中)|(回.)|(クリティカル.メー.)')
    abilities               = re.compile( r'((HP)|(攻.力)|(防.力)|(攻.速度)|(効果..)|(効果命中)|(クリティカル率)|(命中)|(回.)|(クリティカル.メー.)).+(%|\d)' )
    mainoption_tmpseparate  = re.compile( r'((HP)|(攻.力)|(防.力)|(攻.速度)|(効果..)|(効果命中)|(クリティカル率)|(命中)|(回.)|(クリティカル.メー.))(.+$)' )
    statName                = re.compile(r'^([^\+]+)')
    statValue               = re.compile(r'(\+?\d.+$)')
    position                = re.compile(r'\d番')
    attack                  = re.compile(r'攻.力')
    defence                 = re.compile(r'防..?')
    plus_and_percent        = re.compile(r'(HP)|(攻.力)|(防.力)')
    hp_digit_2_noexists     = re.compile(r'[^\d]?([2-9]).*')
    hp_digit_2_exists       = re.compile(r'[^\d](1\d).*')


def valuechecks(value):
    #
    regex = regexes()
    #
    testmode = False
    cp = colorPrints()
    
    cp.red(sys._getframe().f_code.co_name + ": ", 'start') if testmode == True else None
    if regex.no_plus.search(value):
        value = re.sub(regex.no_plus, r'+\2', value)
        cp.yellow('point: over no_plus', value)
        #
        input(value) if testmode == True else None
        if regex.no_plus_mainonly.search(value):
            value = re.sub(regex.no_plus_mainonly, r'\1', value)
            cp.yellow('point: over no_plus_mainonly', value)
            input(value) if testmode == True else None
    #* 上記+がない時の処理が済みの前提
    elif regex.no_plus_mainonly.search(value):
                        value = re.sub(regex.no_plus_mainonly, r'\1', value)
                        cp.yellow('point: over no_plus_mainonly ', value)
                        input(value) if testmode == True else None
    #- 特定の9%6で終わる値はそれを%に置換する   
    elif regex.nine_percent_six.search(value):
                        value = re.sub(regex.nine_percent_six, r'%', value)
                        cp.yellow('point: over 9%6 ', value)
                        input(value) if testmode == True else None
    #- 特定の109で終わる値はそれを10%に置換する   
    elif regex.one_zero_nine.search(value):
                        value = re.sub(regex.one_zero_nine, r'10', value)
                        cp.yellow('point: over 109 ', value)
                        input(value) if testmode == True else None
    #- +1の直後が1意外で4桁(存在し得ない数値)
    elif regex.digit_four_noexists.search(value):
                        value = re.sub(regex.digit_four_noexists, r'\1\2', value)
                        cp.yellow('point: over digit_4_nx ', value)
                        input(value) if testmode == True else None
    #- +1の直後が1で4桁(存在し得る数値)。の時は末尾2桁を消す。
    elif regex.digit_four_percent.search(value):
                        value = re.sub(regex.digit_four_percent, r'\1\2', value)
                        cp.yellow('point: over digit_4_p ', value)
                        input(value) if testmode == True else None
    #- +1の直後が1以外で3桁(存在し得ない数値)。の時は末尾2桁を消す。
    elif regex.digit_three_noexists.search(value):
                        value = re.sub(regex.digit_three_noexists, r'\1\2', value)
                        cp.yellow('point: over digit_3_nx ', value)
                        input(value) if testmode == True else None
    #- +1の直後が1で3桁だが、後ろ２文字が96のときは%に変換する。
    elif regex.digit_three_percent_96.search(value):
                        value = re.sub(regex.digit_three_percent_96, r'1%', value)
                        cp.yellow('point: over digit_3_p_96', value)
                        input(value) if testmode == True else None
    #- +1の直後が1で3桁+%(存在し得る数値)
    elif regex.digit_three_percent.search(value):
                        value = re.sub(regex.digit_three_percent, r'\1\2', value)
                        cp.yellow('point: over digit_3_p ', value)
                        input(value) if testmode == True else None
    #- 2桁だが、存在しない数。
    elif regex.digit_two_noexists.search(value):
                        value = re.sub(regex.digit_two_noexists, r'\1\2\4', value)
                        cp.yellow('point: over digit_2_nx ', value)

    #- %%
    elif regex.double_percent.search(value):
                        value = re.sub(regex.double_percent, r'', value)
                        cp.yellow('point: over double_percent ', value)
                        input(value) if testmode == True else None
    return value

def Detect_hp_attack_defence(abilityName, value):
    #* HPか攻撃力か防御区緑化を見極める
    rex = regexes()
    if  re.search(r'HP',abilityName) or \
        rex.attack.search(abilityName)   or \
        rex.defence.search(abilityName):
        
        #* 攻撃か防御だったら正規表現のフィルタを通す
        if rex.attack.search(abilityName) or rex.defence.search(abilityName):
            print('attack/defence to valuechecks')
            value = valuechecks(value)
        
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
                    print(value)
                    #
                    if rex.hp_digit_2_exists.search(value):
                                    value = re.sub(rex.hp_digit_2_exists, r'\1', value)
                    
                    #input(f'line 511: {value}')
                    pass
    else:
        # クリティカル率などの、数値が％しか無いものは正規表現フィルタを通す。
        if percent_only.search(tmp_abilityName):
            cp.yellow('point: over percentOnly 246', tmp_abilityName)
            value = valuechecks(value)
    return value


#+ ocr の事前準備
tools = pyocr.get_available_tools()
tool  = tools[0]

#? ターゲットの画像を読み込む
targetImagePaths = [ p.as_posix() for p in list(RESULT_DIR.glob("**/*.png")) ]
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

checkIncludePuls = re.compile(r'[^\+]+')

clr.colorTheme()
out_filename = WORKING_DIR.joinpath(f"ocr{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.tsv").as_posix()

mastertable = []

targetImagePaths.reverse()
for imagePath in targetImagePaths:
    img = Image.open(imagePath)
    
    
    
    if False == True:
        with tempfile.NamedTemporaryFile(dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix='.png' ) as big:
            img = img.resize( (img.width * 2 , img.height * 2 ), resample=Image.LANCZOS ).save(big.name)
            cv2.imshow(imagePath, cv2.imread(big.name))
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            
    img = img.resize( (img.width * 2 , img.height * 2 ), resample=Image.LANCZOS )#.save(big.name)
    
    framebase = [] #- for Pandas data frame.
    
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
        
        cp = colorPrints()
        
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
                        checkIncludePuls.findall( r_main.group() )[0],
                        "+" + checkIncludePuls.findall( r_main.group() )[1]
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
    cp = colorPrints()
    rex = regexes()
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
        
        
    pd.set_option('display.unicode.east_asian_width', True)
    print("-------------\n")
    n = 0

    pathlib.Path(tmp_sub.name).unlink(missing_ok=True)#scaned = cv2.imread(tmpf.name)
    pathlib.Path(tmpf.name).unlink(missing_ok=True)
    
    clr.cprint(imagePath,clr.DARKYELLOW)
    columns = ['Main','value_Main','1st','value_1st','2nd','value_2nd','3rd','value_3rd','4th','value_4th','5th','value_5th','Path']
    df = pd.DataFrame(mastertable,columns=columns)
    print( df )
    #print(retval_mainoption)
    
df.to_csv(out_filename, mode='a', header=False, sep="\t")
    
    #pprint.pprint(retval_suboption)
    #cv2.imshow(tmpf.name, cv2.imread(tmpf.name))
    #cv2.imshow(tmp_sub.name, cv2.imread(tmp_sub.name))
    #cv2.waitKey(0)
    #cv2.destroyAllWindows()

