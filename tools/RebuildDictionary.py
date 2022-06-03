from genericpath import exists
import pprint
import sys
#basedictionary_origin = [[{'Main': {'Name': '攻撃力', 'Value': '984'}}, {'Sub': {'Name': '回避', 'Value': '7%'}}, {'1': {'Name': '効果抵抗', 'Value': '17%'}}, {'2': {'Name': 'クリティカルダメーンジン', 'Value': '9%'}}, {'3': {'Name': '防御力', 'Value': '4%'}}, {'4': {'Name': '攻撃速度', 'Value': '10%'}}, {'file': '/home/starsand/DVM-AutoRuneEnhance/work/img/tmpfmiphdlw_summary.png'}]]

def ExistSub(array):
    result = []
    for target in array:
        #まず {
            # 'Main' : { '攻撃力': "984" },
            # 'Sub'  : { '回避': "7%" },
        #}
        # みたいな形にしたい。元のイケてない形のほうが挿入するには楽そう
        # リストを回して、キーにサブが含まれているかどうか確認する。
        result.append( list(target.keys())[0] == 'Sub' )
        
        # ついでにファイル名は
    #input(f'{sys._getframe().f_code.co_name}: {result}')
    return result

# リストを再構成する
def RebuildListToDictionary(TargetList):
    result = {}
    for target in TargetList:
        StatusName = list(target.keys())[0]
        
        if StatusName == 'file':
            result[StatusName] = target[StatusName]
            continue
        else:
            result[StatusName] = []
        
        #print(target[StatusName], type(target[StatusName]),list(target[StatusName].keys()))
        
            
        for StatusValuesKey in target[StatusName].keys():
            #print(StatusValuesKey, type(StatusValuesKey))
            result[StatusName].append(target[StatusName][StatusValuesKey])
            
    #input(f'{sys._getframe().f_code.co_name}: {result}')
    return result

def final(targetDict):
    result = []
    for record in list(targetDict.keys()):
        singleline = []
        singleline.append( record )
        
        if record == 'file':
            singleline.append(targetDict['file'])
            break
        
        for item in targetDict[record]:
            singleline.append(item)
        
        result.append(singleline)
    
    #input(f'{sys._getframe().f_code.co_name}: {result}')
    return result

def relation(basedictionary):
    # Subオプションがない時はからの値を挿入する
    if not True in ExistSub(basedictionary):
        basedictionary.insert(1, { 'Sub': { 'Name': None, 'Value': None } } )
    else:
        pass
    
    # 辞書を再構成する。
    RebuildedDictionary = RebuildListToDictionary(basedictionary)
    #input(f'mid term point, {RebuildedDictionary}')
    
    # 仕上げ
    #input(f'{sys._getframe().f_code.co_name} RebuildListToDictionary : {RebuildedDictionary}')
    return final(RebuildedDictionary)

if __name__ == '__main__':
    #basedictionary_origin = [[{'Main': {'Name': '攻撃力', 'Value': '984'}}, {'1': {'Name': '効果抵抗', 'Value': '17%'}}, {'2': {'Name': 'クリティカルダメーンジン', 'Value': '9%'}}, {'3': {'Name': '防御力', 'Value': '4%'}}, {'4': {'Name': '攻撃速度', 'Value': '10%'}}, {'file': '/home/starsand/DVM-AutoRuneEnhance/work/img/tmpfmiphdlw_summary.png'}]]

    #basedictionary = basedictionary_origin[0]
    
    #print( main(basedictionary) )
    pass