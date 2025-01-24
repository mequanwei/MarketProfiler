
import os
import sys
import json
import sqlite3

sys.path.append("/app")
from  app.esi_client import ESIClient
db_conn = sqlite3.connect('data/data.db')
cursor = db_conn.cursor()




cache_data =  r.get("industry_index_cache")
if cache_data:
    pass
else:
    cache_data = esi_client.get_industry_index()
    r.setex("industry_index_cache", 3600, json.dumps(cache_data))

print(json.loads(cache_data)[0])
system={}
for item in json.loads(cache_data):
    id = item['solar_system_id']
    mapping = {'manufacturing': item['cost_indices'][0]['cost_index'],
               'TE': item['cost_indices'][1]['cost_index'],
               'ME': item['cost_indices'][2]['cost_index'],
                'copying': item['cost_indices'][3]['cost_index'],
                'invention': item['cost_indices'][4]['cost_index'],
                'reaction': item['cost_indices'][5]['cost_index']}
    system[id] = mapping



with open("./data/static_system_id","r") as f:
    for line in f:
        l = line.strip().split(",")
        id = int(l[0])
        name = l[1]
        mapping = system[id]
        mapping['id'] = id
        r.hset(f"system:{name}", mapping=mapping)



    
