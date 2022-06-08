import sys
from pathlib import Path
from typing import KeysView

import mariadb
import practical_training
import ast, pprint,shutil,re
from TerminalColors import TerminalColors

PROJECT_DIR = Path('/home/starsand/DVM-AutoRuneEnhance/program/database')
MARIADB_PASSWORD_PATH = '/home/starsand/.mariadb.txt'

PRIMARY_DB_NAME    = 'dvm_auto_rune_enhance'
PRIMARY_TABLE_NAME = 'runelist'

fg = TerminalColors().fg
bg = TerminalColors().bg

#カラム名の入った配列を作成する。
columns = [
    "id",
    "equip_pos",
    "rune_type",
    "rarerity",
    "main_name",
    "main_value",
    "sub_name",
    "sub_value",
    "first_name",
    "first_value",
    "second_name",
    "second_value",
    "third_name",
    "third_value",
    "fourth_name",
    "fourth_value",
    "digest",
    "annotation"
]

PercentOnlies =[
    '攻撃速度',
    'クリティカル率',
    'クリティカルダメージ',
    '命中',
    '回避',
    '効果命中',
    '効果抵抗'
]

with open(MARIADB_PASSWORD_PATH, mode='r', encoding='utf-8') as fp:
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

def initDB():
    global MARIADB_DATADIR
    cur.execute('SELECT @@datadir;')
    MARIADB_DATADIR = cur.fetchall()[0][0]
    
    try:
        #shutil.rmtree(Path(MARIADB_DATADIR).joinpath(PRIMARY_DB_NAME).as_posix())
        cur.execute(f"DROP DATABASE IF EXISTS {PRIMARY_DB_NAME}")
        cur.execute(f"DROP TABLE IF EXISTS {PRIMARY_DB_NAME}.{PRIMARY_TABLE_NAME}")
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)
    
    try:
        cur.execute(f"CREATE DATABASE IF NOT EXISTS {PRIMARY_DB_NAME}")
        cur.execute(f'USE {PRIMARY_DB_NAME}')
        cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {PRIMARY_TABLE_NAME}(
                        id INT(4) PRIMARY KEY AUTO_INCREMENT,
                        equip_pos       INT(1),
                        rune_type       CHAR(4),
                        rarerity        CHAR(6),
                        main_name       CHAR(10),
                        main_value      FLOAT(8,2),
                        sub_name        CHAR(10),
                        sub_value       FLOAT(8,2),
                        first_name      CHAR(10),
                        first_value     FLOAT(8,2),
                        second_name     CHAR(10),
                        second_value    FLOAT(8,2),
                        third_name      CHAR(10),
                        third_value     FLOAT(8,2),
                        fourth_name     CHAR(10),
                        fourth_value    FLOAT(8,2),
                        digest          CHAR(96) INVISIBLE,
                        annotation      VARCHAR(255) INVISIBLE
                    )
        """)
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)

    return

def ConvertToFloat(input_num):
    return float(1 + (int(input_num.replace("%","")) / 100))

def AddAnnotation(measureArray):
    judge = int( len(measureArray) / 2 )
    if judge == 1:
        position = 'main'
    elif judge == 2:
        position = 'sub'
    else:
        position = judge - 2
    
    return '{},'.format(position)

def DynamicQuery(columns=columns):
    #? init
    keyarray = []
    valuearray = []

    #それらの配列のうち_nameと_valueのものだけをそれぞれ別に抽出する。
    for column in columns:
        try:
            judge = re.search(r'(.+(_name|_value))', column).groups()
            if re.search(r'.+_name',judge[0]):
                keyarray.append( judge[0] )
            else:
                valuearray.append( judge[0] )
        except:
            pass
    #zipでつなげてループする。
    VALUE_LIMIT_HIGH = 2
    VALUE_LIMIT_LOW = 0
    queries = []
    #print(keyarray, valuearray)
    for key, value in zip(keyarray, valuearray):
    #フォーマット文字列で値を代入する。
        #print(fg.CYAN,key,fg.END,fg.RED,value,fg.END)
        query = f"SELECT id,equip_pos,rune_type,rarerity,{key},{value} FROM {PRIMARY_TABLE_NAME} WHERE NOT({value} < {VALUE_LIMIT_HIGH} AND {value} > {VALUE_LIMIT_LOW});"
        queries.append(query)
        
    return queries
    #INTO OUTFILE '{PROJECT_DIR.as_posix()}/{key}-{value}.csv' FIELDS TERMINATED BY ',' ENCLOSED BY '';
    # クエリを実行する。
    """
    try:
        with open(f'{PROJECT_DIR.as_posix()}/{key}-{value}.csv', mode='x', encoding='utf-8') as fp:
            fp.write("")
        print('try statement ', f'{PROJECT_DIR.as_posix()}/{key}-{value}.csv', Path(f'{PROJECT_DIR.as_posix()}/{key}-{value}.csv').exists())
    except:
        pass
    """

def INSERT_MAIN(inputdata):
    for n, record in enumerate(inputdata):
        #print("".join(record))
        digest = practical_training.GetMessageDigestByLine(literal_line = "".join(record))
        Abilities = ast.literal_eval(record[3])
        Abilities.append(['digest', digest])
        #cur.execute("INSERT INTO runelist(id, equip_pos, rune_type, rarerity) VALUES(1,?,?,?)", record[0:3])
        #conn.commit()
        #cur.execute('SELECT * FROM runelist')
        #print(cur.fetchall())

        data_for_inserts = []
        annotation = ""
        append_data = None
        for Ability in Abilities:
            for i, v in enumerate(Ability):
                if i == 0: continue
                elif v == None or v == 'unknown':
                    #print(fg.MAGENTA,'if state 1',fg.END,sep="")#;input()
                    append_data = None
                elif v == '0619%':
                    print(fg.DARKCYAN,'if state 2',fg.END,sep="")#;input()
                    append_data = None
                    annotation += AddAnnotation(data_for_inserts)
                elif i == 2 and (v == "109" or v == "69"):
                    print(fg.GREEN,'if state 3 [ Individual Correspond 109 ]',fg.END,sep="",end="");print(' value',v, data_for_inserts)
                    append_data = ConvertToFloat(str(v[0:-1]))
                    annotation += AddAnnotation(data_for_inserts)
                    #print(annotation, data_for_inserts)
                elif "%" in v and i == 2:
                    #print(fg.YELLOW,'if state 4',fg.END,sep="")#;input()
                    tmp_v = v.replace("%","")
                    if ConvertToFloat(v) >= 2 and len(data_for_inserts) / 2 > 1:
                        if     ( tmp_v[-1] == "9"):
                            #print(v, tmp_v, data_for_inserts[-1],data_for_inserts)
                            #input()
                            if data_for_inserts[-1] in PercentOnlies:
                                print(fg.RED,'if state 5 [ more than 3 digit / Percent Only Type]',fg.END,sep="")#;input()
                                tmpnum = re.sub(r'(.+)9', r'\1', tmp_v)
                                append_data = ConvertToFloat(tmpnum)
                                annotation += AddAnnotation(data_for_inserts)
                            else:
                                print(bg.DARKMAGENTA,'if state 6 [ more than 3 digit / no Percent Only Type]',fg.END,'value ', v, " ", data_for_inserts, sep="")#;input()
                                append_data = None
                                annotation += AddAnnotation(data_for_inserts)
                        else:
                            print(fg.RED,'if state 10 [ more than 3 digit / last char is not 9 ]',fg.END,v,data_for_inserts, sep="")#;input()
                            append_data = None
                            annotation += AddAnnotation(data_for_inserts)
                    else:
                        #print(bg.DARKCYAN,'if state 7',fg.END,sep="")#;input()
                        append_data = ConvertToFloat(v)
                else:
                    #print(bg.DARKGREEN,'if state 8',fg.END,sep="")#;input()
                    append_data = v
                data_for_inserts.append(append_data)
        
        [ data_for_inserts.insert(0,v) for v in reversed(record[0:3]) ]
        
        if len(annotation) == 0:
            data_for_inserts.append(None)
        else:
            annotation += 'AutoCorrected'
            data_for_inserts.append(annotation)
            print(bg.YELLOW,'if state 9 [ Exist Annotation ]',fg.END, data_for_inserts,sep="",end="\n")#;input(f'{v},{data_for_inserts[10]} {type(data_for_inserts[10])} {data_for_inserts}')
        
        
        
        #data_for_inserts.insert(0, n)
        #print(data_for_inserts)
        #print(record)
        #with ThreadPoolExecutor(max_workers=10) as executor:
        query = """
            INSERT INTO runelist(
                equip_pos,
                rune_type,
                rarerity,
                main_name,
                main_value,
                sub_name,
                sub_value,
                first_name,
                first_value,
                second_name,
                second_value,
                third_name,
                third_value,
                fourth_name,
                fourth_value,
                digest,
                annotation
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
        cur.execute(query, data_for_inserts)
        conn.commit()


if __name__ == '__main__':
    data = practical_training.main()

    initDB()
    
    INSERT_MAIN(data)
    
    cur.execute(f'SELECT *,digest FROM {PRIMARY_TABLE_NAME}')
    var = cur.fetchall()
    #[ print(v) for v in var ]
    
    queries = DynamicQuery()
    tsv_filelist = []
    for query in queries:
        cur.execute(query)
        ret =  cur.fetchall()
        FileAppendix = re.search(f'([^\,]+_name),([^\,]+_value) FROM', query).groups()
        #?print(FileAppendix)
        #?print( not Path(f'{PROJECT_DIR.as_posix()}/{FileAppendix[0]}-{FileAppendix[1]}.csv').exists() )
        try:
            if not Path(f'{PROJECT_DIR.as_posix()}/{FileAppendix[0]}-{FileAppendix[1]}.tsv').exists():
                Path(f'{PROJECT_DIR.as_posix()}/{FileAppendix[0]}-{FileAppendix[1]}.tsv').touch(exist_ok=True)
            else:
                Path(f'{PROJECT_DIR.as_posix()}/{FileAppendix[0]}-{FileAppendix[1]}.tsv').unlink(missing_ok=True)
                Path(f'{PROJECT_DIR.as_posix()}/{FileAppendix[0]}-{FileAppendix[1]}.tsv').touch(exist_ok=True)
        except:
            pass
        
        for values in ret:
            #?print(values[0:5])
            #?input(values)
            with open(f'{PROJECT_DIR.as_posix()}/{FileAppendix[0]}-{FileAppendix[1]}.tsv', mode='a') as fp:
                fp.write('{}\t{}\t{}\t{}\t{}\t{}\n'.format(
                    values[0],
                    values[1],
                    values[2],
                    values[3],
                    values[4],
                    values[5],
                ))
        tsv_filelist.append(f'{PROJECT_DIR.as_posix()}/{FileAppendix[0]}-{FileAppendix[1]}.tsv')
    conn.close()
    
    print(fg.DARKCYAN,'\n SELECT id,equip_pos,rune_type,rarerity,{key},{value} FROM {PRIMARY_TABLE_NAME} WHERE NOT({value} < {VALUE_LIMIT_HIGH} AND {value} > {VALUE_LIMIT_LOW});',fg.END)
    [print(v) for v in tsv_filelist]