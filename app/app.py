from flask import Flask, jsonify, g,request,redirect
import redis
import sqlite3
from .esi_client import ESIClient
import time
import os
import json
from datetime import datetime, timedelta
from .type import Structure,Skill
from .sso_client import redirect_to_sso,request_token

app = Flask(__name__)

settings={}

@app.before_request
def before_request():
    g.redis_client = redis.Redis(host='redis', port=6379,decode_responses=True)
    g.esi_client = ESIClient(base_url='https://esi.evetech.net/latest/')    
    g.sqlite_client = sqlite3.connect('data/data.db')
    

@app.route('/')
def hello():
    return "main page!"
    
    
@app.route('/get_industry_index')
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

@app.route('/get_product_info/<int:id>')
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


def login():
    """ this redirects the user to the EVE SSO login """
    token = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    settings['token'] = token
    s =redirect_to_sso(["publicData","esi-calendar.respond_calendar_events.v1","esi-calendar.read_calendar_events.v1","esi-location.read_location.v1","esi-location.read_ship_type.v1","esi-mail.organize_mail.v1","esi-mail.read_mail.v1","esi-mail.send_mail.v1","esi-skills.read_skills.v1","esi-skills.read_skillqueue.v1","esi-wallet.read_character_wallet.v1","esi-wallet.read_corporation_wallet.v1","esi-search.search_structures.v1","esi-clones.read_clones.v1","esi-characters.read_contacts.v1","esi-universe.read_structures.v1","esi-bookmarks.read_character_bookmarks.v1","esi-killmails.read_killmails.v1","esi-corporations.read_corporation_membership.v1","esi-assets.read_assets.v1","esi-planets.manage_planets.v1","esi-fleets.read_fleet.v1","esi-fleets.write_fleet.v1","esi-ui.open_window.v1","esi-ui.write_waypoint.v1","esi-characters.write_contacts.v1","esi-fittings.read_fittings.v1","esi-fittings.write_fittings.v1","esi-markets.structure_markets.v1","esi-corporations.read_structures.v1","esi-characters.read_loyalty.v1","esi-characters.read_opportunities.v1","esi-characters.read_chat_channels.v1","esi-characters.read_medals.v1","esi-characters.read_standings.v1","esi-characters.read_agents_research.v1","esi-industry.read_character_jobs.v1","esi-markets.read_character_orders.v1","esi-characters.read_blueprints.v1","esi-characters.read_corporation_roles.v1","esi-location.read_online.v1","esi-contracts.read_character_contracts.v1","esi-clones.read_implants.v1","esi-characters.read_fatigue.v1","esi-killmails.read_corporation_killmails.v1","esi-corporations.track_members.v1","esi-wallet.read_corporation_wallets.v1","esi-characters.read_notifications.v1","esi-corporations.read_divisions.v1","esi-corporations.read_contacts.v1","esi-assets.read_corporation_assets.v1","esi-corporations.read_titles.v1","esi-corporations.read_blueprints.v1","esi-bookmarks.read_corporation_bookmarks.v1","esi-contracts.read_corporation_contracts.v1","esi-corporations.read_standings.v1","esi-corporations.read_starbases.v1","esi-industry.read_corporation_jobs.v1","esi-markets.read_corporation_orders.v1","esi-corporations.read_container_logs.v1","esi-industry.read_character_mining.v1","esi-industry.read_corporation_mining.v1","esi-planets.read_customs_offices.v1","esi-corporations.read_facilities.v1","esi-corporations.read_medals.v1","esi-characters.read_titles.v1","esi-alliances.read_contacts.v1","esi-characters.read_fw_stats.v1","esi-corporations.read_fw_stats.v1","esi-characterstats.read.v1"],"http://10.1.9.74:5000/sso_callback")
    
    # return redirect(s[0])
    code = "AXxm0F5p-EKkzVobHiogQQ"
    state="LNB310kefYmn0gra"
    s = request_token(code)
    {"access_token":"eyJhbGciOiJSUzI1NiIsImtpZCI6IkpXVC1TaWduYXR1cmUtS2V5IiwidHlwIjoiSldUIn0.eyJzY3AiOlsicHVibGljRGF0YSIsImVzaS1jYWxlbmRhci5yZXNwb25kX2NhbGVuZGFyX2V2ZW50cy52MSIsImVzaS1jYWxlbmRhci5yZWFkX2NhbGVuZGFyX2V2ZW50cy52MSIsImVzaS1sb2NhdGlvbi5yZWFkX2xvY2F0aW9uLnYxIiwiZXNpLWxvY2F0aW9uLnJlYWRfc2hpcF90eXBlLnYxIiwiZXNpLW1haWwub3JnYW5pemVfbWFpbC52MSIsImVzaS1tYWlsLnJlYWRfbWFpbC52MSIsImVzaS1tYWlsLnNlbmRfbWFpbC52MSIsImVzaS1za2lsbHMucmVhZF9za2lsbHMudjEiLCJlc2ktc2tpbGxzLnJlYWRfc2tpbGxxdWV1ZS52MSIsImVzaS13YWxsZXQucmVhZF9jaGFyYWN0ZXJfd2FsbGV0LnYxIiwiZXNpLXdhbGxldC5yZWFkX2NvcnBvcmF0aW9uX3dhbGxldC52MSIsImVzaS1zZWFyY2guc2VhcmNoX3N0cnVjdHVyZXMudjEiLCJlc2ktY2xvbmVzLnJlYWRfY2xvbmVzLnYxIiwiZXNpLWNoYXJhY3RlcnMucmVhZF9jb250YWN0cy52MSIsImVzaS11bml2ZXJzZS5yZWFkX3N0cnVjdHVyZXMudjEiLCJlc2ktYm9va21hcmtzLnJlYWRfY2hhcmFjdGVyX2Jvb2ttYXJrcy52MSIsImVzaS1raWxsbWFpbHMucmVhZF9raWxsbWFpbHMudjEiLCJlc2ktY29ycG9yYXRpb25zLnJlYWRfY29ycG9yYXRpb25fbWVtYmVyc2hpcC52MSIsImVzaS1hc3NldHMucmVhZF9hc3NldHMudjEiLCJlc2ktcGxhbmV0cy5tYW5hZ2VfcGxhbmV0cy52MSIsImVzaS1mbGVldHMucmVhZF9mbGVldC52MSIsImVzaS1mbGVldHMud3JpdGVfZmxlZXQudjEiLCJlc2ktdWkub3Blbl93aW5kb3cudjEiLCJlc2ktdWkud3JpdGVfd2F5cG9pbnQudjEiLCJlc2ktY2hhcmFjdGVycy53cml0ZV9jb250YWN0cy52MSIsImVzaS1maXR0aW5ncy5yZWFkX2ZpdHRpbmdzLnYxIiwiZXNpLWZpdHRpbmdzLndyaXRlX2ZpdHRpbmdzLnYxIiwiZXNpLW1hcmtldHMuc3RydWN0dXJlX21hcmtldHMudjEiLCJlc2ktY29ycG9yYXRpb25zLnJlYWRfc3RydWN0dXJlcy52MSIsImVzaS1jaGFyYWN0ZXJzLnJlYWRfbG95YWx0eS52MSIsImVzaS1jaGFyYWN0ZXJzLnJlYWRfb3Bwb3J0dW5pdGllcy52MSIsImVzaS1jaGFyYWN0ZXJzLnJlYWRfY2hhdF9jaGFubmVscy52MSIsImVzaS1jaGFyYWN0ZXJzLnJlYWRfbWVkYWxzLnYxIiwiZXNpLWNoYXJhY3RlcnMucmVhZF9zdGFuZGluZ3MudjEiLCJlc2ktY2hhcmFjdGVycy5yZWFkX2FnZW50c19yZXNlYXJjaC52MSIsImVzaS1pbmR1c3RyeS5yZWFkX2NoYXJhY3Rlcl9qb2JzLnYxIiwiZXNpLW1hcmtldHMucmVhZF9jaGFyYWN0ZXJfb3JkZXJzLnYxIiwiZXNpLWNoYXJhY3RlcnMucmVhZF9ibHVlcHJpbnRzLnYxIiwiZXNpLWNoYXJhY3RlcnMucmVhZF9jb3Jwb3JhdGlvbl9yb2xlcy52MSIsImVzaS1sb2NhdGlvbi5yZWFkX29ubGluZS52MSIsImVzaS1jb250cmFjdHMucmVhZF9jaGFyYWN0ZXJfY29udHJhY3RzLnYxIiwiZXNpLWNsb25lcy5yZWFkX2ltcGxhbnRzLnYxIiwiZXNpLWNoYXJhY3RlcnMucmVhZF9mYXRpZ3VlLnYxIiwiZXNpLWtpbGxtYWlscy5yZWFkX2NvcnBvcmF0aW9uX2tpbGxtYWlscy52MSIsImVzaS1jb3Jwb3JhdGlvbnMudHJhY2tfbWVtYmVycy52MSIsImVzaS13YWxsZXQucmVhZF9jb3Jwb3JhdGlvbl93YWxsZXRzLnYxIiwiZXNpLWNoYXJhY3RlcnMucmVhZF9ub3RpZmljYXRpb25zLnYxIiwiZXNpLWNvcnBvcmF0aW9ucy5yZWFkX2RpdmlzaW9ucy52MSIsImVzaS1jb3Jwb3JhdGlvbnMucmVhZF9jb250YWN0cy52MSIsImVzaS1hc3NldHMucmVhZF9jb3Jwb3JhdGlvbl9hc3NldHMudjEiLCJlc2ktY29ycG9yYXRpb25zLnJlYWRfdGl0bGVzLnYxIiwiZXNpLWNvcnBvcmF0aW9ucy5yZWFkX2JsdWVwcmludHMudjEiLCJlc2ktYm9va21hcmtzLnJlYWRfY29ycG9yYXRpb25fYm9va21hcmtzLnYxIiwiZXNpLWNvbnRyYWN0cy5yZWFkX2NvcnBvcmF0aW9uX2NvbnRyYWN0cy52MSIsImVzaS1jb3Jwb3JhdGlvbnMucmVhZF9zdGFuZGluZ3MudjEiLCJlc2ktY29ycG9yYXRpb25zLnJlYWRfc3RhcmJhc2VzLnYxIiwiZXNpLWluZHVzdHJ5LnJlYWRfY29ycG9yYXRpb25fam9icy52MSIsImVzaS1tYXJrZXRzLnJlYWRfY29ycG9yYXRpb25fb3JkZXJzLnYxIiwiZXNpLWNvcnBvcmF0aW9ucy5yZWFkX2NvbnRhaW5lcl9sb2dzLnYxIiwiZXNpLWluZHVzdHJ5LnJlYWRfY2hhcmFjdGVyX21pbmluZy52MSIsImVzaS1pbmR1c3RyeS5yZWFkX2NvcnBvcmF0aW9uX21pbmluZy52MSIsImVzaS1wbGFuZXRzLnJlYWRfY3VzdG9tc19vZmZpY2VzLnYxIiwiZXNpLWNvcnBvcmF0aW9ucy5yZWFkX2ZhY2lsaXRpZXMudjEiLCJlc2ktY29ycG9yYXRpb25zLnJlYWRfbWVkYWxzLnYxIiwiZXNpLWNoYXJhY3RlcnMucmVhZF90aXRsZXMudjEiLCJlc2ktYWxsaWFuY2VzLnJlYWRfY29udGFjdHMudjEiLCJlc2ktY2hhcmFjdGVycy5yZWFkX2Z3X3N0YXRzLnYxIiwiZXNpLWNvcnBvcmF0aW9ucy5yZWFkX2Z3X3N0YXRzLnYxIiwiZXNpLWNoYXJhY3RlcnN0YXRzLnJlYWQudjEiXSwianRpIjoiZTM2YjdhNzQtZTMxMy00YjRkLWI3NzctMTlkMDUzOTYwMDJiIiwia2lkIjoiSldULVNpZ25hdHVyZS1LZXkiLCJzdWIiOiJDSEFSQUNURVI6RVZFOjk2NjQxNjA4IiwiYXpwIjoiYWNkZDczY2UwODhkNDM2YmEzZWRmNDY5ZTA5OWVjYWUiLCJ0ZW5hbnQiOiJ0cmFucXVpbGl0eSIsInRpZXIiOiJsaXZlIiwicmVnaW9uIjoid29ybGQiLCJhdWQiOlsiYWNkZDczY2UwODhkNDM2YmEzZWRmNDY5ZTA5OWVjYWUiLCJFVkUgT25saW5lIl0sIm5hbWUiOiJEdVNodSIsIm93bmVyIjoiZ1ZRY2lzSE9jMkg2K1JxS3hEQTlHU2NuNmx3PSIsImV4cCI6MTczNzYyMjMwNSwiaWF0IjoxNzM3NjIxMTA1LCJpc3MiOiJodHRwczovL2xvZ2luLmV2ZW9ubGluZS5jb20ifQ.lG-ypzjHY4lyaC7u_fy7cW5VQ3qoW9NQ30yk0Qanw7SXoxxDLbJexDrVGJpvZtUhWmRYGvJghuVlBoqGcEPt3H5HUmmTKXqCh3a0SXZO5K1sUuqMVth2hxy0RWwPqmhp0AfCV4I8tIJa6vFgyMAYPbasjzglDtAP4m8Lf6_azz-Vh26C36R__vueUCK68NAHDf0koiTISdmzkiSW7cPOeDDeOjq9XdCryd_-RGxl9RPUB0BxaJ-8LAjDrfwQruQ_Mpv5RsIZjCDO0NCU4Lie5vIw0fYraxIx9VgI3RcbEH8q59dhiV6q8RFNojDEU_C9auXUcoa6aixHkDo6xWTe6A",
     "expires_in":1199,
     "refresh_token":"e4AfLbY6pUi6b773cCMSMw==",
     "token_type":"Bearer"}
    return s


@app.route('/auth')
def auth():
    
    if True:
        a = login()
    return a
    # if the user is authed, get the wallet content !
    if current_user.is_authenticated:
        # give the token data to esisecurity, it will check alone
        # if the access token need some update
        esisecurity.update_token(current_user.get_sso_data())

        op = esiapp.op['get_characters_character_id_wallet'](
            character_id=current_user.character_id
        )
        wallet = esiclient.request(op)

    return render_template('base.html', **{
        'wallet': wallet,
    })

@app.route('/sso_callback/')
def sso_callback():
    code = request.args.get('code')  # 获取 'code' 参数
    state = request.args.get('state')  # 获取 'state' 参数
    return jsonify([code,state])