# app/views/home.py
from flask import Flask, jsonify, g,request,redirect,Blueprint
import sqlite3
from datetime import datetime, timedelta
import json

character = Blueprint('character', __name__)


@character.route('/auth')
def auth(): 
    """ this redirects the user to the EVE SSO login """
    #first we send a get request to ccp and this redirect to sso_callback with two parameters code and state. The code will expire in 5 minutes
    scopes = ['esi-ui.write_waypoint.v1', 'esi-characters.read_fatigue.v1', 'esi-characters.read_standings.v1', 'esi-characterstats.read.v1',
    'esi-characters.read_agents_research.v1', 'esi-mail.send_mail.v1', 'esi-characters.write_contacts.v1', 'esi-characters.read_blueprints.v1',
    'esi-planets.manage_planets.v1', 'esi-fleets.write_fleet.v1', 'esi-markets.read_character_orders.v1', 'esi-industry.read_character_mining.v1',
    'esi-alliances.read_contacts.v1', 'esi-industry.read_corporation_mining.v1', 'esi-corporations.read_contacts.v1', 'esi-corporations.track_members.v1',
    'esi-corporations.read_divisions.v1', 'esi-characters.read_opportunities.v1', 'esi-skills.read_skills.v1', 'esi-mail.organize_mail.v1',
    'esi-corporations.read_blueprints.v1', 'esi-clones.read_clones.v1', 'esi-killmails.read_corporation_killmails.v1', 'esi-characters.read_chat_channels.v1',
    'esi-fittings.write_fittings.v1', 'esi-wallet.read_character_wallet.v1', 'esi-clones.read_implants.v1', 'esi-location.read_online.v1',
    'esi-assets.read_assets.v1', 'esi-contracts.read_corporation_contracts.v1', 'esi-bookmarks.read_character_bookmarks.v1',
    'esi-location.read_ship_type.v1', 'esi-corporations.read_facilities.v1','esi-characters.read_notifications.v1', 'esi-mail.read_mail.v1',
    'esi-industry.read_character_jobs.v1', 'esi-planets.read_customs_offices.v1', 'esi-characters.read_fw_stats.v1', 'esi-characters.read_corporation_roles.v1',
    'esi-killmails.read_killmails.v1', 'esi-corporations.read_fw_stats.v1', 'esi-characters.read_loyalty.v1', 'esi-location.read_location.v1', 'esi-bookmarks.read_corporation_bookmarks.v1',
    'esi-characters.read_contacts.v1','esi-characters.read_titles.v1', 'esi-skills.read_skillqueue.v1', 'esi-universe.read_structures.v1', 'esi-corporations.read_titles.v1',
    'esi-assets.read_corporation_assets.v1', 'esi-corporations.read_structures.v1', 'esi-fittings.read_fittings.v1', 'esi-contracts.read_character_contracts.v1',
    'esi-search.search_structures.v1', 'esi-corporations.read_medals.v1', 'esi-corporations.read_container_logs.v1', 'esi-corporations.read_standings.v1', 'esi-markets.structure_markets.v1',
    'esi-fleets.read_fleet.v1', 'esi-corporations.read_starbases.v1', 'esi-markets.read_corporation_orders.v1', 'esi-ui.open_window.v1', 'esi-industry.read_corporation_jobs.v1',
    'esi-wallet.read_corporation_wallet.v1', 'esi-corporations.read_corporation_membership.v1']
    
    res = g.esi_client.redirect_to_sso(scopes,"http://127.0.0.1:5000/character/sso_callback")
    return redirect(res[0])
    

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

def update_esi_token():
    res = g.sqlite_client.cursor().execute("""select value from kv_data where key="esi" """).fetchone()
    esi_data = json.loads(res[0])
    for c in  esi_data['character_info']:
        if 'access_token_create_time' not in c:
            continue 
        create_time_str = c["access_token_create_time"]
        create_time = datetime.strptime(create_time_str, "%Y-%m-%d %H:%M:%S")
        expiration = timedelta(seconds=1100)
        current_time = datetime.now()
        if current_time - create_time > expiration:
            s = g.esi_client.refresh_token(c["refresh_token"])
            c["access_token"] =  s["access_token"]
            c["access_token_create_time"] = current_time.strftime("%Y-%m-%d %H:%M:%S")
        
        
    g.sqlite_client.cursor().execute("""UPDATE kv_data SET value = ? WHERE key = "esi" """,(json.dumps(esi_data),))
    g.sqlite_client.commit()
    return esi_data



@character.route('/sso_callback/')
def sso_callback():
    code = request.args.get('code')  
    state = request.args.get('state')

    # here we get token using the code. state is used for security check.
    s = g.esi_client.request_token(code)
    """ you will get a json like this:
    {"access_token":"eyJhbGciOiJSUzI1NiIsImtpZCI6IkpXVC1TaWduYXR1cmUtS2V5IiwidHlwIjoiSldUIn0.eyJzY3AiOlsicHVibGljRGF0YSIsImVzaS1jYWxlbmRhci5yZXNwb25kX2NhbGVuZGFyX2V2ZW50cy52MSIsImVzaS1jYWxlbmRhci5yZWFkX2NhbGVuZGFyX2V2ZW50cy52MSIsImVzaS1sb2NhdGlvbi5yZWFkX2xvY2F0aW9uLnYxIiwiZXNpLWxvY2F0aW9uLnJlYWRfc2hpcF90eXBlLnYxIiwiZXNpLW1haWwub3JnYW5pemVfbWFpbC52MSIsImVzaS1tYWlsLnJlYWRfbWFpbC52MSIsImVzaS1tYWlsLnNlbmRfbWFpbC52MSIsImVzaS1za2lsbHMucmVhZF9za2lsbHMudjEiLCJlc2ktc2tpbGxzLnJlYWRfc2tpbGxxdWV1ZS52MSIsImVzaS13YWxsZXQucmVhZF9jaGFyYWN0ZXJfd2FsbGV0LnYxIiwiZXNpLXdhbGxldC5yZWFkX2NvcnBvcmF0aW9uX3dhbGxldC52MSIsImVzaS1zZWFyY2guc2VhcmNoX3N0cnVjdHVyZXMudjEiLCJlc2ktY2xvbmVzLnJlYWRfY2xvbmVzLnYxIiwiZXNpLWNoYXJhY3RlcnMucmVhZF9jb250YWN0cy52MSIsImVzaS11bml2ZXJzZS5yZWFkX3N0cnVjdHVyZXMudjEiLCJlc2ktYm9va21hcmtzLnJlYWRfY2hhcmFjdGVyX2Jvb2ttYXJrcy52MSIsImVzaS1raWxsbWFpbHMucmVhZF9raWxsbWFpbHMudjEiLCJlc2ktY29ycG9yYXRpb25zLnJlYWRfY29ycG9yYXRpb25fbWVtYmVyc2hpcC52MSIsImVzaS1hc3NldHMucmVhZF9hc3NldHMudjEiLCJlc2ktcGxhbmV0cy5tYW5hZ2VfcGxhbmV0cy52MSIsImVzaS1mbGVldHMucmVhZF9mbGVldC52MSIsImVzaS1mbGVldHMud3JpdGVfZmxlZXQudjEiLCJlc2ktdWkub3Blbl93aW5kb3cudjEiLCJlc2ktdWkud3JpdGVfd2F5cG9pbnQudjEiLCJlc2ktY2hhcmFjdGVycy53cml0ZV9jb250YWN0cy52MSIsImVzaS1maXR0aW5ncy5yZWFkX2ZpdHRpbmdzLnYxIiwiZXNpLWZpdHRpbmdzLndyaXRlX2ZpdHRpbmdzLnYxIiwiZXNpLW1hcmtldHMuc3RydWN0dXJlX21hcmtldHMudjEiLCJlc2ktY29ycG9yYXRpb25zLnJlYWRfc3RydWN0dXJlcy52MSIsImVzaS1jaGFyYWN0ZXJzLnJlYWRfbG95YWx0eS52MSIsImVzaS1jaGFyYWN0ZXJzLnJlYWRfb3Bwb3J0dW5pdGllcy52MSIsImVzaS1jaGFyYWN0ZXJzLnJlYWRfY2hhdF9jaGFubmVscy52MSIsImVzaS1jaGFyYWN0ZXJzLnJlYWRfbWVkYWxzLnYxIiwiZXNpLWNoYXJhY3RlcnMucmVhZF9zdGFuZGluZ3MudjEiLCJlc2ktY2hhcmFjdGVycy5yZWFkX2FnZW50c19yZXNlYXJjaC52MSIsImVzaS1pbmR1c3RyeS5yZWFkX2NoYXJhY3Rlcl9qb2JzLnYxIiwiZXNpLW1hcmtldHMucmVhZF9jaGFyYWN0ZXJfb3JkZXJzLnYxIiwiZXNpLWNoYXJhY3RlcnMucmVhZF9ibHVlcHJpbnRzLnYxIiwiZXNpLWNoYXJhY3RlcnMucmVhZF9jb3Jwb3JhdGlvbl9yb2xlcy52MSIsImVzaS1sb2NhdGlvbi5yZWFkX29ubGluZS52MSIsImVzaS1jb250cmFjdHMucmVhZF9jaGFyYWN0ZXJfY29udHJhY3RzLnYxIiwiZXNpLWNsb25lcy5yZWFkX2ltcGxhbnRzLnYxIiwiZXNpLWNoYXJhY3RlcnMucmVhZF9mYXRpZ3VlLnYxIiwiZXNpLWtpbGxtYWlscy5yZWFkX2NvcnBvcmF0aW9uX2tpbGxtYWlscy52MSIsImVzaS1jb3Jwb3JhdGlvbnMudHJhY2tfbWVtYmVycy52MSIsImVzaS13YWxsZXQucmVhZF9jb3Jwb3JhdGlvbl93YWxsZXRzLnYxIiwiZXNpLWNoYXJhY3RlcnMucmVhZF9ub3RpZmljYXRpb25zLnYxIiwiZXNpLWNvcnBvcmF0aW9ucy5yZWFkX2RpdmlzaW9ucy52MSIsImVzaS1jb3Jwb3JhdGlvbnMucmVhZF9jb250YWN0cy52MSIsImVzaS1hc3NldHMucmVhZF9jb3Jwb3JhdGlvbl9hc3NldHMudjEiLCJlc2ktY29ycG9yYXRpb25zLnJlYWRfdGl0bGVzLnYxIiwiZXNpLWNvcnBvcmF0aW9ucy5yZWFkX2JsdWVwcmludHMudjEiLCJlc2ktYm9va21hcmtzLnJlYWRfY29ycG9yYXRpb25fYm9va21hcmtzLnYxIiwiZXNpLWNvbnRyYWN0cy5yZWFkX2NvcnBvcmF0aW9uX2NvbnRyYWN0cy52MSIsImVzaS1jb3Jwb3JhdGlvbnMucmVhZF9zdGFuZGluZ3MudjEiLCJlc2ktY29ycG9yYXRpb25zLnJlYWRfc3RhcmJhc2VzLnYxIiwiZXNpLWluZHVzdHJ5LnJlYWRfY29ycG9yYXRpb25fam9icy52MSIsImVzaS1tYXJrZXRzLnJlYWRfY29ycG9yYXRpb25fb3JkZXJzLnYxIiwiZXNpLWNvcnBvcmF0aW9ucy5yZWFkX2NvbnRhaW5lcl9sb2dzLnYxIiwiZXNpLWluZHVzdHJ5LnJlYWRfY2hhcmFjdGVyX21pbmluZy52MSIsImVzaS1pbmR1c3RyeS5yZWFkX2NvcnBvcmF0aW9uX21pbmluZy52MSIsImVzaS1wbGFuZXRzLnJlYWRfY3VzdG9tc19vZmZpY2VzLnYxIiwiZXNpLWNvcnBvcmF0aW9ucy5yZWFkX2ZhY2lsaXRpZXMudjEiLCJlc2ktY29ycG9yYXRpb25zLnJlYWRfbWVkYWxzLnYxIiwiZXNpLWNoYXJhY3RlcnMucmVhZF90aXRsZXMudjEiLCJlc2ktYWxsaWFuY2VzLnJlYWRfY29udGFjdHMudjEiLCJlc2ktY2hhcmFjdGVycy5yZWFkX2Z3X3N0YXRzLnYxIiwiZXNpLWNvcnBvcmF0aW9ucy5yZWFkX2Z3X3N0YXRzLnYxIiwiZXNpLWNoYXJhY3RlcnN0YXRzLnJlYWQudjEiXSwianRpIjoiZTM2YjdhNzQtZTMxMy00YjRkLWI3NzctMTlkMDUzOTYwMDJiIiwia2lkIjoiSldULVNpZ25hdHVyZS1LZXkiLCJzdWIiOiJDSEFSQUNURVI6RVZFOjk2NjQxNjA4IiwiYXpwIjoiYWNkZDczY2UwODhkNDM2YmEzZWRmNDY5ZTA5OWVjYWUiLCJ0ZW5hbnQiOiJ0cmFucXVpbGl0eSIsInRpZXIiOiJsaXZlIiwicmVnaW9uIjoid29ybGQiLCJhdWQiOlsiYWNkZDczY2UwODhkNDM2YmEzZWRmNDY5ZTA5OWVjYWUiLCJFVkUgT25saW5lIl0sIm5hbWUiOiJEdVNodSIsIm93bmVyIjoiZ1ZRY2lzSE9jMkg2K1JxS3hEQTlHU2NuNmx3PSIsImV4cCI6MTczNzYyMjMwNSwiaWF0IjoxNzM3NjIxMTA1LCJpc3MiOiJodHRwczovL2xvZ2luLmV2ZW9ubGluZS5jb20ifQ.lG-ypzjHY4lyaC7u_fy7cW5VQ3qoW9NQ30yk0Qanw7SXoxxDLbJexDrVGJpvZtUhWmRYGvJghuVlBoqGcEPt3H5HUmmTKXqCh3a0SXZO5K1sUuqMVth2hxy0RWwPqmhp0AfCV4I8tIJa6vFgyMAYPbasjzglDtAP4m8Lf6_azz-Vh26C36R__vueUCK68NAHDf0koiTISdmzkiSW7cPOeDDeOjq9XdCryd_-RGxl9RPUB0BxaJ-8LAjDrfwQruQ_Mpv5RsIZjCDO0NCU4Lie5vIw0fYraxIx9VgI3RcbEH8q59dhiV6q8RFNojDEU_C9auXUcoa6aixHkDo6xWTe6A",
     "expires_in":1199,
     "refresh_token":"e4AfLbY6pUi6b773cCMSMw==",
     "token_type":"Bearer"}
    """
    #save token to db
    name,uid = g.esi_client.get_charcter_info(s['access_token'])

    res = g.sqlite_client.cursor().execute("""select value from kv_data where key="esi" """).fetchone()
    esi_data = json.loads(res[0])
    
    if 'character_info' not in esi_data:
        esi_data['character_info'] = []
    else:
        esi_data['character_info'] = [item for item in esi_data['character_info'] if item.get('name') != name]

    new_character = {
        "name":name,
        "uid": uid,
        "access_token":s['access_token'],
        "refresh_token":s['refresh_token'],
        "access_token_create_time":datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    esi_data['character_info'].append(new_character)
    
    g.sqlite_client.cursor().execute("""UPDATE kv_data SET value = ? WHERE key = "esi" """,(json.dumps(esi_data),))

    g.sqlite_client.commit()

    return "Access granted!"


def get_esi_token():
    res = g.sqlite_client.cursor().execute("""select value from kv_data where key="esi" """).fetchone()
    esi_data = json.loads(res[0])
    for c in  esi_data['character_info']:
        create_time_str = c["access_token_create_time"]
        create_time = datetime.strptime(create_time_str, "%Y-%m-%d %H:%M:%S")
        expiration = timedelta(seconds=1100)
        current_time = datetime.now()
        if current_time - create_time > expiration:
            s = g.esi_client.refresh_token(c["refresh_token"])
            c["access_token"] =  s["access_token"]
            c["refresh_token"] =  s["refresh_token"]
            c["access_token_create_time"] = current_time.strftime("%Y-%m-%d %H:%M:%S")
        
        
    g.sqlite_client.cursor().execute("""UPDATE kv_data SET value = ? WHERE key = "esi" """,(json.dumps(esi_data),))
    g.sqlite_client.commit()
    return esi_data



@character.route('/esi_list')
def esi_list():
    esi_data = get_esi_token()
    return jsonify(esi_data)

@character.route('/wallet')
def get_wallet():
    esi_data = get_esi_token()
    res = []
    sum = 0
    for c in esi_data['character_info']:
        balance = g.esi_client.get_wallet(c['uid'],c["access_token"])
        sum += balance
        res.append({c["name"]:balance})
    res.append({"sum":sum})
    return jsonify(res)

@character.route('get_jobs')
def get_jobs():
    esi_data = get_esi_token()
    res = []
    for c in esi_data['character_info']:
        job = g.esi_client.get_jobs(c['uid'],c["access_token"])
        res.append({c["name"]:job})
    return jsonify(res)
    
@character.route('assets')
def get_assets():
    esi_data = get_esi_token()
    res = []
    for c in esi_data['character_info']:
        asserts = g.esi_client.get_assets(c['uid'],c["access_token"])
        res.append({c["name"]:asserts})
    return jsonify(res)