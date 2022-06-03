import re, sys, pathlib

PROJECT_DIR = pathlib.Path('/home/starsand/DVM-AutoRuneEnhance/')
sys.path.append(PROJECT_DIR.as_posix())
sys.path.append(PROJECT_DIR.joinpath('tools').as_posix())
sys.path.append(PROJECT_DIR.joinpath('lib', 'python3.10', 'site-packages').as_posix())

from tools.TerminalColors import TerminalColors

class TestWords():
    # 最初の2つが正
    words_att_def = ['攻撃力','防御力','防伽力', '防僅力', '防爺力', '防件力', '防全力', '防御カ', '防御カカ', '際御カカ', '攻内力', '攻沿力']

    #* くりて、ウリティは個別対応
    words_crit_d =['クリティカルダメージ','クリテ', 'クリティカルタダメージ', 'ウリティ', 'クリティカルタメーンジ', 'クリティカルダメーンジ', 'クリティカルダメーン', 'クリティカルタメージ', 'クリティカルダメーンジン', 'クリティカルタダメーンジ']

    words_other = ['回可','便中','回間']


class IndividualSubstites():
    crit_d = ['クリテ', 'ウリティ'] #クリティカルダメージのやつ

class Regexes():
    att_def_true = re.compile( r'(防|攻)(御|撃)(力)' )
    att_def_top = re.compile( r'(攻|防)(.)..*$') #- OK
    att_def_center = re.compile( r'(.)(御|撃)..*$' ) #- OK
    
    crit_d       = re.compile( r'クリティ(カ|力)ル[^率].*$')
    
    evation      = re.compile( r'(回.)|(.避)' )
    
    acc_r        = re.compile( r'(.中)|(命.)')

rx = Regexes()
fg = TerminalColors.fg
bg = TerminalColors.bg

# 正規の値ならそのまま値を返す。そうでない時は一文字目を見るパターン２文字目を見るパターンでそれぞれ置換する。
def Substitute_att_def(word, silent=False):
    rx = Regexes()
    
    def Message(result, input=word, parentFuncName=sys._getframe().f_code.co_name):
        ret = (f'[ {parentFuncName} ] {fg.DARKCYAN}Input{fg.END}: {input} {fg.DARKRED}Result{fg.END}: {result}')
        return ret
    
    if not rx.att_def_true.search(word):
        
        if rx.att_def_top.search(word):
            print( Message(result='攻撃力') ) if silent == False else True
            re.sub(rx.att_def_top, r'\1\2力', word)
            
            if word[0] == '攻':
                print( Message(result='攻撃力') ) if silent == False else True
                return '攻撃力'
            else:
                print( Message(result='防御力') ) if silent == False else True
                return '防御力'
        
        if rx.att_def_center.search(word):
            re.sub(rx.att_def_center,r'\1\2力', word)
            
            if word[1] == '撃':
                print( Message(result='攻撃力') ) if silent == False else True
                return '攻撃力'
            else:
                print( Message(result='防御力') ) if silent == False else True
                return '防御力'
    else:
        print( Message(result=f'{word} (No Substituted)') ) if silent == False else True
        return word

def Substitute_crit_d(word, silent=False):
    rx = Regexes()
    
    def Message(result, input=word, parentFuncName=sys._getframe().f_code.co_name):
        ret = (f'[ {parentFuncName} ] {fg.DARKCYAN}Input{fg.END}: {input} {fg.DARKRED}Result{fg.END}: {result}')
        return ret
    
    if rx.crit_d.search(word):
        print( Message(result='クリティカルダメージ') ) if silent == False else True
        return 'クリティカルダメージ'
    elif word in IndividualSubstites().crit_d:
        print( Message(result='クリティカルダメージ') ) if silent == False else True
        return 'クリティカルダメージ'
    else:
        print( Message(result=f'{word} (Exception Word or No Substituted)') ) if silent == False else True
        return word

def Substitute_others(word, silent=False):
    rx = Regexes()
    
    def Message(result, input=word, parentFuncName=sys._getframe().f_code.co_name):
        ret = (f'[ {parentFuncName} ] {fg.DARKCYAN}Input{fg.END}: {input}, {fg.DARKRED}Result{fg.END}: {result}')
        return ret
    
    if rx.acc_r.search(word):
        print( Message(result='命中') ) if silent == False else True
        return '命中'
    elif rx.evation.search(word):
        print( Message(result='回避') ) if silent == False else True
        return '回避'
    else:
        print( Message(result=f'{word} (Exception Word or No Substituted)') ) if silent == False else True
        return word

if __name__ == '__main__':
    for word in TestWords.words_att_def:
        Substitute_att_def(word, silent=False)
        Substitute_crit_d(word, silent=False)
        Substitute_others(word, silent=False)

#    print(Substitute_att_def(word, silent=False))



#re.sub()では第一引数に正規表現パターン、第二引数に置換先文字列、第三引数に処理対象の文字列を指定する。


# 辞書整理用
#print( list(set(tmpwords)) )