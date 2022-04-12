#+ ######### init params #########
PROJECT_DIR = pathlib.Path('/home/starsand/DVM-AutoRuneEnhance/')
sys.path.append(PROJECT_DIR.joinpath('tools').as_posix())

WORKING_DIR = PROJECT_DIR.joinpath('work')       
WORKING_PICTURE_SAVE_DIR = WORKING_DIR.joinpath('img')

RESOURCE_DIR = PROJECT_DIR.joinpath('resources')
TEMPLATE_IMG_DIR = RESOURCE_DIR.joinpath('img', 'template')

RESULT_DIR = PROJECT_DIR.joinpath('result')

#* basic modules
import os, pathlib, sys, pprint, time, statistics

#* advanced modules
import numpy as np
from matplotlib import pyplot as plt
import cv2

#* My tools
from tools import colortheme as clr
from tools import reduce_overdetected as rod
clr.colorTheme()   # initialize


#+++++++++++ main ++++++++++

# リストメニュを開き、ルーン画面遷移アイコンをクリックする。

sys.exit()


#  オリジナル画像を取得、グレースケール変換
origin  = cv2.imread(ORIGIN_PICTURE_DIR.joinpath('origin_rune_1.png').as_posix())
gray    = cv2.cvtColor(origin, cv2.COLOR_BGR2GRAY)

#  テンプレート画像ををグレースケールで取得。
templatepath = TEMPLATE_PICTURE_DIR.joinpath('template3.png')
template = cv2.imread(templatepath.as_posix(), 0)

print(f'template fullpath: {templatepath.as_posix()}')
print(f'template filename: {templatepath.name}' )
print(f'template parent: {templatepath.parent.as_posix()}' )

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

