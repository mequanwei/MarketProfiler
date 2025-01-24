
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
    
import_esi_token()