
import os
import sys

sys.path.append("/home/zhuquanwei/dev/MarketProfiler")
from  app.esi_client import ESIClient
client = ESIClient(
    base_url='https://esi.evetech.net/latest/'
)

try:    
    
    print("Items:", client.get_system())

finally:
    client.close()
