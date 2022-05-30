from csv import DictReader
import pathlib, sys
from subprocess import call
from enum import Enum
import re, datetime, pprint, os, shutil
import tempfile
from blinker import receiver_connected




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
RECENT_ENHANCED_LIST_PATH = RESULT_DIR.joinpath('RecentEnhancedList.json').as_posix()

# 実行世代間利用
PROCESS_GENERATION_FILE_DIR  = PROJECT_DIR.joinpath('Generation')
PROCESS_GENERATION_FILE_NAME = 'GenerationFile'

GENYMOTION_FHD_DPI640_RUNESUMMARY_WIDTH = 839 # 639 でコメントなしになる。
GENYMOTION_FHD_DPI640_RUNESUMMARY_HEIGHT = 652

JSON_SAVE_DIR  = PROJECT_DIR.joinpath('program','fastapi','dev')
JSON_FILE_NAME = 'results.json'
JSON_FILE_PATH = JSON_SAVE_DIR.joinpath(JSON_FILE_NAME)

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from fastapi.responses import RedirectResponse
from fastapi.responses import HTMLResponse
from tools.clickcondition import ClickCondition as clcd
import pyautogui as pag
import cv2
from PIL import Image
from tools.ScreenCapture_pillow import ScreenCapture
import tools.line_submit_tools as linetools
from tools.TerminalColors import TerminalColors as tc
import json
import psutil
import queue
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import Form
from typing import Optional
#os.chdir(PROJECT_DIR.joinpath('program', 'fastapi').as_posix())

lnToken = linetools.getToken() # Line Notify 用のトークン取得
fg = tc.fg #フォアグラウンド 色つけ用
bg = tc.bg #バックグラウンド 色つけ用

templates = Jinja2Templates(directory="templates")

class PathName_Methods(str, Enum):
    unlock = 'unlock'
    lock   = 'lock'
    invert = 'invert'

app = FastAPI()
app.mount('/result', StaticFiles(directory="/home/starsand/DVM-AutoRuneEnhance/result"), name='result')
#app.mount('/templates', StaticFiles(directory="templates"), name='static')
app.mount('/static', StaticFiles(directory="templates"), name='static') #! 本番環境はここをよく比べて見直す


results = []
q = queue.Queue()

#jsonファイルが無い時は作成する。
def CheckJSON():
    if not JSON_FILE_PATH.exists():
        with open(JSON_FILE_PATH.as_posix(), 'x') as fp:
            fp.write("")
            fp.close()

CheckJSON()

# 画像退避先の確認と作成。
if not RESULT_DIR.joinpath('AfterLockingOperation', 'divert', 'images', 'dev').exists():
    RESULT_DIR.joinpath('AfterLockingOperation', 'divert', 'images', 'dev').mkdir(exist_ok=False, parents=True)

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
        shutil.move(filepath, RESULT_DIR.joinpath('AfterLockingOperation', 'divert', 'images', 'dev'))
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
            print('try statement', results)
        except:
            pass
        
        print(list(RESULT_DIR.glob(f'./*{str(process_gen)}*{date}*'))[0].as_posix().split(f"{os.sep}")[-1] )
        if results == None or len(results) == 0:
            results = []
            results.append(
                {
                    'Process_gen' : str(process_gen),
                    'call_method' : call_methods.value,
                    'date' : date,
                    'file' : list(RESULT_DIR.glob(f'./*{str(process_gen)}*{date}*'))[0].as_posix().split(f"{os.sep}")[-1] ,
                    'position' : pos , 
                    'coord_x': x,
                    'coord_y': y,
                    'id' : "0"
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
                
            # 既に同じルーンが入っている時は、配列から取り除く。
            if list(RESULT_DIR.glob(f'./*{str(process_gen)}*{date}*'))[0].as_posix().split(f"{os.sep}")[-1] in documents:
                targetFileName = list(RESULT_DIR.glob(f'./*{str(process_gen)}*{date}*'))[0].as_posix().split(f"{os.sep}")[-1]
                index = [ i for i, v in enumerate(results) if v['file'] == targetFileName ]
                results.pop(index[0])
                with open(JSON_FILE_PATH.as_posix(), 'w') as jf:
                    json.dump(results, jf, indent=4)
                    jf.close()
            else:
                results.append(
                    {
                        'Process_gen' : str(process_gen),
                        'call_method' : call_methods.value,
                        'date' : date,
                        'file' : list(RESULT_DIR.glob(f'./*{str(process_gen)}*{date}*'))[0].as_posix().split(f"{os.sep}")[-1] ,
                        'position' : pos , 
                        'coord_x': x,
                        'coord_y': y,
                        'id' : "0"
                    }
                )
                
                with open(JSON_FILE_PATH.as_posix(), 'w') as jf:
                    json.dump(results, jf, indent=4)
                    jf.close()
            
        
        pprint.pprint(results)
        
        return RedirectResponse('http://192.168.11.8:8000/portal')

@app.post("/{process_gen}")
async def ReadPostedItem(params: Optional[str] = Form(None)):
    receivcedParameters = params.split(',')
    
    try:
        master
    except UnboundLocalError:
        master = []

    # indexを2で割った余りが0の時はキー、1の時は値となるリストを作成する。
    # 辞書を2つに分けて、Zipで結合売る。
    keys = []
    values = []
    for i, item in enumerate(receivcedParameters):
        keys.append(item) if i % 2 == 0 else values.append(item)
    zipped = zip(keys, values)
    master.append(dict(zipped))

    #received = json.JSONEncoder.encode(params)
    print(fg.DARKCYAN,'received params', fg.END, "\n", master)
    
    global results
    
    # 実行世代をファイルから取得
    with open(PROCESS_GENERATION_FILE_DIR.joinpath(PROCESS_GENERATION_FILE_NAME).as_posix(), 'r') as fp:
        saved_gen = fp.read()
        
    with open('./testlogs.log', 'a') as fp:
        fp.write(", ".join(
            [
                            master[0]['call_method'],
                            master[0]['Process_gen'],
                            master[0]['date'],
                            master[0]['coord_x'],
                            master[0]['coord_y']
            ]
                        )
                 + "\n"
                )
    
    return master
    
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
            print('try statement', results)
        except:
            pass
        
        print(list(RESULT_DIR.glob(f'./*{str(process_gen)}*{date}*'))[0].as_posix().split(f"{os.sep}")[-1] )
        if results == None or len(results) == 0:
            results = []
            results.append(
                {
                    'Process_gen' : str(process_gen),
                    'call_method' : call_methods.value,
                    'date' : date,
                    'file' : list(RESULT_DIR.glob(f'./*{str(process_gen)}*{date}*'))[0].as_posix().split(f"{os.sep}")[-1] ,
                    'position' : pos , 
                    'coord_x': x,
                    'coord_y': y,
                    'id' : "0"
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
                
            # 既に同じルーンが入っている時は、配列から取り除く。
            if list(RESULT_DIR.glob(f'./*{str(process_gen)}*{date}*'))[0].as_posix().split(f"{os.sep}")[-1] in documents:
                targetFileName = list(RESULT_DIR.glob(f'./*{str(process_gen)}*{date}*'))[0].as_posix().split(f"{os.sep}")[-1]
                index = [ i for i, v in enumerate(results) if v['file'] == targetFileName ]
                results.pop(index[0])
                with open(JSON_FILE_PATH.as_posix(), 'w') as jf:
                    json.dump(results, jf, indent=4)
                    jf.close()
            else:
                results.append(
                    {
                        'Process_gen' : str(process_gen),
                        'call_method' : call_methods.value,
                        'date' : date,
                        'file' : list(RESULT_DIR.glob(f'./*{str(process_gen)}*{date}*'))[0].as_posix().split(f"{os.sep}")[-1] ,
                        'position' : pos , 
                        'coord_x': x,
                        'coord_y': y,
                        'id' : "0"
                    }
                )
                
                with open(JSON_FILE_PATH.as_posix(), 'w') as jf:
                    json.dump(results, jf, indent=4)
                    jf.close()
            
        
        pprint.pprint(results)
        
        return RedirectResponse('http://192.168.11.8:8000/portal')


@app.get("/exec")
def LockAccess(request: Request):
    global results
    
    #print(fg.DARKRED, datetime.datetime.now().strftime('%Y%m%d %H%M%S') , fg.END)
    
    success_items_count = 0
    failed_items_count = 0
    
    success_items = []
    failed_items  = []
    
    # 画像ファイルの退避先確認
    
    with open(JSON_FILE_PATH.as_posix(), 'r') as jf:
        try:
            results = json.load(jf)
        except:
            return 'target not found 1.'
        finally:
            jf.close()
    
    if len(results) == 0:
        return 'target not found 2.'
    
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
                template = cv2.imread(RESULT_DIR.joinpath(str(record['file'])).as_posix())
                
                #- テンプレートマッチングと、類似率の取得
                matchResult = cv2.minMaxLoc( cv2.matchTemplate(origin, template, cv2.TM_CCOEFF_NORMED) )
                print('[ TemplateMatching Result ]', matchResult)
            
            if matchResult[1] < 0.80: #本番は変更したほうが良いかも0.98とか
                failed_items_count += 1
                failed_items.append(f'<li>{record["file"]}</li><br>')
                
                #return { 'time': f'{datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")}', 'content': 'Template Matching', 'message': f'Matched Rate Failue {matchResult[1]}'}
            else:
            # 引数(unlock, lock, invert)に応じてロックマークの操作をする
                LockMarkOperation(record['call_method'], RESULT_DIR.joinpath(str(record['file'])).as_posix())
                    # サマリエリアのマークを見て、既に希望の状態（unlock だったらロック解除されている）であれば何もしない。
                    # invertは問答無用でクリックする。
                    # 正確性が不明なので、安定してると言えるまではキャプチャをとって送信。
                success_items_count += 1
                success_items.append(f'<li>{record["file"]}</li><br>')
            
    print(fg.DARKRED, 'json remove point', fg.END)
    results = []
    with open(JSON_FILE_PATH.as_posix(), 'w') as jf:
        jf.write("".join(results))
        jf.close()
    return templates.TemplateResponse('dev/index.html', {
        "request": request
        }
    )
@app.get("/clear")
async def ClearArray(request: Request):
    global results
    results = []
    os.remove( JSON_FILE_PATH.as_posix() ) if os.path.isfile(JSON_FILE_PATH.as_posix() ) is True else None
    with open(JSON_FILE_PATH.as_posix(), 'x') as jf:
        jf.write("")
    return templates.TemplateResponse('prod/index.html', {
        "request": request
        }
    )

@app.get("/list")
async def ViewReceivedContent():
    try:
        view_content = "<br>".join( [ f'<li><a href="image/result/\
        {pathlib.Path(v["file"]).name}\
            ">{v["file"]}</a> Operation: {v["call_method"]}</li>' for v in results] )
    except:
        view_content = ""

    return HTMLResponse(f"""
        Locking Operation: <a href="http://192.168.11.8:8000/exec">Run Locking Operation</a><br>
        List Clear: <a href="http://192.168.11.8:8000/clear">List Clear API</a><br>
        <hr>
        Target Items {len(results)}<br>
        {view_content}
        <br><hr>Server Terminate: <a href="http://192.168.11.8:8000/exit">Server Terminate</a><br>
        """
    )


@app.get("/exit")
def exit_uvicorn():
    print(bg.DARKMAGENTA, 'Receive signal self process terminate.', bg.END)
    
    # 親プロセスのPID取得
    self_pid = os.getpid()
    Pprocess = psutil.Process(self_pid)
    
    # 関連子プロセスのPID群を取得,終了
    pid_list = [pc.pid for pc in Pprocess.children(recursive=True)]
    for pid in pid_list:
        psutil.Process(pid).terminate()
    
    # よくわからないが reloader processというのも一緒に消さないと次回サーバがうまく建てられない。watchgodと名前がついてるので関連する別プロセス？
    [psutil.Process(v.pid).terminate() for v in psutil.process_iter() if v.name() == 'uvicorn']

@app.get("/dev")
def Devviewtemplate(request: Request):
    global results
    if type(results) == None or len(results) == 0:
        results = [
            {'process_gen': '20220528131051', 'file': 'Gen-20220528131051_Date-2022-05-28-13-12-48_Position-6_Rarerity-RARE_EstStartMoney-35661404.png', 'call_method': 'unlock', 'date': '2022-05-28-13-12-48', 'position': '6', 'coord_x': '0','coord_y': '0', 'id': "1"},
            {'process_gen': '20220528131051', 'file': 'Gen-20220528131051_Date-2022-05-28-13-12-48_Position-6_Rarerity-RARE_EstStartMoney-35661404.png', 'call_method': 'unlock', 'date': '2022-05-28-13-12-48', 'position': '6', 'coord_x': '0','coord_y': '0', 'id': "2"},
        ]
    #print(results['file'])
    return templates.TemplateResponse('dev/index.html', {
        "request": request,
        "dicts"  : results
        }
    )

@app.get("/portal")
def viewtemplate(request: Request):
    global results
    
    try:
        with open(RECENT_ENHANCED_LIST_PATH, mode='r', encoding='utf-8') as jfp:
            basedict = json.load(jfp)
    except:
        basedict = []
        pass
    
    """
    if type(results) == None or len(results) == 0:
        return templates.TemplateResponse('prod/actionlist.html', {
            "request": request
            }
        )
    """

    # basedictのfileを非再帰的に見て、存在しなければ其のインデックスを削除する。
    basedict = [ v for v in basedict if RESULT_DIR.joinpath(v['file']).exists() ]
    
    return templates.TemplateResponse('prod/index.html', {
        "request": request,
        "basedicts"  : basedict,
        }
    )

@app.get("/actionlist")
def actionlist(request: Request):
    global results
    if type(results) == None or len(results) == 0:
        return templates.TemplateResponse('prod/index.html', {
        "request": request,
        "dicts"  : results
        }
    )
    return templates.TemplateResponse('prod/actionlist.html', {
        "request": request,
        "dicts"  : results
        }
    )