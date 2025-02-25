from flask import Flask, jsonify, g,request,redirect
import redis
import sqlite3
from .esi_client import ESIClient
import json
from datetime import datetime, timedelta
from .type import Structure,Skill
from app.character import character
from app.industrial import industrial
app = Flask(__name__)
app.config['UPDATE_PRICE_TASK_RUNNING'] = False
app.config['UPDATE_PRICE_TASK_PROGRESS'] = ""
app.config['PROFILE_TASK_RUNNING'] = False
app.config['PROFILE_TASK_PROGRESS'] = ""
app.register_blueprint(character,url_prefix="/character")
app.register_blueprint(industrial,url_prefix="/industrial")

@app.before_request
def before_request():
    g.redis_client = redis.Redis(host='redis', port=6379,decode_responses=True)
    g.esi_client = ESIClient(base_url='https://esi.evetech.net/latest/') 
    g.sqlite_client = sqlite3.connect('data/data.db')
    
@app.teardown_request
def teardown_request(exception):
    sqlite_client = getattr(g, 'sqlite_client', None)
    if sqlite_client is not None:
        sqlite_client.close()

@app.route('/')
def hello():
    return "main page!"
    
