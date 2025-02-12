# app/views/home.py
from flask import Flask, jsonify, g,Blueprint,request
import requests
import sqlite3
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import json
import xml.etree.ElementTree as ET
from collections import defaultdict
import math
industrial = Blueprint('industrial', __name__)




@industrial.route('/get_industry_index')
def get_industry_index():
    '''
    工业系数
    '''
    result =  g.sqlite_client.cursor().execute('SELECT created_at from kv_data where key="system_index_cache"').fetchone()

    if not result:
        return None
    create_time_str = result[0]
    create_time = datetime.strptime(create_time_str, "%Y-%m-%d %H:%M:%S")
    current_time = datetime.now()
    expiration = timedelta(days=1)
    if current_time - create_time > expiration:
        # 缓存过期，更新数据
        data = g.esi_client.get_industry_index()
        
        # 将工业系数解析更新到星系表
        system = g.sqlite_client.cursor().execute('select system_id from system').fetchall()
        for item in data:
            if item['solar_system_id'] not in system:
                pass
            g.sqlite_client.cursor().execute('''Update market_price set manufacturing=?,TE=?,ME=?,copying=?,invention=?,reaction=?  where system_id=?''',
                                             (item['cost_indices'][0]['cost_index'], item['cost_indices'][1]['cost_index'],item['cost_indices'][2]['cost_index'],
                                              item['cost_indices'][3]['cost_index'],item['cost_indices'][4]['cost_index'],item['cost_indices'][5]['cost_index'],
                                              item['solar_system_id']))
        g.sqlite_client.cursor().execute('''Update kv_data set created_at=? where key="system_index_cache"''',(current_time.strftime("%Y-%m-%d %H:%M:%S"),))
        g.sqlite_client.commit()
   
    # 返回system数据
    result = g.sqlite_client.cursor().execute('''select name,TE,ME,manufacturing,copying,invention,reaction from system''').fetchall()
    return jsonify(result)

@industrial.route('/get_adjusted_price')
def get_adjusted_price():
    result =  g.sqlite_client.cursor().execute('SELECT created_at from kv_data where key="adjusted_price"').fetchone()

    if not result:
        return None
    create_time_str = result[0]
    create_time = datetime.strptime(create_time_str, "%Y-%m-%d %H:%M:%S")
    current_time = datetime.now()
    expiration = timedelta(days=1)
    if current_time - create_time > expiration:
        # 缓存过期，更新数据
        adjust_price_data = g.esi_client.get_adjusted_price()
        adjusted_price = [(float(item["adjusted_price"]),int(item["type_id"])) for item in adjust_price_data if "adjusted_price" in item]
        # 将价格更新到调整价格表
        for item in adjusted_price:
            g.sqlite_client.cursor().execute('''update adjusted_price set adjusted_price = ?  where type_id = ? ''',item)
        g.sqlite_client.cursor().execute('''Update kv_data set created_at=? where key="adjusted_price"''',(current_time.strftime("%Y-%m-%d %H:%M:%S"),))
        g.sqlite_client.commit()
   
    # 返回
    result = g.sqlite_client.cursor().execute('''select * from adjusted_price''').fetchall()
    return jsonify(result)

def calc_modifier(struct,skill=None):
    '''
    建筑修正系数
    '''
    result = g.sqlite_client.cursor().execute('select value from kv_data where key="modify_factor"').fetchone()
    if not result:
        return None
    map=json.loads(result[0])
    
    struct_base = map['structure_mod'][struct['type']]
    base_me =  struct_base['ME']
    base_te =  struct_base['TE']
    base_cost =  struct_base['cost']
    
    rig_base = map['structure_rig_mod'][struct['rig']]
    rig_base_te = rig_base['TE']
    rig_base_me = rig_base['ME']

    loc_base = map['structure_rig_loc_mod'][struct['loc']]
    
    if struct['type'] == "tatara" or struct['type'] == "athanor":
        rig_loc = loc_base['reaction']
        skill = 1 - int(skill['reactions']) * map['TE_skill_mod']['reactions']
    else:
        rig_loc = loc_base['manufactor']
        skill = (1 - int(skill['industry']) * map['TE_skill_mod']['industry']) \
                * (1 - int(skill['advanced_industry']) * map['TE_skill_mod']['advanced_industry']) \
                * (1 - int(skill['advanced_ship_construction']) * map['TE_skill_mod']['advanced_ship_construction']) \
                * (1 - int(skill['racial_starship_engineering']) * map['TE_skill_mod']['racial_starship_engineering']) \
                * (1 - int(skill['t2_science_engineering']) * map['TE_skill_mod']['t2_science_engineering']) 

    me=base_me*(1-rig_base_me*rig_loc)
    te=base_te*(1-rig_base_te*rig_loc)*skill
    cost = base_cost
    return me,te,cost

@industrial.route('/get_product_info/<int:id>')
def get_product_info(id):
    structure = {"type":"tatara","rig":"T2","loc":"null"}
    skill={"industry": 5,
        "advanced_industry" : 4,
        "advanced_ship_construction": 1,
        "racial_starship_engineering": 1,
        "t2_science_engineering": 1,
        "encryption_methods":1,
        "reactions": 5,}
    s = calc_modifier(structure,skill)
    return jsonify(s)

def get_item_name(id):
    res = g.sqlite_client.cursor().execute("select typeName from invTypes where typeID = ?",(id,)).fetchone()
    return res[0]

def get_item_type(id):
    res = g.sqlite_client.cursor().execute("SELECT invMarketGroups.marketGroupName FROM invTypes JOIN invMarketGroups ON invTypes.marketGroupID = invMarketGroups.marketGroupID WHERE invTypes.typeID = ?; ",(id,)).fetchone()
    if not res :
        return "NULL"
    return res[0]

@industrial.route('/pi/')
def get_pi_info():
    '''
    获取PI的输入
    '''
    typeid = request.args.get('typeid')  
    sql = f"select * from PlanetIndustry where typeid = {typeid}"
    result = g.sqlite_client.cursor().execute(sql).fetchall()
    s={}
    for row in result:
        if "product_name" not in s:
            s["product_name"] = get_item_name(row[0])
            s["input"] = []
        input={}
        input["name"] = get_item_name(row[1])
        input["quantity"] = row[2]
        input["category"]=get_item_type(row[1])
        s["input"].append(input)
    return jsonify(s)

 
def get_station_id():
    res = g.sqlite_client.cursor().execute('''select value from kv_data where key = "station_id"''').fetchone()
    return json.loads(res[0])

    
def fetch_price_data(location,ids):
    BASE_URL = f"http://goonmetrics.apps.gnf.lt/api/price_data/?station_id={location}&type_id={{}}"
    # 将所有id分成多个批次，每个批次最多100个id
    chunk_ids = lambda ids, chunk_size=100: [ids[i:i+chunk_size] for i in range(0, len(ids), chunk_size)]

    parse_xml = lambda response_text: {
        type_elem.get('id'): {
            # 'updated': type_elem.find('updated').text,
            'weekly_movement': float(type_elem.find('./all/weekly_movement').text),
            'buy': float(type_elem.find('./buy/max').text),
            # 'buy_vol': type_elem.find('./buy/listed').text,
            'sell': float(type_elem.find('./sell/min').text),
            # 'sell_vol': type_elem.find('./sell/listed').text
        } for type_elem in ET.fromstring(response_text).findall('.//price_data//type')
    }
    fetch_data = lambda type_ids: parse_xml(requests.get(BASE_URL.format(','.join(map(str, type_ids)))).text)
    results = {}
    with ThreadPoolExecutor(max_workers=20) as executor:
    # 分批次处理所有ID，并提交给线程池
        futures = [executor.submit(fetch_data, id_chunk) for id_chunk in chunk_ids(ids)]
    
    # 获取结果并保存
        for future in futures:
            result_data = future.result()
            results.update(result_data)
    return results


def update_price(ids=[]):
    if not ids:
        data = g.sqlite_client.cursor().execute("SELECT type_id from market_price").fetchall()
        ids = [item[0] for item in data] 
    placeholders = ', '.join(['?'] * len(ids))  # 生成与ids长度相等的占位符
    sql = f"SELECT type_id, updated_time FROM market_price WHERE type_id IN ({placeholders})"
    datas = g.sqlite_client.cursor().execute(sql,tuple(ids)).fetchall()
    expiration = timedelta(days=1)
    update_ids=[]
    for data in datas:
        create_time = datetime.strptime(data[1], "%Y-%m-%d %H:%M:%S")
        current_time = datetime.now()
        if current_time - create_time > expiration:
            update_ids.append(data[0])
    
    for loc,loc_id in get_station_id().items():
        result = fetch_price_data(loc_id,update_ids)
        if loc == "jita":
            sql = '''UPDATE market_price 
                         SET home_buy_price = ?, home_sell_price = ?, home_7d_movement = ?, home_7d_capacity = ?, 
                             updated_time = ? 
                         WHERE type_id = ?'''
        else :
            sql = '''UPDATE market_price 
                         SET jita_buy_price = ?, jita_sell_price = ?, jita_7d_movement = ?, jita_7d_capacity = ?, 
                             updated_time = ? 
                         WHERE type_id = ?'''
        insert_data=[]
        for id,r in result.items():
            insert_data.append((r["buy"],r["sell"],r["weekly_movement"],int(r["sell"]*r["weekly_movement"]),datetime.now().strftime("%Y-%m-%d %H:%M:%S"),id))
        
        g.sqlite_client.cursor().executemany(sql, insert_data)
    g.sqlite_client.commit()
    

def get_material_cost(product_id, price_type,cache=None):
    """
    递归计算某个产品的 build_cost，并返回嵌套 JSON 结构
    """
    if cache is None:
        cache = {}
    if product_id in cache:
        return cache[product_id]
    
    update_price([product_id])
    # 合并查询是否是原材料和是否存在手动价格
    result = g.sqlite_client.cursor().execute("""
        SELECT m.jita_buy_price, m.jita_sell_price, m.home_buy_price, m.home_sell_price, i.name, i.category, i.volume,
            mp.build_type, mp.price
        FROM market_price m
        JOIN item i ON m.type_id = i.type_id
        LEFT JOIN manual_price mp ON m.type_id = mp.type_id
        WHERE m.type_id = ?
    """, (product_id,)).fetchone()

    if not result:
        return {"product_id": product_id, "name":"", "build_cost": 0}  # 没有数据，返回 0
    
    jita_buy, jita_sell, home_buy, home_sell, name, category, volume,  manual_build_type, manual_price = result
    if price_type == "buy":
        market_price = min(jita_buy+900*volume,home_buy)
    else :
        market_price = min(jita_sell+900*volume,home_sell)

    # 是否使用手动价格
    if manual_build_type == "buy":
        #存在强制购买的产品
        cost = manual_price if manual_price else market_price
        cache[product_id] = {"product_id": product_id, "name": name, "build_cost": cost, "manual_build": "buy", "manual_price": manual_price}
        return cache[product_id]

    if category == 16:  # 原材料
        cost = market_price
        cache[product_id] = {"product_id": product_id, "name": name, "build_cost": cost}
        return cache[product_id]

    # 查询该产品的所有输入材料
    inputs = g.sqlite_client.cursor().execute("""
        SELECT  ipm.input_id, ipm.input_quantity,ipm.output_quantity 
        FROM industry_products_materials ipm
        WHERE ipm.product_id = ?
    """, (product_id,)).fetchall()
    
    total_cost = 0
    input_details = {}

    for input_id, input_quantity, output_quantity in inputs:
        input_data  = get_material_cost(input_id, price_type,cache)  # 递归计算输入材料的 build_cost
        total_cost += input_quantity * input_data["build_cost"]  # 按需求量累加总成本
        input_details[f"input_{input_id}"] = {
            "material_id": input_id,
            "quantity": float(input_quantity),
            "output_quantity": float(output_quantity),
            **input_data
        }
    total_cost = total_cost/output_quantity #计算单价
    build = "Build"
    if total_cost > market_price :
        total_cost = market_price # 购买还是build
        build = "Buy"
    
    cache[product_id] ={
        "product_id": product_id,
        "name": name,
        "build_cost": total_cost,
        "inputs": input_details,
        "build" : build
    }
    return cache[product_id]


def get_build_cost(product_id):
    """
    递归更新所有 `ids` 及其子 ID 的 build_cost
    """
    computed_costs = {}
    computed_costs[f"product_{product_id}"] = get_material_cost(product_id, price_type="buy")
    return computed_costs

        
def update_market_price(ids):
    update_price(ids)

@industrial.route('/updateprice/')
def update_price_api():
    ids = request.args.getlist('type_id')
    if ids:
        ids = [int(item) for item in ids]  # 确保是整数列表
    update_market_price(ids)
    return jsonify("success")
    

def get_product_tree(product_id):
    """
    递归查询产品的原材料组成，并计算总需求量。
    """
    def query_inputs(product_id):
        """
        查询该 product_id 作为 output 所需的 inputs。
        """
        query = """
        SELECT 
            ipm.product_id, ipm.output_quantity, ipm.input_id, ipm.input_quantity, 
            input_item.name, input_item.category, input_item.volume
        FROM industry_products_materials ipm
        JOIN item AS input_item ON ipm.input_id = input_item.type_id
        WHERE ipm.activity_id in (1,6)  AND ipm.product_id = ?
        """
        cursor = g.sqlite_client.cursor().execute(query, (product_id,))
        return cursor.fetchall()
    
    def build_tree(product_id):
        """
        递归构建材料树，并计算生产轮数。
        """
        inputs = query_inputs(product_id)
        if not inputs:
            return None  # 该产品没有输入材料
        
        output_quantity = inputs[0][1]  # 使用数据库中的 output_quantity
        input_data = {}
        total_materials = defaultdict(float)

        for row in inputs:
            _, out_qty, input_id, input_qty, name, category, volume = row

            # 计算所需原材料或中间产品的数量
            required_input_qty = input_qty  # 需求量
            production_rounds = math.ceil(required_input_qty / out_qty)  # 计算生产轮数

            if category == 16:  # 原材料
                input_data[name] = {"quantity": required_input_qty}
                total_materials[name] += required_input_qty
            else:  # 中间材料
                sub_tree = build_tree(input_id)
                if sub_tree:
                    input_data[name] = {
                        "quantity": required_input_qty,
                        "production_rounds": production_rounds,
                        "details": sub_tree["input"]
                    }
                    for key, value in sub_tree["total"].items():
                        total_materials[key] += value  # 累加原材料需求量

        return {
            "output_name": g.sqlite_client.cursor().execute("SELECT name FROM item WHERE type_id = ?", (product_id,)).fetchone()[0],
            "output_quantity": output_quantity,
            "input": input_data,
            "total": dict(total_materials)
        }

    return build_tree(product_id)

@industrial.route('/get_product_tree/')
def get_product_tree_api():
    name = request.args.get('name')  
    data = g.sqlite_client.cursor().execute(f"SELECT type_id FROM item WHERE name = '{name}' collate nocase").fetchone()
    if not data:
        return jsonify(None)
    # res=get_product_tree(data[0])
    res = get_build_cost(data[0])
    
    return jsonify(res)
