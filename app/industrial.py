# app/views/home.py
from flask import Flask, jsonify, g,Blueprint,request,copy_current_request_context,current_app
import requests
import sqlite3
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import json
import xml.etree.ElementTree as ET
from collections import defaultdict
import math
import threading
from functools import partial
from typing import List, Tuple, Optional,Dict, Any


industrial = Blueprint('industrial', __name__)

def update_industry_index():
    '''
    工业系数
    '''
    # 缓存过期，更新数据
    data = g.esi_client.get_industry_index()
    
    # 将工业系数解析更新到星系表
    system = g.sqlite_client.cursor().execute('select system_id from system').fetchall()
    for item in data:
        if item['solar_system_id'] not in system:
            pass
        g.sqlite_client.cursor().execute('''Update system set manufacturing=?,TE=?,ME=?,copying=?,invention=?,reaction=?  where system_id=?''',
                                            (item['cost_indices'][0]['cost_index'], item['cost_indices'][1]['cost_index'],item['cost_indices'][2]['cost_index'],
                                            item['cost_indices'][3]['cost_index'],item['cost_indices'][4]['cost_index'],item['cost_indices'][5]['cost_index'],
                                            item['solar_system_id']))
    g.sqlite_client.commit()
   
def get_industry_index(system_name):
    sql = f"select name,TE,ME,manufacturing,copying,invention,reaction from system where name = '{system_name}'"
    result = g.sqlite_client.cursor().execute(sql).fetchone()
    return result

@industrial.route('/get_industry_index')
def  get_industry_index_api():
    system = request.args.get('system') 
    return jsonify(get_industry_index(system))

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

def get_modifier_info():
    structure = {"type":"tatara","rig":"T2","loc":"null"}
    skill={"industry": 5,
        "advanced_industry" : 4,
        "advanced_ship_construction": 1,
        "racial_starship_engineering": 1,
        "t2_science_engineering": 1,
        "encryption_methods":1,
        "reactions": 5,}
    return  calc_modifier(structure,skill)

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

     
def fetch_price_data(location,ids):    
    BASE_URL = f"http://goonmetrics.apps.gnf.lt/api/price_data/?station_id={location}&type_id={{}}"
    # 将所有id分成多个批次，每个批次最多100个id
    chunk_ids = lambda ids, chunk_size=100: [ids[i:i+chunk_size] for i in range(0, len(ids), chunk_size)]

    parse_xml = lambda response_text: {
        type_elem.get('id'): {
            # 'updated': type_elem.find('updated').text,
            'weekly_movement': int(float(type_elem.find('./all/weekly_movement').text)),
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


def update_market_price(ids=[]):
    sqlite_client = sqlite3.connect('data/data.db')
    cursor = sqlite_client.cursor()
    if not ids:
        data = cursor.execute("SELECT type_id from items").fetchall()
        ids = [item[0] for item in data] 
    
    station_json = cursor.execute('''select value from kv_data where key = "station_id"''').fetchone()[0]

    for loc,loc_id in json.loads(station_json).items():
        result = fetch_price_data(loc_id,ids)
        if loc == "home":
            sql = '''UPDATE items 
                         SET home_buy_price = ?, home_sell_price = ?, home_7d_movement = ?, home_7d_capacity = ?,updated_time = ?
                         WHERE type_id = ?'''
        else :
            sql = '''UPDATE items 
                         SET jita_buy_price = ?, jita_sell_price = ?, jita_7d_movement = ?, jita_7d_capacity = ?,updated_time = ?
                         WHERE type_id = ?'''
        insert_data=[]
        for id,r in result.items():
            insert_data.append((r["buy"],r["sell"],r["weekly_movement"],int(r["sell"]*r["weekly_movement"]),datetime.now().strftime("%Y-%m-%d %H:%M:%S"),id))
        cursor.executemany(sql, insert_data)
    sqlite_client.commit()

def update_adjust_price():
    adjust_price_data = g.esi_client.get_adjusted_price()
    adjusted_price = [(float(item["adjusted_price"]),int(item["type_id"])) for item in adjust_price_data if "adjusted_price" in item]
    # 将价格更新到调整价格表
    for item in adjusted_price:
        g.sqlite_client.cursor().execute('''update items set adjusted_price = ?  where type_id = ? ''',item)
    g.sqlite_client.commit()

@industrial.route('/update_all_network_data/')
def update_all_network_data():
    update_industry_index()
    update_adjust_price()
    thread = threading.Thread(target=update_market_price, daemon=True)
    thread.start()
    return jsonify("updated")


def preload_data() -> None:
    """
    Preload items and industry_products_materials into memory.
    """
    # Global in-memory caches
    item_cache: Dict[int, Dict[str, float]] = {}
    materials_cache: Dict[int, List[Tuple[int, float, float, int]]] = {}
    manual_price_cache: Dict[int, Tuple[str, float]] = {}
    time_cache: Dict[int, float] = {}
    cursor = g.sqlite_client.cursor()

    # Preload items (combined_items)
    items = cursor.execute("""
        SELECT type_id, jita_buy_price, jita_sell_price, home_buy_price, home_sell_price,
               name, category, volume, adjusted_price
        FROM items
    """).fetchall()
    for row in items:
        item_cache[row[0]] = {
            "jita_buy_price": row[1],
            "jita_sell_price": row[2],
            "home_buy_price": row[3],
            "home_sell_price": row[4],
            "name": row[5],
            "category": row[6],
            "volume": row[7],
            "adjusted_price": row[8] or 0.0  # Default to 0 if None
        }

    # Preload industry_products_materials
    materials = cursor.execute("""
        SELECT product_id, input_id, input_quantity, output_quantity, activity_id
        FROM industry_products_materials where activity_id in (1,6)
    """).fetchall()
    for product_id, input_id, input_quantity, output_quantity, activity_id in materials:
        if product_id not in materials_cache:
            materials_cache[product_id] = []
        materials_cache[product_id].append((input_id, input_quantity, output_quantity, activity_id))
    
    # Preload manual_price
    manual_prices = cursor.execute("""
        SELECT type_id, build_type, price
        FROM manual_price
    """).fetchall()
    manual_price_cache.update((row[0], (row[1], row[2] or 0.0)) for row in manual_prices)

    # Preload industry_activity_time
    times = cursor.execute("""
        SELECT product_id, time
        FROM industry_activity_time
    """).fetchall()
    time_cache.update((row[0], row[1] or 0.0) for row in times)


    return item_cache,materials_cache,manual_price_cache,time_cache

def get_install_cost(
    ids: List[Tuple[int, float, float, int]],
    cost_index: float,
    cost_modifier: float,
    item_cache = None,
    db=None  # Kept for compatibility, but unused with preloading
) -> float:
    """
    Calculate installation cost using preloaded item_cache.

    Args:
        ids: List of (input_id, input_quantity, output_quantity, activity_id).
        cost_index: Cost index factor.
        cost_modifier: Base cost adjustment factor.
        db: Ignored if preloading is used.

    Returns:
        Total installation cost.
    """
    if not ids:
        return 0.0
    if  not item_cache:
        item_cache = {}

    job_base_price = 0.0
    missing_ids = []
    for input_id, input_quantity, _, _ in ids:
        item = item_cache.get(input_id)
        if item:
            adjusted_price = item["adjusted_price"]
        else:
            adjusted_price = 0.0
            if input_id not in missing_ids:
                missing_ids.append(input_id)
        job_base_price += input_quantity * adjusted_price

    if missing_ids:
        print(f"Warning: No adjusted_price found for input_ids: {missing_ids}")

    scc_tax = 0.04
    crop_tax = 0.01
    install_price = job_base_price * (cost_index * cost_modifier + scc_tax + crop_tax)
    return install_price


def get_material_cost(
    product_id: int,
    modifier: Tuple[float, float, float, float, float],
    price_type: str,
    db=None,
    db_cache = None,
    cache: Optional[Dict[int, Dict[str, Any]]] = None
) -> Dict[str, Any]:
    if cache is None:
        cache = {}
    if product_id in cache:
        return cache[product_id]
    if db is None:
        db = g.sqlite_client  # Only needed for time query if not preloaded
    if db_cache is None:
        raise ValueError("db cache is None")
    item_cache,materials_cache,manual_price_cache,time_cache = db_cache
    # Fetch from item_cache
    item = item_cache.get(product_id)
    if not item:
        print(f"No type {product_id}")
        return {"product_id": product_id, "name": "", "build_cost": 0}

    jita_buy = item["jita_buy_price"]
    jita_sell = item["jita_sell_price"]
    home_buy = item["home_buy_price"]
    home_sell = item["home_sell_price"]
    name = item["name"]
    category = item["category"]
    volume = item["volume"]

    # Manual price logic (assuming manual_price isn’t in items yet)
    manual_price_data = manual_price_cache.get(product_id)
    manual_build_type = manual_price_data[0] if manual_price_data else ""
    manual_price = manual_price_data[1] or 0 if manual_price_data else 0

    # Market price calculation
    def get_market_price(buy_price: float, sell_price: float) -> Tuple[float, str]:
        price = buy_price if price_type == "buy" else sell_price
        jita_price = price + 900 * volume
        home_price = home_buy if price_type == "buy" else home_sell
        if home_price == 0:
            return (jita_price, "jita")
        return (min(jita_price, home_price), "jita" if jita_price < home_price else "home")

    market_price, market_price_loc = get_market_price(jita_buy, jita_sell)

    # Case 1: Manual buy
    if manual_build_type == "buy":
        cost = manual_price if manual_price else market_price
        cache[product_id] = {
            "product_id": product_id, "name": name, "build_cost": cost, "material_cost": cost,
            "manual_build": "buy", "manual_price": manual_price, "buy_loc": market_price_loc
        }
        return cache[product_id]

    # Case 2: Raw material
    if category == 16:
        cost = market_price
        cache[product_id] = {
            "product_id": product_id, "name": name, "build_cost": cost, "material_cost": cost,
            "buy_loc": market_price_loc
        }
        return cache[product_id]

    # Case 3: Recursive calculation
    inputs = materials_cache.get(product_id, [])
    if not inputs:
        cache[product_id] = {
            "product_id": product_id, "name": name, "build_cost": market_price,
            "material_cost": 0, "install_cost": 0, "buy_loc": market_price_loc
        }
        return cache[product_id]

    material_cost = 0
    input_details = []
    me, te, cost, cost_manufacturing, cost_reaction = modifier

    for input_id, input_quantity, output_quantity, activity_id in inputs:
        input_data = get_material_cost(input_id, modifier, price_type, db_cache=db_cache, cache=cache)
        input_quantity_mod = math.ceil(input_quantity * me * 0.9)
        material_cost += input_quantity_mod * input_data["build_cost"]
        input_details.append({
             "require_quantity": float(input_quantity_mod),
             **input_data
        })
    
    cost_index = cost_manufacturing if inputs[0][3] == 1 else cost_reaction
    install_cost = get_install_cost(inputs, cost_index, cost, item_cache, db) / inputs[0][2]
    material_cost /= inputs[0][2]
    total_cost = material_cost + install_cost

    build_type = "Build"
    buy_loc = ""
    if total_cost > market_price:
        total_cost = market_price
        build_type = "Buy"
        buy_loc = market_price_loc


    time_data = time_cache.get(product_id)
    time = time_data * te if time_data else 0

    cache[product_id] = {
        "product_id": product_id, "name": name, "build_cost": total_cost,
        "material_cost": material_cost, "install_cost": install_cost, "time": time,
        "inputs": input_details, "build": build_type, "buy_loc": buy_loc,"output_quantity": float(output_quantity)
    }
    return cache[product_id]

def get_product_tree(product_id):
    """
    递归更新所有 `ids` 及其子 ID 的 build_cost
    """
    item_cache,materials_cache,manual_price_cache,time_cache = preload_data()
    db_cache =(item_cache,materials_cache,manual_price_cache,time_cache) 
    
    computed_costs = {}
    me,te,cost = get_modifier_info()
    cost_index = get_industry_index(system_name = "CKX-RW")
    cost_manufacturing = cost_index[3]
    cost_reaction = cost_index[6]
    computed_costs[f"product_{product_id}"] = get_material_cost(product_id, (me,te,cost,cost_manufacturing,cost_reaction), price_type="sell",db_cache = db_cache)
    return computed_costs

@industrial.route('/get_product_tree/')
def get_product_tree_api():
    name = request.args.get('name')  
    data = g.sqlite_client.cursor().execute(f"SELECT type_id FROM items WHERE name = '{name}' collate nocase").fetchone()
    if not data:
        return jsonify(None)
    res = get_product_tree(data[0])
    
    return jsonify(res)

def update_build_cost(params):
    item_cache,materials_cache,manual_price_cache,time_cache = preload_data()
    db_cache =(item_cache,materials_cache,manual_price_cache,time_cache) 
    cursor = g.sqlite_client.cursor()
    items = cursor.execute('''select type_id from items''').fetchall()

    id = [item[0] for item in items]
    result = []
    cache = {}
    for i in id:
        build_cost =  get_material_cost(i, params, price_type="sell",db_cache = db_cache,cache = cache)["build_cost"]
        result.append((build_cost,i))
    cursor.executemany("UPDATE items SET build_cost = ? WHERE type_id = ?",result)
    g.sqlite_client.commit()
        
@industrial.route('/updatebuildcost/')
def update_build_cost_api():
    me,te,cost = get_modifier_info()
    cost_index = get_industry_index(system_name = "CKX-RW")
    cost_manufacturing = cost_index[3]
    cost_reaction = cost_index[6]
    params = (me,te,cost,cost_manufacturing,cost_reaction)
    update_build_cost(params)
    return jsonify("success")

    
@industrial.route('/marketprofile/')
def market_profile_api():
    items = g.sqlite_client.cursor().execute('''select * from items''').fetchall()
    result = []
    for item in items:
        try:
            type_id,name,category,_, build_cost,_,home_buy_price,home_sell_price,home_7d_movement,home_7d_capacity,jita_buy_price,jita_sell_price,jita_7d_movement,jita_7d_capacity,_  = item 
            if home_7d_capacity < 100000000 :
                continue
            margin_p = (home_sell_price - build_cost) / build_cost
            if margin_p > 0:
                result.append({"margin_p":margin_p,"details":item})
        except:
            pass
    
    # 按照内层字典中'count'键的值进行排序
    result.sort(key=lambda x: x["margin_p"],reverse=True)
    result_new=[]
    for i in result:
        margin_p = i["margin_p"]
        type_id,name,category,_, build_cost,_,home_buy_price,home_sell_price,home_7d_movement,home_7d_capacity,jita_buy_price,jita_sell_price,jita_7d_movement,jita_7d_capacity,_  = i["details"]
        d = {}
        d["typeID"] = type_id
        d["name"] = name
        d["build_cost"] = build_cost
        d["home_buy_price"] = home_buy_price
        d["home_sell_price"] = home_sell_price
        d["home_7d_movement"] = home_7d_movement
        d["home_7d_capacity"] = home_7d_capacity
        d["jita_buy_price"] = jita_buy_price
        d["jita_sell_price"] = jita_sell_price
        d["jita_7d_movement"] = jita_7d_movement
        d["jita_7d_capacity"] = jita_7d_capacity
        d["margin_p"] = margin_p
        result_new.append(d) 
    return jsonify(result_new)
    
    


        