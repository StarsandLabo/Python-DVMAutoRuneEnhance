import pathlib, sys
from site import addpackage
from telnetlib import NOP
from tokenize import Name

from cv2 import CAP_PROP_APERTURE, SparsePyrLKOpticalFlow_create, add, convertPointsFromHomogeneous, cvtColor, reduce
from flask import flash
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

#+ ocr の事前準備
tools = pyocr.get_available_tools()
tool  = tools[0]

#? ターゲットの画像を読み込む
targetImagePaths = [ p.as_posix() for p in list(RESULT_DIR.glob("**/*.png")) ]
#pprint.pprint(targetImagePath)

#? target regex
abilities_only = re.compile( r'((HP)|(攻.力)|(防.力)|(攻.速度)|(効果抵抗)|(効果命中)|(クリティカル率)|(命中)|(回避)|(クリティカル.メー.))' )
operatorAndValue = re.compile( r'(\+|\d)(\d.*$)' )
percent_only   = re.compile( r'(攻.速度)|(効果抵抗)|(効果命中)|(クリティカル率)|(命中)|(回避)|(クリティカル.メー.)')

abilities = re.compile( r'((HP)|(攻.力)|(防.力)|(攻.速度)|(効果抵抗)|(効果命中)|(クリティカル率)|(命中)|(回避)|(クリティカル.メー.)).+(%|\d)' )
mainoption_tmpseparate = re.compile( r'((HP)|(攻.力)|(防.力)|(攻.速度)|(効果抵抗)|(効果命中)|(クリティカル率)|(命中)|(回避)|(クリティカル.メー.))(.+$)' )
statName  = re.compile(r'^([^\+]+)')
statValue = re.compile(r'(\+?\d.+$)')
position  = re.compile(r'\d番')

checkIncludePuls = re.compile(r'[^\+]+')

clr.colorTheme()
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
            attack  = re.compile(r'攻.(力)')
            defence = re.compile(r'防.(力)?')
            speed   = re.compile(r'攻..度')
            crit_d  = re.compile(r'クリティカル.メー.')
            if  attack.search(tmp_abilityName):
                                        tmp_abilityName = re.sub(attack,'攻撃力', tmp_abilityName)
            elif defence.search(tmp_abilityName):
                                        tmp_abilityName = re.sub(defence,'防御力', tmp_abilityName)
            elif speed.search(tmp_abilityName):
                                        tmp_abilityName = re.sub(speed,'攻撃速度', tmp_abilityName)
            elif crit_d.search(tmp_abilityName):
                                        tmp_abilityName = re.sub(crit_d,'クリティカルダメージ', tmp_abilityName)
            else:
                pass
            
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
                
                def valuechecks(value):
                    if no_plus.search(value):
                        value = re.sub(no_plus, r'+\2', value)
                        cp.yellow('point: over no_plus 246', value)
                        #
                        if no_plus_mainonly.search(value):
                            value = re.sub(no_plus_mainonly, r'\1', value)
                            cp.yellow('point: over no_plus_mainonly 246', value)
                                        
                    #* 上記+がない時の処理が済みの前提
                    elif no_plus_mainonly.search(value):
                                        value = re.sub(no_plus_mainonly, r'\1', value)
                                        cp.yellow('point: over no_plus_mainonly 246', value)
                                        
                    #- +1の直後が1以外で3桁(存在し得ない数値)。の時は末尾2桁を消す。
                    elif digit_three_noexists.search(value):
                                        value = re.sub(digit_three_noexists, r'\1\2', value)
                                        cp.yellow('point: over digit_3_nx 246', value)
                                        
                    #- +1の直後が1で4桁(存在し得る数値)。の時は末尾2桁を消す。
                    elif digit_four_noexists.search(value):
                                        value = re.sub(digit_four_noexists, r'\1\2', value)
                                        cp.yellow('point: over digit_4_nx 246', value)
                                        
                    #- +1の直後が1で2桁以上+%(存在し得る数値)
                    elif digit_three_percent.search(value):
                                        value = re.sub(digit_three_percent, r'\1\2', value)
                                        cp.yellow('point: over digit_3_p 246', value)
                                        
                    #- +1の直後が1意外で2桁以上+%(存在し得ない数値)
                    elif digit_three_percent.search(value):
                                        value = re.sub(digit_three_percent, r'\1\2', value)
                                        cp.yellow('point: over digit_4_p 246', value)
                    #- %%
                    elif double_percent.search(value):
                                        value = re.sub(double_percent, r'', value)
                                        cp.yellow('point: over double_percent 246', value)
                    return value

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
                        """
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
                        """

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

        framebase.append( [tmp_abilityName, tmp_value] )
        
        with tempfile.NamedTemporaryFile(dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix='.jpg' ) as tmp_sub:
            
            #- 対象画像メインオプションだけ異なるフィルタリングをする（フォントの太さがあまりにも違うため、同じフィルタで適用しないほうが良いと判断)
            img_optimized_mainoption = optimize(img, border=80) # for jpg
            #img_optimized = optimize(img, border=82) # for jpg
            img_optimized_mainoption.save(tmp_sub.name)
            
            # 画像から文字を取得する
            retval_suboption = tool.image_to_string( Image.open(tmp_sub.name), lang='jpn', builder=pyocr.builders.TextBuilder(tesseract_layout=6) ).split("\n")
            
            #- メインオプションは飛ばして取得する
            n = 1
            r_suboptions = []
            for i, p in enumerate(retval_suboption):
                if p is not None:
                    r_sub = abilities.search(p)
                    
                    #print(r_sub)
                    if type(r_sub) == re.Match:
                        if n == 1:
                            n += 1
                            pass
                        else:
                            if r_sub is not None:
                                r_suboptions.append(r_sub.group())
                                n += 1
            #pprint.pprint(r_suboptions)
            
            for word in r_suboptions:
                if len( checkIncludePuls.findall( word ) ) > 1:
                    framebase.append(
                        [
                            checkIncludePuls.findall( word )[0],
                            "+" + checkIncludePuls.findall( word )[1]
                        ]
                    )
                else:
                    framebase.append(
                        [
                            re.search(r'[^0-9,%,+]+', word ).group(),
                            re.search(r'[0-9,%,+]+.+$', word ).group()
                        ]
                    )
            
            
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
            """
                for i, p in enumerate(retval):
                
                r = abilities.search(p)
                
                if r == None:
                    continue
                else:
                    if len( re.findall(r'[^+]+',r.group()) ) == 1:
                        r = re.sub(r'(\d+)',r'+\1', r.group())
                    else:
                        r = str(r.group())

                    if n == 0:
                        r_divert = re.sub(r'(\+[0-9]{,2})%', r'\1%', r)
                        #input(f'{n}, {r_divert}, {r}')
                    else:
                        r_divert = re.sub(r'(\+[2-9])\d%', r'\1%', r)
                        #input(f'{n}, {r_divert}')
                    
                    if n > 1:
                        r_divert = re.sub(r'(\d)9%', r'\1%', r_divert)

                    r_divert = re.sub(r'(\+\d\d?)96$', r'\1%', r_divert)
                    r_group = r_divert
                    try:
                        framebase.append(
                            [
                                statName.search(r_group).group(), statValue.search(r_group).group()
                            ]
                        )
                    except AttributeError:
                        pass
                    #r_out += r_divert + "\n"
                    n += 1
                #r = re.sub('(\+\d\d?)96$','\1\%', r)
            """
        #pathlib.Path(tmp_sub.name).unlink(missing_ok=True)#scaned = cv2.imread(tmpf.name)
    #pathlib.Path(tmpf.name).unlink(missing_ok=True)
            clr.cprint(imagePath,clr.DARKYELLOW)
            print( pd.DataFrame(framebase, columns=['BonusName','Value']) )
            print(retval_mainoption)
            #pprint.pprint(retval_suboption)
            #cv2.imshow(tmpf.name, cv2.imread(tmpf.name))
            #cv2.imshow(tmp_sub.name, cv2.imread(tmp_sub.name))
            cv2.waitKey(0)
            cv2.destroyAllWindows()

