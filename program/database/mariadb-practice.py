import sys
from pathlib import Path

import mariadb
import practical_training
import ast

PROJECT_DIR = Path('/home/starasand/DVM-AutoRuneEnhance/program/database')
MARIADB_PASSWORD_PATH = '/home/starsand/.mariadb.txt'

PRIMARY_DB_NAME    = 'dvm_auto_rune_enhance'
PRIMARY_TABLE_NAME = 'runelist'


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

    try:
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
                        digest          CHAR(96) INVISIBLE
                    )
        """)
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)

    return

if __name__ == '__main__':
    data = practical_training.main()

    initDB()
    
    for n, record in enumerate(data):
        #print("".join(record))
        digest = practical_training.GetMessageDigestByLine(literal_line = "".join(record))
        Abilities = ast.literal_eval(record[3])
        Abilities.append(['digest', digest])
        #cur.execute("INSERT INTO runelist(id, equip_pos, rune_type, rarerity) VALUES(1,?,?,?)", record[0:3])
        #conn.commit()
        #cur.execute('SELECT * FROM runelist')
        #print(cur.fetchall())
        
        data_for_inserts = []
        for Ability in Abilities:
            for i, v in enumerate(Ability):
                if i == 0: continue
                elif v == None or v == 'unknown': data_for_inserts.append(None)
                elif i == 2 and "%" in v:
                    float_data = float(1 + (int(v.replace("%","")) / 100))
                    data_for_inserts.append(float_data)
                else:
                    data_for_inserts.append(v)
        [ data_for_inserts.insert(0,v) for v in reversed(record[0:3]) ]
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
                digest
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
        cur.execute(query, data_for_inserts)
        conn.commit()
