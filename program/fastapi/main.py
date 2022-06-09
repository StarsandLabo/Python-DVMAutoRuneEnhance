import pathlib, sys
from subprocess import call
from enum import Enum, auto
import re, datetime, pprint, os, shutil
import tempfile
from types import NoneType
from xml.dom.xmlbuilder import DocumentLS

from numpy import cov, single

PROJECT_DIR = pathlib.Path('/home/starsand/DVM-AutoRuneEnhance/')
sys.path.append(PROJECT_DIR.as_posix())
sys.path.append(PROJECT_DIR.joinpath('tools').as_posix())
sys.path.append(PROJECT_DIR.joinpath('lib', 'python3.10', 'site-packages').as_posix())
sys.path.append(PROJECT_DIR.joinpath('program').as_posix())
sys.path.append(PROJECT_DIR.joinpath('program','database').as_posix())

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
from pydantic import BaseModel, Field
import mariadb
import mariadb_practice as db

#os.chdir(PROJECT_DIR.joinpath('program', 'fastapi').as_posix())
with open( db.MARIADB_PASSWORD_PATH, mode='r', encoding='utf-8') as fp:
    secret = fp.read().splitlines()[0]
    
try:
    conn = mariadb.connect(
        user = 'starsand',
        password = secret,
        host = 'localhost',
        port = 3306
    )
    
except mariadb.Error as e:
    print(f"Error connecting to MariaDB Platform: {e}")
    sys.exit(1)
    

cur = conn.cursor()



lnToken = linetools.getToken() # Line Notify 用のトークン取得
fg = tc.fg #フォアグラウンド 色つけ用
bg = tc.bg #バックグラウンド 色つけ用

templates = Jinja2Templates(directory="templates")

class PathName_Methods(str, Enum):
    unlock = 'unlock'
    lock   = 'lock'
    invert = 'invert'

class StrEnum(Enum):
    @staticmethod
    def _generate_next_value_(name: str, start: int, count: int) -> str:
        return name

class LockingOperations(StrEnum):
    unlock = 'unlock'
    lock   = 'lock'

class PostReceivedFromUser(BaseModel):
    Process_gen : str# = Field("",       title="Execution generation")
    call_method : str# = Field("unlock", title="Type of Locking operation(unlock/lock)")
    coord_x     : str# = Field("",       title="target x axis")
    coord_y     : str# = Field("",       title="target y axis")
    date        : str# = Field("",       title="datetime")
    file        : str# = Field("",       title="filename")
    position    : str# = Field("",       title="Equip position")

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

def GetBaseDict():
    try:
        with open(RECENT_ENHANCED_LIST_PATH, mode='r', encoding='utf-8') as jfp:
            basedict = json.load(jfp)
    except:
        basedict = []
        pass

    # basedictのfileを非再帰的に見て、存在しなければ其のインデックスを削除する。
    
    return [ v for v in basedict if RESULT_DIR.joinpath(v['file']).exists() ]

# 画像退避先の確認と作成。
if not RESULT_DIR.joinpath('AfterLockingOperation', 'divert', 'images', 'dev').exists():
    RESULT_DIR.joinpath('AfterLockingOperation', 'divert', 'images', 'dev').mkdir(exist_ok=False, parents=True)

def GetCurrentProcessGen():
    try:
        # 実行世代をファイルから取得
        with open(PROCESS_GENERATION_FILE_DIR.joinpath(PROCESS_GENERATION_FILE_NAME).as_posix(), 'r') as fp:
            saved_gen = fp.read()
    except:
        print(f'[ {sys._getframe().f_code.co_name} ]', fg.DARKRED, 'Operaton Failed', fg.END)
        return
    
    return saved_gen

def LogWrite(dictionary, logfilepath='./testlogs.log'):
    # 受け取ったJsonデータをログファイルに追記
    try:
        with open(logfilepath, 'a') as fp:
            fp.write(", ".join(
                [
                                dictionary['call_method'],
                                dictionary['Process_gen'],
                                dictionary['date'],
                                dictionary['file'],
                                dictionary['position'],
                                dictionary['coord_x'],
                                dictionary['coord_y']
                ]
                            )
                    + "\n"
                    )
    except:
        print(f'[ {sys._getframe().f_code.co_name} ]', fg.DARKRED, 'Operaton Failed', fg.END)
    
    return

def JsonWrite(content=results, path=JSON_FILE_PATH.as_posix() ):
    try:
        with open(path, 'w') as jf:
            json.dump(content, jf, indent=4)
            jf.close()
    except:
        print(f'[ {sys._getframe().f_code.co_name} ]', fg.DARKRED, 'Operaton Failed', fg.END)
        return

def ValidateProcessGenAndFilepath(dictionary, Process_gen):
    if re.fullmatch(r'\d{14}', dictionary['Process_gen'] ):
        # ProcessGenerationがクエリパラメータと現在保存されている値で一致するか
        if not int(dictionary['Process_gen']) == int(Process_gen):
            errormessage = 'process_gen did not match received query.'
            print(f'[ {sys._getframe().f_code.co_name} ]', errormessage)
            return { 'time': f'{datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")}', 'received': dictionary['Process_gen'], 'message': errormessage}
            
        # globの戻りは1つの値か(時刻を利用しているので基本一つ)
        elif not len( list(RESULT_DIR.glob(f"./*{dictionary['Process_gen']}*{dictionary['date']}*") ) ) == 1:
            errormessage = 'Found items over quantity limit.'
            print(f'[ {sys._getframe().f_code.co_name} ]', errormessage)
            return {
                'time': f'{datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")}',
                'message': errormessage
            }
        
        else:
            return True

def LocalFileSearch(gen, date):
    targetpath = str(list(RESULT_DIR.glob(f"./*{gen}*{date}*"))[0].as_posix().split(f"{os.sep}")[-1])
    return targetpath

def UpdateResults(dictionary, results=results):
    print(f'[ {sys._getframe().f_code.co_name} ]',results)
    # 検証がOKだった時、アイテムを格納する。
    
    # 初回resultsが何もない時は、resultsに辞書を追加し、Jsonファイルへ書き込む
    # resultsの配列が1つ以上の時、同じファイル名が含まれているか確認し、含まれていれば何もしない。
    try:
        print('try statement', results,"\n")
    except:
        print(f'[ {sys._getframe().f_code.co_name} ]', fg.DARKRED, 'Operaton Failed', fg.END)
        return
    
    #print( LocalFileSearch(gen=dictionary['Process_gen'], date=dictionary['date']) )
    if results == None or len(results) == 0:
        results = []
        results.append(
            {
                'Process_gen'   : dictionary['Process_gen'],
                'call_method'   : dictionary['call_method'],
                'date'          : dictionary['date'],
                'file'          : LocalFileSearch(gen=dictionary['Process_gen'], date=dictionary['date']) ,
                'position'      : int(dictionary['position']) , 
                'coord_x'       : int(dictionary['coord_x']),
                'coord_y'       : int(dictionary['coord_y']),
                'id'            : "0"
            }
        )
        
        JsonWrite(content=results)
        print(f'[ {bg.DARKCYAN}{sys._getframe().f_code.co_name}{bg.END} ] True statement: items', len(results),"\n")
        return results
            
    else:
        # バリデーション用に一時的にオブジェクトを作成
        CheckJSON()
        
        #print(f'[ {sys._getframe().f_code.co_name} ] Json file path: ', JSON_FILE_PATH.as_posix() )
        with open(JSON_FILE_PATH.as_posix(), 'r') as jfp:
            documents = jfp.read()
        
        item = LocalFileSearch(gen=dictionary['Process_gen'], date=dictionary['date'])
        print(item, type(item))
        print('documents',documents)
        # 既に同じルーンが入っている時は、配列から取り除く。
        if item in documents:
            index = [ i for i, v in enumerate(results) if v['file'] == item ]
            results.pop(index[0])
            print(bg.RED, index, bg.END)
            pprint.pprint(results)
            print(f'[ {bg.DARKCYAN}{sys._getframe().f_code.co_name}{bg.END} ] else > True statement: items', len(results),"\n")
            JsonWrite(content=results)
        else:
            results.append(
                {
                    'Process_gen'   : dictionary['Process_gen'],
                    'call_method'   : dictionary['call_method'],
                    'date'          : dictionary['date'],
                    'file'          : LocalFileSearch(gen=dictionary['Process_gen'], date=dictionary['date']),
                    'position'      : int(dictionary['position']) , 
                    'coord_x'       : int(dictionary['coord_x']),
                    'coord_y'       : int(dictionary['coord_y']),
                    'id'            : "0"
                }
            )
            
            JsonWrite(content=results)
            print(f'[ {bg.DARKMAGENTA}{sys._getframe().f_code.co_name}{bg.END} ] else > else statement: items', len(results),"\n")
            return results


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

def GetActiveTable(c=cur):
    c.execute('SELECT * FROM runelist;')
    return c.fetchall()

def GetColumnNames(c=cur,syncGetActiveTable=True):
    c.execute('desc runelist;')
    if syncGetActiveTable:
        columns = [ v[0] for v in cur.fetchall() ]
        columns.remove('annotation')
        columns.remove('digest')
        return columns
    else:
        return [ v[0] for v in cur.fetchall() ]

def GetRecordsForHTML(c=cur):
    c.execute('USE dvm_auto_rune_enhance')
    data = GetActiveTable()
    columns = GetColumnNames(syncGetActiveTable=True)
        
    DictRecord = []
    for record in data:
        DictRecord.append(dict(zip(columns, record)))
        

    ConvertedDict = []
    for record in DictRecord:
        ConvertedDictRecord = {}
        
        for single_key in list(record.keys()):
            if  type(record[single_key]) == float:
                if int(record[single_key]) < 2:
                    ConvertedDictRecord[single_key] = str(int( ( record[single_key] - 1 ) * 100 )) + "%"
                else:
                    ConvertedDictRecord[single_key] = int(record[single_key])
            else:
                ConvertedDictRecord[single_key] = record[single_key]
        ConvertedDict.append(ConvertedDictRecord)
            
            
    return ConvertedDict

fg = tc.fg
bg = tc.bg

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

@app.post('/post')
async def posttest(payload: PostReceivedFromUser):
    Converted = {}
    print(fg.GREEN,'Received Payload',fg.END,datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), sep="")
    print(type(payload), [f'{i}: {v}' for i, v in enumerate(payload)])
    for record in payload:
        Converted[record[0]] = record[1]
    print(f'{fg.RED}\ndicted\n{fg.END}', Converted)
    
    SavedCurrentProcessGeneration = GetCurrentProcessGen()
    LogWrite(Converted)
    if ValidateProcessGenAndFilepath(Converted, SavedCurrentProcessGeneration) == True:
        print('[ /post ] ', 'true statement')
        global results
        results = UpdateResults(dictionary=Converted, results=results)
    else:
        print('[ /post < Validation Process_gen and Saved image file path > ] ', "Converted['Process_gen']:", Converted['Process_gen'], "SavedCurrentProcessGeneration:", SavedCurrentProcessGeneration)
    
    return ['post ok', payload]


@app.get('/possesion')
def possesion(request: Request):
    records = GetRecordsForHTML()
    pprint.pprint(records[0])
    """
    def possesion(request: Request):
        records = GetRecordsForHTML()
        pprint.pprint(records[0])
        
        return templates.TemplateResponse('prod/possesion.html', {
            "request"  : request,
            "records"  : records
            }
        )
    """
    return templates.TemplateResponse('prod/possesion.html', {
        "request": request,
        "records"  : records
        }
    )


@app.post("/{process_gen}")
async def ReadPostedItem(request: Request, params: Optional[str] = Form(None)):
    receivcedParameters = params.split(',')

    try:
        RECEIVED_MASTER
    except NameError:
        RECEIVED_MASTER = []

    
    # indexを2で割った余りが0の時はキー、1の時は値となるリストを作成する。
    # 辞書を2つに分けて、Zipで結合売る。
    keys = []
    values = []
    for i, item in enumerate(receivcedParameters):
        keys.append(item) if i % 2 == 0 else values.append(item)
    zipped = zip(keys, values)
    RECEIVED_MASTER.append(dict(zipped))

    def LocalFileSearch(gen=RECEIVED_MASTER[0]['Process_gen'], date=RECEIVED_MASTER[0]['date']):
        targetpath = str(list(RESULT_DIR.glob(f"./*{gen}*{date}*"))[0].as_posix().split(f"{os.sep}")[-1])
        return targetpath
    
    #received = json.JSONEncoder.encode(params)
    print(fg.DARKCYAN,'received params', fg.END, "\n", RECEIVED_MASTER)
    
    global results
    
    # 実行世代をファイルから取得
    with open(PROCESS_GENERATION_FILE_DIR.joinpath(PROCESS_GENERATION_FILE_NAME).as_posix(), 'r') as fp:
        saved_gen = fp.read()
    
    # 受け取ったJsonデータをログファイルに書き込み
    with open('./testlogs.log', 'a') as fp:
        fp.write(", ".join(
            [
                            RECEIVED_MASTER[0]['call_method'],
                            RECEIVED_MASTER[0]['Process_gen'],
                            RECEIVED_MASTER[0]['date'],
                            RECEIVED_MASTER[0]['file'],
                            RECEIVED_MASTER[0]['position'],
                            RECEIVED_MASTER[0]['coord_x'],
                            RECEIVED_MASTER[0]['coord_y']
            ]
                        )
                + "\n"
                )
    
    if re.fullmatch(r'\d{14}', RECEIVED_MASTER[0]['Process_gen'] ):
        print(RECEIVED_MASTER[0]['Process_gen'], saved_gen)
        # ProcessGenerationがクエリパラメータと現在保存されている値で一致するか
        if not int(RECEIVED_MASTER[0]['Process_gen']) == int(saved_gen):
            return { 'time': f'{datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")}', 'received': RECEIVED_MASTER[0]['Process_gen'], 'message': 'process_gen did not match received query.'}
            
        # globの戻りは1つの値か(時刻を利用しているので基本一つ)
        elif not len( list(RESULT_DIR.glob(f"./*{RECEIVED_MASTER[0]['Process_gen']}*{RECEIVED_MASTER[0]['date']}*") ) ) == 1:
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
        
        print( LocalFileSearch() )
        if results == None or len(results) == 0:
            results = []
            results.append(
                {
                    'Process_gen'   : RECEIVED_MASTER[0]['Process_gen'],
                    'call_method'   : RECEIVED_MASTER[0]['call_method'],
                    'date'          : RECEIVED_MASTER[0]['date'],
                    'file'          : LocalFileSearch() ,
                    'position'      : int(RECEIVED_MASTER[0]['position']) , 
                    'coord_x'       : int(RECEIVED_MASTER[0]['coord_x']),
                    'coord_y'       : int(RECEIVED_MASTER[0]['coord_y']),
                    'id'            : "0"
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
            
            item = LocalFileSearch()
            # 既に同じルーンが入っている時は、配列から取り除く。
            if item in documents:
                index = [ i for i, v in enumerate(results) if v['file'] == item ]
                results.pop(index[0])
                with open(JSON_FILE_PATH.as_posix(), 'w') as jf:
                    json.dump(results, jf, indent=4)
                    jf.close()
            else:
                results.append(
                    {
                        'Process_gen'   : RECEIVED_MASTER[0]['Process_gen'],
                        'call_method'   : RECEIVED_MASTER[0]['call_method'],
                        'date'          : RECEIVED_MASTER[0]['date'],
                        'file'          : list(RESULT_DIR.glob(f"./*{RECEIVED_MASTER[0]['Process_gen']}*{RECEIVED_MASTER[0]['date']}*"))[0].as_posix().split(f"{os.sep}")[-1] ,
                        'position'      : int(RECEIVED_MASTER[0]['position']) , 
                        'coord_x'       : int(RECEIVED_MASTER[0]['coord_x']),
                        'coord_y'       : int(RECEIVED_MASTER[0]['coord_y']),
                        'id'            : "0"
                    }
                )
                
                with open(JSON_FILE_PATH.as_posix(), 'w') as jf:
                    json.dump(results, jf, indent=4)
                    jf.close()
            
        
        pprint.pprint(results)
    
    basedicts = GetBaseDict()
    abilities = None
    
    try:
        basedicts[0]['abilities']['file']
        basedicts[0]['abilities'].pop('file')
        abilities = basedicts[0]['abilities']
    except:
        pass
    return templates.TemplateResponse('prod/index.html', {
        "request": request,
        "basedicts"  : basedicts,
        "abilities"  : abilities
        }
    )

    #return RedirectResponse('http://192.168.11.8:8000/portal')


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
    return templates.TemplateResponse('prod/index.html', {
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
    
    try:
        basedict[0]['abilities']
    except:
        pass
    
    # tableを作るためにキーを削除する
    try:
        basedict[0]['abilities']['file']
        basedict[0]['abilities'].pop('file')
        abilities = basedict[0]['abilities']
    except:
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
        "abilities" : abilities
        }
    )


@app.get("/actionlist")
def actionlist(request: Request):
    global results
    if type(results) == NoneType or None or len(results) == 0:
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

