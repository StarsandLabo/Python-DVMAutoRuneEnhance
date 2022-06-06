from audioop import reverse
import re, sys, pathlib, datetime
from types import NoneType
from typing import Type

PROJECT_DIR = pathlib.Path('/home/starsand/DVM-AutoRuneEnhance/')
sys.path.append(PROJECT_DIR.as_posix())
sys.path.append(PROJECT_DIR.joinpath('tools').as_posix())
sys.path.append(PROJECT_DIR.joinpath('lib', 'python3.10', 'site-packages').as_posix())

from tools.TerminalColors import TerminalColors

SUBSTITUTED_RESULT_FILE_PATH = PROJECT_DIR.joinpath(f'./{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}Substituted.txt').as_posix()

class Regexes():
    att_def_true = re.compile( r'[防|攻][御|撃]力' )
    
    att_def_top = re.compile( r'[攻防][^際][^速度御,\']+') #- OK
    att_def_top_type2 = re.compile( r'[攻防][^際][^速度御,\']+') #- OK
    att_def_top_judge = re.compile(r'(攻|防)(御|撃)?[カ力]+')
    
    att_def_center = re.compile( r'[^反][御撃][^速度,\']+' ) #- OK
    crit_d       = re.compile( r'クリティ[カ力]ル[^率,\']+')
    crit_d_indivisual = re.compile(r'(クリテ|ウリティ)(?=\')')
    crit_d_indivisual_type2 = re.compile(r'(クリテ|ウリティ)[^\']*')
    # 'クリテ'or'ウリティ'の形であってほしい。
    # クリティカルダメージ(クリティカル率)は除外したい。
    # クリテの時'ィカルダメージ'が続かないものをマッチ条件にしたい。?!多分これ
    
    
    otherObject = {
        '回避': re.compile( r'(回.)|(.避)' ),
        '命中': re.compile( r'((?<!効果).中)|((?<!効果)命.)'),
        '効果抵抗': re.compile( r'効果[^命][^中]') 
    }
    #evation      = re.compile( r'(回.)|(.避)' )
    #acc_r        = re.compile( r'(.中)|(命.)')
    #res_effect   = re.compile( r'効果[^命]抵?[^中]抗?')



rx = Regexes()

fg = TerminalColors.fg

bg = TerminalColors.bg
bg.AddWebColor('mediumblue', '#0000cd')
bg.AddWebColor('orange', '#ff4500')

class TestWords():
    # 最初の2つが正
    words_att_def = ['攻撃力','防御力','防伽力', '防僅力', '防爺力', '防件力', '防全力', '防御カ', '防御カカ', '際御カカ', '攻内力', '攻沿力']
    #
    #* くりて、ウリティは個別対応
    words_crit_d =['クリティカルダメージ','クリテ', 'クリティカルタダメージ', 'ウリティ', 'クリティカルタメーンジ', 'クリティカルダメーンジ', 'クリティカルダメーン', 'クリティカルタメージ', 'クリティカルダメーンジン', 'クリティカルタダメーンジ']
    #
    words_other = ['回可','便中','回間']

class Message():
    def Message(result, input_origin, emphasis=None, parentFuncName=sys._getframe().f_code.co_name):
        if emphasis:
            
            input_origin_foundpoints = [ m.span() for m in re.finditer(emphasis[0],input_origin) ]
            
            #? print(input_origin_foundpoints)
            view_input_origin = list(input_origin)
            for input_origin_foundpoint in reversed(input_origin_foundpoints):
                view_input_origin.insert(input_origin_foundpoint[0], f'{bg.MEDIUMBLUE}')
                view_input_origin.insert(input_origin_foundpoint[1] + 1, fg.END)
            view_input = "".join(view_input_origin)
            
            #print(result, type(result), emphasis[1])
            result_origin_foundpoints = [ m.span() for m in re.finditer(emphasis[1], result) ]
            
            view_result_origin = list(result)
            for result_origin_foundpoint in reversed(result_origin_foundpoints):
                view_result_origin.insert(result_origin_foundpoint[0], f'{bg.ORANGE}')
                view_result_origin.insert(result_origin_foundpoint[1] + 1, fg.END)
            view_result = "".join(view_result_origin)
            #print('view input', view_input)
            #print(result_origin_foundpoints)
            #input(f'view result preview {view_result}')
            
            ret = (f'[ {parentFuncName} ]\n{fg.DARKCYAN}Input{fg.END} : {view_input}\n{bg.DARKYELLOW}{fg.DARKRED}Result{fg.END}: {view_result}')
        #
        else:
            ret = (f'[ {parentFuncName} ]\n{fg.DARKCYAN}Input{fg.END} : {input_origin}\n{fg.DARKRED}Result{fg.END}: {result}')
        #
        return ret
class IndividualSubstites():
    crit_d = ['クリテ', 'ウリティ'] #クリティカルダメージのやつ




# 正規の値ならそのまま値を返す。そうでない時は一文字目を見るパターン２文字目を見るパターンでそれぞれ置換する。
def Substitute_att_def(word, silent=False):
    rx = Regexes()
    ret = word # for return value
    
    for RegexCondition in [Regexes.att_def_top_type2, Regexes.att_def_center]:
        if RegexCondition.findall(ret):
            #print(fg.CYAN,ret,fg.END)
            spanAndGroups = [ v for v in RegexCondition.finditer(ret) ]
            tmparray = list(ret)
            
            for value in reversed(spanAndGroups):
                tmparray[value.span()[0]:value.span()[1]] = []
                
                if RegexCondition.search(value.group()).group()[0] == '攻':
                    insertword = '攻撃力'
                else:
                    insertword = '防御力'
                tmparray.insert(value.span()[0], insertword)
            print( Message.Message(result="".join(tmparray), input_origin=ret, emphasis=(RegexCondition, re.compile(insertword)), parentFuncName=sys._getframe().f_code.co_name + f": {insertword}" ) ) if silent == False else True
            ret = "".join(tmparray)
        else:
            print( Message.Message(result=f'{ret} ({fg.YELLOW}Exception ret or No Substituted{fg.END})', input_origin=ret, parentFuncName=sys._getframe().f_code.co_name ) )if silent == False else True
            ret = word
    
    return ret

    #- findallによって全ての語を見る必要がある。
    """
    if not rx.att_def_true.search(ret):
        
        #[v.group() for v in rx.att_def_true.findall(ret)]
        #spans =[ v.span() for v in rx.att_def_top.finditer(ret) ]
        #print(fg.BLUE,spans,fg.END)
        #input()
        if rx.att_def_top.search(ret):
            #print(rx.att_def_top.search(word))
            #judge = re.sub(rx.att_def_top, r'\1\2力', word)
            #input(f'{rx.att_def_top.search(word).group()}[0]: {rx.att_def_top.search(word).group()[0]} [1]: {rx.att_def_top.search(word).group()[1]}')
            print(rx.att_def_top.search(ret).group(),rx.att_def_top.search(ret).group()[0])
            if  (rx.att_def_top.search(ret).group()[0]  == '攻') and \
                (rx.att_def_top.search(ret).group()     != '攻撃速度') :
                print( Message.Message(result=rx.att_def_top.sub('攻撃力', ret), input_origin=ret, emphasis=(rx.att_def_top, rx.att_def_true), parentFuncName=sys._getframe().f_code.co_name  ) ) if silent == False else True
                ret = rx.att_def_top.sub('攻撃力', word)
            else:
                print( Message.Message(result=rx.att_def_top.sub('防御力', ret), input_origin=ret, emphasis=(rx.att_def_top, rx.att_def_true), parentFuncName=sys._getframe().f_code.co_name ) ) if silent == False else True
                ret = rx.att_def_top.sub('防御力', ret)
        
        if rx.att_def_center.search(ret):
            #input(f'{rx.att_def_center.search(ret).group()}[0]: {rx.att_def_center.search(ret).group()[0]} [1]: {rx.att_def_center.search(ret).group()[1]}')
            
            if  (rx.att_def_center.search(ret).group()[1]  == '撃' or '御') and \
                (rx.att_def_center.search(ret).group()     != '攻撃速度') :
                #input(f'{rx.att_def_center.search(ret).group()}[0]: {rx.att_def_center.search(ret).group()[0]} [1]: {rx.att_def_center.search(ret).group()[1]}')
            
                print( Message.Message(result=rx.att_def_center.sub('攻撃力', ret), input_origin=ret, emphasis=(rx.att_def_center, rx.att_def_true), parentFuncName=sys._getframe().f_code.co_name ) ) if silent == False else True
                ret = rx.att_def_center.sub('攻撃力', ret)
                word = rx.att_def_center.sub('攻撃力', ret)
            else:
                print( Message.Message(result=rx.att_def_center.sub('防御力', ret), input_origin=ret, emphasis=(rx.att_def_center, rx.att_def_true), parentFuncName=sys._getframe().f_code.co_name ) ) if silent == False else True
                ret = rx.att_def_center.sub('防御力', ret)
                word = rx.att_def_center.sub('防御力', ret)
    """

# クリテやウリティとクリティカルダメージが一緒にいると対応できないので修正する。
def Substitute_crit_d(word, silent=False):
    rx = Regexes()
    ret = word
    
    if rx.crit_d.search(word):
        if not rx.crit_d.search(word).group() == 'クリティカルダメージ':
            print( Message.Message(result=rx.crit_d.sub('クリティカルダメージ', word), input_origin=word, emphasis=(rx.crit_d, 'クリティカルダメージ'), parentFuncName=sys._getframe().f_code.co_name + ": 基本" ) ) if silent == False else True
            ret = rx.crit_d.sub('クリティカルダメージ', word)
        else:
            print( Message.Message(result=f'{word} ({fg.DARKGREEN}Exception Word or No Substituted{fg.END})', input_origin=word, parentFuncName=sys._getframe().f_code.co_name ) ) if silent == False else True
            ret = word
    else:
        ret = word
    
    #input()
    #  そもそもここで認識されていない。
    # 再起処理だとクリティカルダメージがクリテを内包しているのでループが切れなくなる。
    # 先読みか後読みの正規表現を定義してあげる。
    # 複数存在することはあり得るので、まずfinditerかfindallでクリテorウリティと合致した時該当spanの内容を削除してインサートする。
    #+ finditerでとってきた領域だけ切り取ってそれがクリテorウリティとイコールになるかを比べる。
    #- ifが必要
    if rx.crit_d_indivisual.findall(ret):
        for tgtword in IndividualSubstites.crit_d:
            #?print( [ v.span() for v in rx.crit_d_indivisual_type2.finditer(ret) if v.group() == tgtword ] )
            try:
                spans = [ v.span() for v in rx.crit_d_indivisual_type2.finditer(ret) if v.group() == tgtword ]
                tmpline = list(ret)
                tmpline[spans[0][0]:spans[0][1]] = []
                tmpline.insert(spans[0][0], 'クリティカルダメージ')
                print( Message.Message(result="".join(tmpline), input_origin=ret, emphasis=(rx.crit_d_indivisual_type2, tgtword), parentFuncName=sys._getframe().f_code.co_name + f": 個別対応 {tgtword}" ) ) if silent == False else True
                ret = "".join(tmpline)
                
                print(ret)
                #input()
            except IndexError:
                pass
    
    """
    for condition in IndividualSubstites.crit_d:
        def IndividualCheck(arg,line):
            if arg in line:
                print( Message.Message(result=rx.crit_d_indivisual.sub('クリティカルダメージ', line), input_origin=line, emphasis=(rx.crit_d_indivisual, 'クリティカルダメージ'),parentFuncName=sys._getframe().f_code.co_name + ": 個別対応" ) ) if silent == False else True
                ret = rx.crit_d_indivisual.sub('クリティカルダメージ', line)
                IndividualCheck(arg=condition, line=ret)
            else:
                print( Message.Message(result=f'{word} ({fg.DARKGREEN}Exception Word or No Substituted{fg.END})', input_origin=word, parentFuncName=sys._getframe().f_code.co_name + ": 個別対応" ) ) if silent == False else True
                ret = word
            return ret
        
        trueret = IndividualCheck(arg=condition, line=ret)
    """
    
    return ret

def Substitute_others(inputword, silent=False, recursiveFlag=True):
    rx = Regexes()
    nextRecursive = recursiveFlag
    ret = inputword
    tmpret = ""
    
    #input(f'{bg.ORANGE}{ret}{bg.END}')
    for key, pattern in rx.otherObject.items():
        #?print(fg.ORANGE,key,fg.END,f'{fg.CYAN}{ret}{fg.END}')
        if pattern.findall(ret):
            try:
                if not key in pattern.findall(ret)[0]:
                    #? print(fg.ORANGE,key,fg.END,bg.BLUE, 'true statement', bg.END,tmpret)
                    print( Message.Message(result=pattern.sub(key, ret), input_origin=ret, emphasis=(pattern, key), parentFuncName=sys._getframe().f_code.co_name + f": {key}") ) if silent == False else None 
                    tmpret = pattern.sub(key, ret)
                    #? print(bg.DARKRED, 'substituted', bg.END,"\n",tmpret)
                    ret = tmpret
                    #input(f'{fg.DARKGREEN}{ret}{bg.END}')
                    #? print(key, list(rx.otherObject.keys())[-1], type(list(rx.otherObject.keys())[-1]))
                    nextRecursive = True if key != list(rx.otherObject.keys())[-1] else False
                    break
                else:
                    #? print(fg.ORANGE,key,fg.END,bg.DARKGREEN, 'else statement', bg.END,tmpret)
                    print( Message.Message(result=ret + ' (No Substituted)', input_origin=ret, parentFuncName=sys._getframe().f_code.co_name + f": {key}") ) if silent == False else None 
                    nextRecursive = False
            except IndexError:
                input(f"{bg.ORANGE} IndexError {bg.END}")
        else:
            print( Message.Message(result=ret + ' (No Substituted)', input_origin=ret, parentFuncName=sys._getframe().f_code.co_name + f": {key}") ) if silent == False else None 
            nextRecursive = False
            #return ret
    
    if nextRecursive == True:
        return Substitute_others(inputword=ret, recursiveFlag=nextRecursive)
    else:
        #? print(fg.DARKYELLOW,ret,fg.END)
        return ret


if __name__ == '__main__':
    with open('/home/starsand/DVM-AutoRuneEnhance/work/ocr2022-06-03_11-41-11.tsv', mode='r') as fp:
        targets = fp.read()
    
    #print(targets)
    #input()
    def rexcheck(target):
        
    #if True == False
        string = Substitute_crit_d(target)
        if string == None:
            print(fg.YELLOW, string, fg.END)
            input()
        
        string2 = Substitute_others(string)
        if string2 == None:
            print(fg.YELLOW, string2, fg.END)
            input()
        
        string3 = Substitute_att_def(string2)
        #string3 = Substitute_att_def(string2)
        print(bg.DARKMAGENTA,string3,bg.END)
        if string3 == None:
            print(fg.RED, string3, fg.END)
        
        return string3
    
    adjusted = ""
    for target in targets.split("\n"):
        print()
        #print(target, type(target))
        adjusted += rexcheck(target) + "\n"
            
    with open(SUBSTITUTED_RESULT_FILE_PATH, mode='w') as fp:
        fp.write(adjusted)
    
    print(bg.ORANGE,'Result',bg.END, 'cat', SUBSTITUTED_RESULT_FILE_PATH )
    
    #? test
    targetword = "'攻撃カ'"
    import subprocess
    print(bg.DARKGREEN,f'Auto Grepping Result (Word: {targetword})',bg.END,sep="")
    subprocess.Popen([f'grep -i "{targetword}" {SUBSTITUTED_RESULT_FILE_PATH}'],shell=True)
    #for word in TestWords.words_att_def:
    #    Substitute_att_def(word, silent=False)
    #    Substitute_crit_d(word, silent=False)
    #    Substitute_others(word, silent=False)

#    print(Substitute_att_def(word, silent=False))



#re.sub()では第一引数に正規表現パターン、第二引数に置換先文字列、第三引数に処理対象の文字列を指定する。


# 辞書整理用
#print( list(set(tmpwords)) )

