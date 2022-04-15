import colortheme as clr
import numpy as np
import pprint

clr.colorTheme()

def reduceOverDetectedCoordinates(masterPositionList, count, permissive, primaryIndex=1):

    class ArgumentError(Exception):
        """ArgumentError: Expected argument "count " did not receive."""
        pass
    
    if count == None:
        raise ArgumentError( 'ArgumentError: Expected argument "count " did not receive.' )
    
    try:
        print(clr.DARKYELLOW + f'{count}回目,1stcheckpoint 基準にしたいy軸の値 {masterPositionList[count][primaryIndex]}' + clr.END)
    except IndexError:
        return masterPositionList
    else:
        #input(f'count {count} times')
        nearYidx = np.where(
                        (masterPositionList < masterPositionList[count][primaryIndex] + permissive) &
                        (masterPositionList > masterPositionList[count][primaryIndex] - permissive)
                    )[0][::1]
        print(f'count: {count} / 基準にしたいy軸{masterPositionList[count][primaryIndex]}を含むインデックス\nTargetindex: {nearYidx}\nlength: {len(nearYidx)}' ) 
        #print('masterPositionList:', len(masterPositionList) )
        
        print(f'{clr.YELLOW}取得したインデックスを使用してマスター配列(posListIntermidiate)から値を取得する。{clr.END}')
        print(type(nearYidx),len(nearYidx), nearYidx)
        #input()
        
        for i, target in enumerate(nearYidx):            
            print(target, masterPositionList[target])
        #input('x, yの確認')
        
        #- nearYidx で取得したインデックスを基にmasterPositionList配列から値を取得
        coordinateByNearYidx = np.array(masterPositionList[nearYidx[0]:nearYidx[-1] + 1])
        print(f'line 40 coordinateByNearYidx:\n', coordinateByNearYidx, type(coordinateByNearYidx), len(coordinateByNearYidx))

        checkarr = coordinateByNearYidx.tolist()
        print(f'checkarr: items {len(checkarr)}, type: {type(checkarr)}')
        pprint.pprint(checkarr)
        #input()
        #- x軸の値のみ取得
        #print(type(xAxisOnlyInNearYidx))

        xAxisOnlyInNearYidx = []
        for i, item in enumerate(coordinateByNearYidx):
            xAxisOnlyInNearYidx.append(item[0])

        #input(f'line 288: \n{coordinateByNearYidx}, {xAxisOnlyInNearYidx}')
        #- x軸の値をグループ化する。
        xAxisGroupName = {}
        for i, xaxis in enumerate(xAxisOnlyInNearYidx):
            
            xaxis = int(xaxis)
            
            # x軸の値(xaxis)に一致するグループ名が有る場合は、そのグループに値を追加する。
            if xaxis in xAxisGroupName.keys():
                xAxisGroupName[xaxis].append( {"idx": nearYidx[i], "value": xaxis} )
                print(f'xaxis {clr.GREEN}PerfectMatched{clr.END}. (xaxis: {xaxis}, currentCompairGroup: {group}, permissive: {permissive})' )
            else:
                #現在の値xaxisは既存のグループの許容値に含まれるか。
                existsFlag = False
                for group in xAxisGroupName.keys():
                
                    # 既存のグループの許容値に含まれる場合はexistsフラグをTrueにする。
                    #print(xaxis, type(xaxis), int(group), permissive)
                    if 	( xaxis < int(group) + permissive ) and \
                        ( xaxis > int(group) - permissive ):
                        
                        print(f'xaxis {clr.CYAN}matched{clr.END}. (xaxis: {xaxis}, currentCompairGroup: {group}, permissive: {permissive})' )
                        xAxisGroupName[group].append( {"idx": nearYidx[i], "value": xaxis} )
                        existsFlag = True
                        break
                    else:
                        print( f'xaxis {clr.DARKRED}notmatched{clr.END}. (xaxis: {xaxis}, currentCompairGroup: {group} permissive: {permissive})' )
                        existsFlag = False
            
                # existsFlag を 確認して処理をおこなう。
                if existsFlag == False:
                    
                    xAxisGroupName[xaxis] = []
                    xAxisGroupName[xaxis].append( {"idx": nearYidx[i], "value": xaxis} )
                    print(f'{clr.YELLOW}new group create{clr.END}, (xaxis: {xaxis}) appended value {xAxisGroupName[xaxis]}')
            #print(f'{xAxisGroupName}, {i}, {xaxis}')
            #print(xAxisOnlyInNearYidx)
            #input('tier0')
        #input('tier1')
        
        #- 各グループから、１つだけインデックスと値を残して、それ以外を削除したいx,yのインデックスとして idx_nearY_and_nearX配列に格納する。
        idx_nearY_and_nearX = []
        for group in xAxisGroupName:
            #input(f'groupname {group}, {type(group)}')
            
            for i, item in enumerate(xAxisGroupName[group]):
                #print( item['idx'], type(item['idx']) )
                if i == 0:
                    print(f'{clr.YELLOW}index {item["idx"]} passed.{clr.END} {clr.DARKMAGENTA}ValueInMasterArray: {masterPositionList[item["idx"]]}{clr.END}')
                    continue
                else:
                    print(f"index appended. {item['idx']} ValueInMasterArray: {masterPositionList[item['idx']]}")
                    idx_nearY_and_nearX.append(item['idx'])
                    
            pprint.pprint(xAxisGroupName[group])
            #input('line 340')
            
        print(idx_nearY_and_nearX, type(idx_nearY_and_nearX))
        idx_nearY_and_nearX.sort()
        idx_nearY_and_nearX.reverse()
        #input(f'削除したいインデックスの値 {idx_nearY_and_nearX}')
        print(f'削除したいインデックスの値 {idx_nearY_and_nearX}')

        for idx in idx_nearY_and_nearX:
            print(f'index:{idx} remove value: {masterPositionList[idx]}')
            
            del masterPositionList[idx]
            
        masterPositionListForRecursive = masterPositionList
        
        if False == True:
            for i, v in enumerate(masterPositionList):
                print(f'confirm masterPositionList\n', i,v)
        
        
        print('masterPositionList(element removed):', masterPositionList, type(masterPositionList),end="\n")
        #input()
        count += 1
        reduceOverDetectedCoordinates(masterPositionList=masterPositionListForRecursive, count=count, permissive=permissive)
    finally:
        return masterPositionList