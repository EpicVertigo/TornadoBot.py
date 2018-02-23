import requests
import json

def connect(title_id):
    try:
        data = {"CustomId": "TornadoBot","CreateAccount": False, "TitleId":'{}'.format(title_id)}
        headers = {'Content-Type': "application/json"}
        r =  requests.post('https://'+title_id+'.playfabapi.com/Client/LoginWithCustomID', headers=headers, json=data)
        session_ticket = json.loads(r.text)['data']['SessionTicket']
        return [r.status_code, session_ticket]
    except Exception:
        return [r.status_code, None]

def get_leaderboard(title_id):
    status, ticket = connect(title_id)
    data = {"StatisticName": "Rokkebol","StartPosition": 0}
    headers = {'Content-Type': "application/json", "X-Authentication":ticket}
    if status == 200:
        leaderboard_request =  requests.post('https://'+title_id+'.playfabapi.com/Client/GetLeaderboard', headers=headers, json=data)
        top_player = json.loads(leaderboard_request.text)['data']['Leaderboard'][0]
        return top_player
    else:
      return None
