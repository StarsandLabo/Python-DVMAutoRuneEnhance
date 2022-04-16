import numpy as np
from PIL import Image
import cv2
import statistics, pprint
import colortheme

colors = {
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
}

class colorPrints():
    def red(self, coloredtext="",whitetext=""):
        return print(f'\033[38;2;239;41;41m{coloredtext}\033[0m{whitetext}')

    def yellow(self, coloredtext="",whitetext=""):
        return print(f'\033[38;2;237;212;0m{coloredtext}\033[0m{whitetext}')

    def green(self, coloredtext="",whitetext=""):
        return print(f'\033[38;2;138;226;52m{coloredtext}\033[0m{whitetext}')

cp = colorPrints()

def GetUniqueCoordinates(rootArray, templateImagePath, permissiveRate=50):
    
    #+ 準備
    #? インデックス付きrootArrayを作成する  
    #?rootArrayWithIndex = []
    #?for i, item in enumerate(rootArray):
    #?    rootArrayWithIndex.append( {i: item} )
    
    #! 確定した配列を格納する変数。
    FixedCoordinates = []    
    
    #- permissive の値を取得する
    #* テンプレート画像を読み込み、幅と高さを取得する
    Image = cv2.imread(templateImagePath, 0)
    w, h = Image.shape[0:2]
    hPermissive = int(h * (permissiveRate / 100) )
    wPermissive = int(w * (permissiveRate / 100) )
    
    #+ 仮の基準用Y軸を設定する。
    #- 初回は値がないので、RootArrayの一番最初のY軸の値とする。
    tmpYcriterion = None
    if tmpYcriterion is None:
        tmpYcriterion = rootArray[0][1]
    else:
        pass
    
    while True:
        #+ 仮のY軸の値を基準に、RootArrayを走査して仮のY軸のグループを作成する。
        #- tmpYcriterionから見て +- permissive(テンプレート画像の50%の長さ)以内に収まる値を仮のYグループと見立てる。
        tmpYGroup = []
        for coords in rootArray:
            if  coords[1] <= ( tmpYcriterion + hPermissive ) and \
                coords[1] >= ( tmpYcriterion - hPermissive ):
                
                tmpYGroup.append(coords[1])
                #input(f'{tmpYcriterion}, {coords[1]}')
            else:
                pass
        #+ 正式なY軸グループを決める。
        #- 仮Y軸グループ中のmean high(中央値)を正式Y軸グループの基準値とする。
        cp.red('tmpYGroup mean high ',statistics.median_high(tmpYGroup))
        Ycriterion = statistics.median_high(tmpYGroup)
        cp.red()
        
        #- 正式なY軸グループを取得する
        YGroup = []
        YGroupForMedians = []
        for coords in rootArray:
            if  coords[1] <= ( Ycriterion + hPermissive ) and \
                coords[1] >= ( Ycriterion - hPermissive ):
                
                #+ 正式なY軸グループとして追加する
                YGroup.append(coords)
                
                #* 中央値検索用の配列を作成する。
                YGroupForMedians.append(coords[1])
                
                #- 次のグループのために、インデックスもを取得する
                YGroupLastIndex = (rootArray.index(coords))
            else:
                pass
        #* 中央値を取得。正式Y軸グループ中のY軸の値。
        YGroupMedian = statistics.median_high(YGroupForMedians)
        cp.yellow('YGroup Median ',statistics.median_high(YGroupForMedians))
        pprint.pprint(YGroup)
        
        #- 正式なY軸グループの中から中央値を持つ群を抽出する。
        YGroupMedians = [ x for x in YGroup if x[1] == YGroupMedian]
        print(f'YGroupMedians: {YGroupMedians}')
        
        #+ x軸のグループを作る。(y軸のグループの中で)
        #- 仮のx軸基準値を取得する(x軸は複数のグループが想定される)
        
        #* 仮の基準値はYGroupMediansの配列中一番最初の値とする。
        cp.red(f'Minimum x(in YGroupMedians): ', np.sort(YGroupMedians, axis=0)[0][0] )
        tmpXcriterion = int( np.sort(YGroupMedians, axis=0)[0][0] )
        #? print(YGroup[0], tmpXcriterion+wPermissive, tmpXcriterion-wPermissive, len(YGroup))
        
        while True:
            #* (a)仮の基準値 tmpXcriterion から +- wPermissive の値を持つインデックスを取得する。
            #? print( [ i for i, x in enumerate(YGroup) if x[0] < (tmpXcriterion + wPermissive) and x[0] > (tmpXcriterion - wPermissive) ] )
            tmpXGroupIndexes = [ i for i, x in enumerate(YGroupMedians) if x[0] < (tmpXcriterion + wPermissive) and x[0] > (tmpXcriterion - wPermissive) ]
            cp.red('(a)仮の基準値 tmpXcriterion から +- wPermissive の値を持つインデックスを取得する。\n',tmpXGroupIndexes)
            
            #* (b)基準値から外れたインデックスを格納する。
            tmpXGroupIndexesOutofCriterion = [ i for i, x in enumerate(YGroupMedians) if not( x[0] < (tmpXcriterion + wPermissive) and x[0] > (tmpXcriterion - wPermissive) )]
            cp.red('(b)基準値から外れたインデックスを格納する。\n',tmpXGroupIndexesOutofCriterion)
            
            #- 基準値から外れたインデックスの数ループを回す。
            
            #cp.green('Current index: ',f'{tmpXGroupIndexesOutofCriterion[i]} {i} times')
            
            #* (c) (a)で取得したインデックスから、YGroupMediansにあるx軸の実際の値を取得し、その中央値を正式なX軸の基準値(Xcriterion)とする。
            tmparr = []
            for idx in tmpXGroupIndexes:
                tmparr.append(YGroupMedians[idx][0])
            #print(tmparr)
            
            Xcriterion = statistics.median_high(tmparr)
            cp.red(
                '(c) (a)で取得したインデックスから、YGroupMediansにあるx軸の実際の値を取得し、その中央値を正式なX軸の基準値(Xcriterion)とする。\n',
                Xcriterion
            )
            
            #* (d) YGroupMedians の配列から Xcriterion +- wPermissiveの値を持つインデックスを取得する。
            XGroupIndexes = [ i for i, x in enumerate(YGroupMedians) if x[0] < (Xcriterion + wPermissive) and x[0] > (Xcriterion - wPermissive) ]
            cp.yellow('(d) YGroupMedians の配列から Xcriterion +- wPermissiveの値を持つインデックスを取得する。\n', XGroupIndexes)
            
            #* (e) (d)で取得したインデックスから、YGroupMediansにある実際のx軸の値を取得し、その中央値を取得する。
            arr = []
            for idx in XGroupIndexes:
                arr.append(YGroupMedians[idx][0])
            
            XGroupMedian = statistics.median_high(arr)
            cp.yellow('(e) (d)で取得したインデックスから、YGroupMediansにある実際のx軸の値を取得し、その中央値を取得する。\n', XGroupMedian)
            
            #* (f) YGroupMediansの配列から (e)で取得したインデックスの値を持つ配列を取得する。
            XGroupMediansInYMedianGroup = [ v for v in YGroupMedians if v[0] == XGroupMedian ]
            cp.yellow('(f) YGroupMediansの配列から (e)で取得したインデックスの値を持つ配列を取得する。\n', XGroupMediansInYMedianGroup)
            
            #* (g) (f)の配列が複数検出された時(テンプレートを複数回分けて適用した場合は起こりうる。)先頭の配列[0]で確定とする。
            #- すでに同一の値が含まれている場合は無視する(上手なアルゴリズムが思いつかなかった。)
            if XGroupMediansInYMedianGroup[0] in FixedCoordinates:
                continue
            else:
                FixedCoordinates.append(XGroupMediansInYMedianGroup[0])
                
                # (h) YGroupMediansからXGroupIndexes(d)の値を取り除く。
                XGroupIndexes.reverse()
                for idx in XGroupIndexes :
                    YGroupMedians.pop(idx)
                    cp.yellow('(h) YGroupMediansからXGroupIndexes(d)の値を取り除く。\n', f'current idx: {idx}\nremain coords: {YGroupMedians}')
                input(f'current YGroupMedians: {YGroupMedians}')
                
                # (i) 基準値から外れたインデックスで採れる値を、仮のx基準値に代入する
                try:
                    tmpXcriterion = int( np.sort(YGroupMedians, axis=0)[0][0] )
                except IndexError:
                    # IndexErrorは基本的に正常終了
                    break
            #? test codes
            #! y軸グループからx軸のグループを取得するループ。ここまで
            print(YGroupMedians, 'outofcriterion', tmpXGroupIndexesOutofCriterion)
            print('fixedCoordinates',FixedCoordinates)
        
        # 仮のY軸基準値を取得する(ループ用)
        try:
            tmpYcriterion = rootArray[YGroupLastIndex + 1][1]
        except IndexError:
            return FixedCoordinates


RootArray = [[761, 1005], [762, 1005], [760, 1006], [761, 1006], [762, 1006], [763, 1006], [1002, 1006], [760, 1007], [761, 1007], [762, 1007], [763, 1007], [761, 1008], [762, 1008], [1122, 1125], [1242, 1125], [1001, 1126], [1002, 1126], [1003, 1126], [1121, 1126], [1122, 1126], [1123, 1126], [1241, 1126], [1242, 1126], [1243, 1126], [1001, 1127], [1002, 1127], [1003, 1127], [1121, 1127], [1122, 1127], [1123, 1127], [1241, 1127], [1242, 1127], [1243, 1127], [1001, 1128], [1002, 1128], [1121, 1128], [1122, 1128], [1123, 1128], [1241, 1128], [1242, 1128], [1243, 1128]]
templatePath = '/home/starsand/DVM-AutoRuneEnhance/resources/img/template/runelist/frame1.png'

print( GetUniqueCoordinates(rootArray=RootArray, templateImagePath=templatePath, permissiveRate=50) )