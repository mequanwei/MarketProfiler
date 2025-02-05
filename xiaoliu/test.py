# # #a=1+2+3+4+5+6+7+8+9+10
# # # print(a)


# # a=0
# # for i in range(10):
# #     a+=i
# # # print(i)


# # b=[1,2,3,4,5,6,234,345,2,3,23,42,34]

# # b[0]
# # b[5]
# # print(b[len(b)-1])
# # print(b[-1])

# # print(len(b))
# # for i in b:
# #     #print(i)


# a={'age':23,'gender':'male',"name":"zhquanwei"}

# tttt={}
# tttt['name']=1




# print(tttt)
# # print(a['name'])
# # {chr(i): i - 96 for i in range(97, 123)}



# for i in range(97,123):
#     key = chr(i)
#     value = i-96
#     tttt[key]=value
# print(tttt)

# tttt['name'] = "xiaoliu"
# print(tttt)





# table = {"sheet1": {"name":"OSD","num":12},
#          "sheet2": {"ID":"SS"} 
#         }

import csv


# import csv

# def load_data(file_path):
#     data = []
#     with open(file_path, mode='r', encoding='utf-8') as file:
#         reader = csv.DictReader(file)
#         for row in reader:
#             # 假设所有的值都被正确地读为字符串形式，如果有需要可以在这里进行类型转换
#             row['marketGroupID'] = int(row['marketGroupID'])
#             row['parentGroupID'] = int(row['parentGroupID']) if row['parentGroupID'] else None  # 如果为空则设置为None
#             row['hasTypes'] = bool(int(row['hasTypes']))
#             data.append(row)
#     return data

# def build_hierarchy(data, parent_id=None):
#     hierarchy = {}
#     for item in data:
#         if item['parentGroupID'] == parent_id:
#             # 记录marketGroupID
#             node_info = {'marketGroupID': item['marketGroupID']}
#             if not item['hasTypes']:
#                 # 如果不是物品，则递归构建子类别
#                 children = build_hierarchy(data, item['marketGroupID'])
#                 if children:  # 如果有子类别，则添加
#                     node_info['children'] = children
#             hierarchy[item['marketGroupName']] = node_info
#     return hierarchy

# def find_path_by_market_group_id(hierarchy, market_group_id, path=None):
#     if path is None:
#         path = []
#     for name, info in hierarchy.items():
#         new_path = path + [name]
#         if info['marketGroupID'] == market_group_id:
#             return new_path
#         elif 'children' in info:
#             found_path = find_path_by_market_group_id(info['children'], market_group_id, new_path)
#             if found_path:
#                 return found_path
#     return None


# file_path = 'C:\\Users\\quanwei.zhu\\Downloads\\invMarketGroups_export_2025-01-31_100017.csv'
# data = load_data(file_path)
# hierarchy = build_hierarchy(data)

# import json
# with open('market','w') as f:
#     f.write(json.dumps(hierarchy))