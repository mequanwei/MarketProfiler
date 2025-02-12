
import os
import sys
import json
import sqlite3
from datetime import datetime

sys.path.append("/app")

db_conn = sqlite3.connect('data/data.db')
cursor = db_conn.cursor()



def import_system_id():
    value=[]
    with open("./data/static_system_id","r") as f:
        for line in f:
            l = line.strip().split(",")
            id = int(l[0])
            name = l[1]
            value.append((id,name))

    cursor.executemany('''INSERT OR IGNORE INTO system (system_id, name) VALUES (?, ?)''', value)
    db_conn.commit()


def import_modify_factor():
    map = {
    "structure_mod": {
        "raitaru": {"cost": 0.97, "ME": 0.99, "TE": 0.85},
        "azabel": {"cost": 0.96, "ME": 0.99, "TE": 0.80},
        "sotiyo": {"cost": 0.95, "ME": 0.99, "TE": 0.7},
        "athanor": {"cost": 1, "ME": 1, "TE": 1},
        "tatara": {"cost": 1, "ME": 1, "TE": 0.75}, 
    },
    "structure_rig_mod": {
        "T1": {"TE": 0.2, "ME": 0.02},
        "T2": {"TE": 0.24, "ME": 0.024},
    },
    "structure_rig_loc_mod": {
        "high": {"manufactor":1},
        "low": {"manufactor":1.9, "reaction": 1},
        "null": {"manufactor":1.1, "reaction": 1.1},
    },
    "TE_skill_mod": {
        "industry": 0.04,
        "advanced_industry" : 0.03,
        "advanced_ship_construction": 0.01,
        "racial_starship_engineering": 0.01,
        "t2_science_engineering": 0.01,
        "encryption_methods":0,
        "reactions": 0.04,
    },
    }
    cursor.execute('''delete from kv_data where key="modify_factor"''')
    cursor.execute('''INSERT OR IGNORE INTO kv_data values (?,?,?)''',("modify_factor",json.dumps(map), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    db_conn.commit()

def import_esi_token():
    map = {
    "client_id" :"acdd73ce088d436ba3edf469e099ecae",
    "client_secret":"alOhr3hpwWhb7Pu4P3YSvps4Vaxc7E9Vk4VKzGG3"
    }
    cursor.execute('''INSERT OR IGNORE INTO kv_data values (?,?,?)''',("esi",json.dumps(map), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    db_conn.commit()
    
# import_esi_token()
def import_pi_data():
    sql = f"SELECT r_out.typeID AS outputTypeID, r_in.typeID AS inputTypeID, r_in.quantity AS inputQuantity FROM planetSchematicsTypeMap r_out JOIN planetSchematicsTypeMap r_in ON r_out.schematicID = r_in.schematicID WHERE r_out.isInput = FALSE  AND r_in.isInput = TRUE ORDER BY r_out.typeID, r_in.typeID;"
    result = cursor.execute(sql).fetchall()

    insert_sql = f"INSERT INTO PlanetIndustry (typeid, inputid, quantity) VALUES (?,?,?)"
    for row in result:
        cursor.execute(insert_sql, row)
    db_conn.commit()
    cursor.close()
    db_conn.close()
   
# import_pi_data()
    

def build_parent_map(id_parent_pairs):
    # 1. 构建 {id: parent_id} 字典
    parent_dict = {child: parent for child, parent in id_parent_pairs}

    # 2. 递归查找所有父级
    def find_parents(item_id):
        path = []
        while item_id is not None:
            path.append(item_id)  # 添加当前 id
            item_id = parent_dict.get(item_id)  # 获取父 id
        return path  # 结束时返回完整路径
    
    # 3. 构建 {id: [自己 → 顶层父 id]} 的字典
    hierarchy_map = {item: find_parents(item) for item in parent_dict}
    return hierarchy_map

def  import_type_info():
    # 构建包含每个id的所有父id的字典
    sql = f"select marketGroupID,parentGroupID from  invMarketGroups"
    data = cursor.execute(sql).fetchall()
    all_parents_dict = build_parent_map(data)

    sql = f"select typeID,typeName,marketGroupID from invTypes where published = True and marketGroupID is not NULL" 
    data = cursor.execute(sql).fetchall()
    no_need_type=[2,19,24,150,1320,1396,1659,1922,1954,3628]
    
    # 弹药(11)：弹药 脚本
    # 无人机(157)：无人机和铁骑舰载机
    # T1小船：护卫舰(1361)、驱逐舰(1372)和穿梭机(391)
    # T1中船：巡洋舰(1367)、战列巡洋舰(1374)、运载舰(8)和采矿驳船(494)
    # T1大船：战列舰(1376)、货舰(766)和工业指挥舰(2335)
    # T2小船：二级科技护卫舰(1364)、二级和三级科技驱逐舰(1373)
    # T2中船：二级科技巡洋舰(1368)、二级科技战列巡洋舰(1375)、二级科技运载舰(1385)、三级科技巡洋舰(1375)、三级科技子系统(1112)和采掘者(874)
    # T2大船：二级科技战列舰(1377)和战略货舰(1089)
    # 组件：高级组件(65)、高级旗舰组件(1883)、和三级科技组件(1147)、保护性组件(2768)、R.A.M(1908)
    # 旗舰组件：旗舰组件(781)
    # 建筑：建筑组件(1865)、建筑装备(2202)、建筑改装件(2203)、昇威建筑(477 -404)、母星建筑和燃料块(1870)
    # 装备：装备装备(9)、船插(1111)、可部署装备(404)、脑插(27)、货柜
    # 小旗舰：T1无畏(761),FAX(2271),小航,T2无畏(3510),旗舰级工业舰(1047)
    # 超旗：大航、titan(812)
    # ----
    # 中间产物:中间反应产物(1034)、复合反应产物(499,500)，生化反应产物(1858，1860)，分子反应材料(2767)
    # 原材料:研究装备(1872)、材料(533)
    type_dict={
        1:[11],
        2:[157],
        3:[1361,1372,391],
        4:[1367,1374,8,494],
        5:[1376,766,2335],
        6:[1364,1373],
        7:[1368,1375,1385,1375,1112,874],
        8:[1377,1089,3510],
        9:[65,1883,1147,2768,1908],
        10:[781],
        11:[1865,2202,2203,477,1870],
        12:[9,111,404,27],
        13:[761,2271,3510,1047],
        14:[812,817],
        15:[1034,499,500,1858,1860,2767],
        16:[1872,533]
    }
    result={}
    leaked=[]
    type_value_to_key = {}
    for key, value_list in type_dict.items():
        for v in value_list:
            type_value_to_key[v] = key
    
    for item in data:
        parents = all_parents_dict[item[2]]
        if parents[-1] in no_need_type:
            continue
        for t in parents:
            category = type_value_to_key.get(t)
            if category:
                result[item[0]] = (item[1],category)
                if item[0] in [23757,23911,23915,24483,42132]:
                    #carriers
                    result[item[0]] = (item[1],13)
                break
        else:
            if (parents[-1] == 955):
                #abyl
                continue
            if 1612 in parents:
                #special edition ship
                continue
            leaked.append((item[1],parents[-1]))
    #debug
    # with open("r0.json","w") as f,open("r1.json","w") as f1:
    #     f.write(json.dumps(result))
    #     f1.write(json.dumps(leaked))
    insert_values=[]
    
    data = cursor.execute("SELECT d1.typeID, COALESCE(d2.volume , d1.volume) AS final_vol FROM invTypes d1 LEFT JOIN invVolumes d2 ON d1.typeID = d2.typeID;").fetchall()
    vol_map={row[0]:row[1] for row in data}
    for id,v in result.items():
        insert_values.append((id,v[0],v[1],vol_map[id],))
    cursor.executemany('''INSERT INTO item (type_id, name, category, volume) VALUES (?, ?, ?, ?) ''', insert_values)
    db_conn.commit()
    

# import_type_info()
results = []
# 解析XML数据
def parse_xml(response_text):
    result_data = {}
    import xml.etree.ElementTree as ET
    root = ET.fromstring(response_text)
    
    # 解析 <price_data> 节点中的每个 <type> 节点
    for type_elem in root.findall('.//price_data//type'):
        type_id = type_elem.get('id')
        updated = type_elem.find('updated').text
        weekly_movement = type_elem.find('./all/weekly_movement').text
        buy_max = type_elem.find('./buy/max').text
        buy_listed = type_elem.find('./buy/listed').text
        sell_min = type_elem.find('./sell/min').text
        sell_listed = type_elem.find('./sell/listed').text
        
        # 存储数据
        result_data[type_id] = {
            'updated': updated,
            'weekly_movement': weekly_movement,
            'buy_max': buy_max,
            'buy_listed': buy_listed,
            'sell_min': sell_min,
            'sell_listed': sell_listed
        }
    
    return result_data
# 发送请求的线程函数
def fetch_data(type_ids):
    import requests
    type_ids_str = ','.join(map(str, type_ids))  # 转换为字符串，以便传递
    # 请求URL模板
    BASE_URL = "http://goonmetrics.apps.gnf.lt/api/price_data/?station_id=60003760&type_id={}"
    url = BASE_URL.format(type_ids_str)
    
    try:
        # 发送请求
        response = requests.get(url)
        if response.status_code == 200:
            parsed_data = parse_xml(response.text)
            results.append(parsed_data)
            print(f"Successfully fetched data for types {type_ids}")
        else:
            print(f"Failed to fetch data for types {type_ids}")
    except Exception as e:
        print(f"Error fetching data for types {type_ids}: {e}")

# 将所有id分成多个批次，每个批次最多100个id
def chunk_ids(ids, chunk_size=100):
    for i in range(0, len(ids), chunk_size):
        yield ids[i:i+chunk_size]

def import_vol_data():
    
    threads = []
    data = cursor.execute("SELECT type_id from market_price").fetchall()
    ids = [item[0] for item in data] 
    
    # 分批次处理所有ID
    for id_chunk in chunk_ids(ids):
        import threading
        thread = threading.Thread(target=fetch_data, args=(id_chunk,))
        threads.append(thread)
        thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()

    # 打印所有结果
    print("All fetched data:", results)

    
# import_vol_data()


   

def home_location():
    d = {
        "jita":60003760,
        "home":1046664001931
    }
    cursor.execute('''INSERT OR IGNORE INTO kv_data values (?,?,?)''',("station_id",json.dumps(d), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    db_conn.commit()
    cursor.close()
    db_conn.close()
    
# home_location()

