# app/views/home.py
from flask import Flask, jsonify, g,Blueprint
import sqlite3
from datetime import datetime, timedelta
import json

industrial = Blueprint('industrial', __name__)



@industrial.route('/get_industry_index')
def get_industry_index():
    result =  g.sqlite_client.cursor().execute('SELECT created_at from kv_data where key="system_index_cache"').fetchone()

    if not result:
        return None
    create_time_str = result
    create_time = datetime.strptime(create_time_str, "%Y-%m-%d %H:%M:%S")
    current_time = datetime.now()
    expiration = timedelta(seconds=1)
    if current_time - create_time > expiration:
        # 缓存过期，更新数据
        data = g.esi_client.get_industry_index()
        g.sqlite_client.cursor().execute('''Update kv_data set value=?,created_at=? where key="system_index_cache"''',(json.dumps(data),current_time.strftime("%Y-%m-%d %H:%M:%S")))
        g.sqlite_client.commit()
        
        # 将缓存解析更新到星系表
        system = g.sqlite_client.cursor().execute('select system_id from system').fetchall()
        for item in data:
            if item['solar_system_id'] not in system:
                pass
            g.sqlite_client.cursor().execute('''Update system set manufacturing=?,TE=?,ME=?,copying=?,invention=?,reaction=?  where system_id=?''',
                                             (item['cost_indices'][0]['cost_index'], item['cost_indices'][1]['cost_index'],item['cost_indices'][2]['cost_index'],
                                              item['cost_indices'][3]['cost_index'],item['cost_indices'][4]['cost_index'],item['cost_indices'][5]['cost_index'],
                                              item['solar_system_id']))
        g.sqlite_client.commit()
   
    # 返回system数据
    result = g.sqlite_client.cursor().execute('''select name,TE,ME,manufacturing,copying,invention,reaction from system''').fetchall()
    return jsonify(result)

def calc_modifier(struct,skill=None):
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

