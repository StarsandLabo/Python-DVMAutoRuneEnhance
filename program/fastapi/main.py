import pathlib, sys
from subprocess import call
from enum import Enum
import re, datetime, pprint, os
import tempfile
from tkinter.filedialog import askopenfile
from unittest import result

PROJECT_DIR = pathlib.Path('/home/starsand/DVM-AutoRuneEnhance/')
sys.path.append(PROJECT_DIR.as_posix())
sys.path.append(PROJECT_DIR.joinpath('tools').as_posix())
sys.path.append(PROJECT_DIR.joinpath('lib', 'python3.10', 'site-packages').as_posix())
sys.path.append(PROJECT_DIR.joinpath('program').as_posix())

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

# 実行世代間利用
PROCESS_GENERATION_FILE_DIR  = PROJECT_DIR.joinpath('Generation')
PROCESS_GENERATION_FILE_NAME = 'GenerationFile'

GENYMOTION_FHD_DPI640_RUNESUMMARY_WIDTH = 839 # 639 でコメントなしになる。
GENYMOTION_FHD_DPI640_RUNESUMMARY_HEIGHT = 652

JSON_SAVE_DIR  = PROJECT_DIR.joinpath('program','fastapi')
JSON_FILE_NAME = 'results.json'
JSON_FILE_PATH = JSON_SAVE_DIR.joinpath(JSON_FILE_NAME)

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from tools.clickcondition import ClickCondition as clcd
import pyautogui as pag
import cv2
from PIL import Image
from tools.ScreenCapture_pillow import ScreenCapture
import tools.line_submit_tools as linetools
from tools.TerminalColors import TerminalColors as tc
import json

lnToken = linetools.getToken() # Line Notify 用のトークン取得
fg = tc.fg #フォアグラウンド 色つけ用
bg = tc.bg #バックグラウンド 色つけ用

class PathName_Methods(str, Enum):
    unlock = 'unlock'
    lock   = 'lock'
    invert = 'invert'

app = FastAPI()

results = []
#jsonファイルが無い時は作成する。
def CheckJSON():
    if not JSON_FILE_PATH.exists():
        with open(JSON_FILE_PATH.as_posix(), 'x') as fp:
            fp.write("")
            fp.close()

CheckJSON()

def EquipPositionClickFromImage(number, confidence=0.9):
    print(f'[ {sys._getframe().f_code.co_name} ] Start {datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")}')
    
    print(PROJECT_DIR.joinpath(clcd.Position(number=number, confidence=0.95)['template']).as_posix())
    
    pag.click(
        pag.locateCenterOnScreen(
            PROJECT_DIR.joinpath(
                clcd.Position(
                    number=number,
                    confidence=confidence,
                )['template']
            ).as_posix(),confidence=0.9
        )
    )
    
    print(f'[ {sys._getframe().f_code.co_name} ] Click End ( {pag.position()} ) {datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")}')

def LockMarkOperation(mode, filepath):
    # キー名は、その状態にしたい内容を示す。（unlock ならロックを解除したい）
    templates = {
        'unlock'  : 'locked_big.png',
        'lock': 'nolock_big.png'
    }
    print(f'[ {sys._getframe().f_code.co_name} ] Mode {mode} {datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")}')
    template_lockpath = TEMPLATE_IMG_DIR.joinpath('runelist', templates[mode]).as_posix()
    
    #テンプレートマッチングで現在の状態を確認する。
    sc = ScreenCapture()
    with tempfile.NamedTemporaryFile(dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix='.png', delete=False) as tmpf:
        sc.grab(mode='color', filepath=tmpf.name)
        
        origin   = cv2.imread(tmpf.name)
        template = cv2.imread(filepath)
        
        #- テンプレートマッチングと、類似率の取得
        matchResult = cv2.minMaxLoc( cv2.matchTemplate(origin, template, cv2.TM_CCOEFF_NORMED) )
        print(f'[ {sys._getframe().f_code.co_name} ] Template Matching Result: ', matchResult)
    
    # 類似率は0.98以上なら鍵マークをクリック、それ以外なら何もしない。
    if matchResult[1] > 0.98:
        pag.click(
            pag.locateCenterOnScreen(template_lockpath)
        )
    else:
        print(f'[ {sys._getframe().f_code.co_name} ] Locking Operation: ', 'False')
        pass
    #return print(f'[ {sys._getframe().f_code.co_name} ] end {datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")}')

@app.get("/{process_gen}/{call_methods}")
async def ReadGen(
    call_methods: PathName_Methods,
    process_gen: int, 
    date: str,
    pos: int,
    x: int,
    y: int,
    ):
    
    global results
    
    # 実行世代をファイルから取得
    with open(PROCESS_GENERATION_FILE_DIR.joinpath(PROCESS_GENERATION_FILE_NAME).as_posix(), 'r') as fp:
        saved_gen = fp.read()
        
    with open('./testlogs.log', 'a') as fp:
        fp.write(", ".join( [call_methods, str(process_gen), date, str(x), str(y)] ) )
    
    if re.fullmatch(r'\d{14}', str(process_gen) ):
        # ProcessGenerationがクエリパラメータと現在保存されている値で一致するか
        if not process_gen == int(saved_gen):
            return { 'time': f'{datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")}', 'received': process_gen, 'message': 'process_gen did not match received query.'}
            
        # globの戻りは1つの値か(時刻を利用しているので基本一つ)
        elif not len( list(RESULT_DIR.glob(f'./*{str(process_gen)}*{date}*')) ) == 1:
            return {
                'time': f'{datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")}',
                'message': 'Found items over quantity limit.'
            }
        
        # 検証がOKだった時、アイテムを格納する。
        
        # 初回resultsが何もない時は、resultsに辞書を追加し、Jsonファイルへ書き込む
        # resultsの配列が1つ以上の時、同じファイル名が含まれているか確認し、含まれていれば何もしない。
            # len(results) == 0:
        try:
            print(results)
        except:
            pass
        
        if results == None or len(results) == 0:
            results = []
            results.append(
                {
                    'Process_gen' : process_gen,
                    'call_method' : call_methods.value,
                    'file' : list(RESULT_DIR.glob(f'./*{str(process_gen)}*{date}*'))[0].as_posix() ,
                    'position' : pos , 
                    'coord_x': x,
                    'coord_y': y
                }
            )
            
            with open(JSON_FILE_PATH.as_posix(), 'w') as jf:
                json.dump(results, jf, indent=4)
                jf.close()
                
        else:
            # バリデーション用に一時的にオブジェクトを作成
            
            CheckJSON()
            
            print(JSON_FILE_PATH.as_posix())
            with open(JSON_FILE_PATH.as_posix(), 'r') as jfp:
                documents = jfp.read()
                
            if list(RESULT_DIR.glob(f'./*{str(process_gen)}*{date}*'))[0].as_posix() in documents:
                pass
            else:
                results.append(
                    {
                        'Process_gen' : process_gen,
                        'call_method' : call_methods.value,
                        'file' : list(RESULT_DIR.glob(f'./*{str(process_gen)}*{date}*'))[0].as_posix() ,
                        'position' : pos , 
                        'coord_x': x,
                        'coord_y': y
                    }
                )
                
                with open(JSON_FILE_PATH.as_posix(), 'w') as jf:
                    json.dump(results, jf, indent=4)
                    jf.close()
            
        """
        try:
            if len(results) > 1:
                duplicate_check = list(RESULT_DIR.glob(f'./*{str(process_gen)}*{date}*'))[0] in results[0].values()
        except:
            duplicate_check = ""
            pass # リストの中に一つもないようであればIndex Errorが出るのでこれはOK
            
        try:
            duplicate_check
        except:
            results.append(
                {
                    'Process_gen' : process_gen,
                    'call_method' : call_methods.value,
                    'file' : list(RESULT_DIR.glob(f'./*{str(process_gen)}*{date}*'))[0].as_posix() ,
                    'position' : pos , 
                    'coord_x': x,
                    'coord_y': y
                }
            )
            
            with open(JSON_FILE_PATH.as_posix(), 'w') as jf:
                json.dump(results, jf, indent=4)
                jf.close() 
            return results
        
        if duplicate_check:
            pass
        else:
            results.append(
                {
                    'Process_gen' : process_gen,
                    'call_method' : call_methods.value,
                    'file' : list(RESULT_DIR.glob(f'./*{str(process_gen)}*{date}*'))[0].as_posix() ,
                    'position' : pos , 
                    'coord_x': x,
                    'coord_y': y
                }
            )
            
            with open(JSON_FILE_PATH.as_posix(), 'w') as jf:
                json.dump(results, jf, indent=4)
                jf.close()
        """
        
        pprint.pprint(results)
        
        return results

@app.get("/exec")
async def LockAccess():
    #global results
    #pprint.pprint(results)
    
    with open(JSON_FILE_PATH.as_posix(), 'r') as jf:
        results = json.load(jf)
        jf.close()
    
    if len(results) == 0:
        return 'target not found.'
    
    for record in results:
        
        with open(PROCESS_GENERATION_FILE_DIR.joinpath(PROCESS_GENERATION_FILE_NAME).as_posix(), 'r') as fp:
            saved_gen = int( fp.read() )
        #+ process_genを確認する。念の為
        if int( record['Process_gen'] ) != saved_gen:
            print(f'[ Process Generation Validation ] False')
            return { 'time': f'{datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")}', 'content': 'Process_gen', 'value': record['Process_gen'], 'message': 'process_gen did not match.'}
        else:
                # 【見送り】オプションを排除する()s #+ 見送り理由は、強化を選択していないこともあるので、終了時点の画面はソのまま維持。
                # バツとじ
                # ソートメニューの［強化］をテンプレートマッチングし、合致率が低い時はソートメニュー［強化］を選択する
                # 降順でない時は降順にする(△の向きが正)
            # 装着箇所をクリックする
            EquipPositionClickFromImage(number=record['position'])
            pag.sleep(0.6)
            
        # 座標をクリック。
            pag.click( x=record['coord_x'], y=record['coord_y'] )
            print(f'[ Fix Coords Click ] {pag.position()} {datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")}')
        # 辞書に入っている画像をテンプレートマッチングして、一致率が高ければTrueで処理継続。
            sc = ScreenCapture()
            with tempfile.NamedTemporaryFile(dir=WORKING_PICTURE_SAVE_DIR.as_posix(), suffix='.png', delete=False) as tmpf:
                sc.grab(mode='color', filepath=tmpf.name)
                
                origin   = cv2.imread(tmpf.name)
                template = cv2.imread(str(record['file']))
                
                #- テンプレートマッチングと、類似率の取得
                matchResult = cv2.minMaxLoc( cv2.matchTemplate(origin, template, cv2.TM_CCOEFF_NORMED) )
                print('[ TemplateMatching Result ]', matchResult)
            
            if matchResult[1] < 0.3: #本番は変更したほうが良いかも0.98とか
                return { 'time': f'{datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")}', 'content': 'Template Matching', 'message': f'Matched Rate Failue {matchResult[1]}'}
            
            # 引数(unlock, lock, invert)に応じてロックマークの操作をする
            LockMarkOperation(record['call_method'], record['file'])
                # サマリエリアのマークを見て、既に希望の状態（unlock だったらロック解除されている）であれば何もしない。
                # invertは問答無用でクリックする。
                # 正確性が不明なので、安定してると言えるまではキャプチャをとって送信。
    print(fg.DARKRED, 'json remove point', fg.END)
    results = None
    with open(JSON_FILE_PATH.as_posix(), 'w') as jf:
        jf.write("")
        jf.close()

@app.get("/clear")
async def ClearArray():
    global results
    results = None
    os.remove( JSON_FILE_PATH.as_posix() ) if os.path.isfile(JSON_FILE_PATH.as_posix() ) is True else None
    return 'clear OK.'

