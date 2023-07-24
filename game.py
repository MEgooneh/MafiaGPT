from random import shuffle
from api import send_message
import json, re

roles = ['Medic', 'Seer', 'Villager_simple', 'Villager_simple', 'Villager_simple', 'Werewolf_leader', 'Werewolf_simple']

# random shuffling the roles

shuffle(roles)

#Create a players list

players = [{'role' : role , 'is_alive' : True , 'special_actions_log' : [] , 'votes_log' : [] , 'notes' : ""} for role in roles]

# adding essential variables


log = []
game_summary = []
rounds_cnt = 0
werewolves_cnt = 2
villagers_cnt = 5
token_limit = 4000
time_limit_rate = 20
alives_index = list(range(7))


# add initial logs : 
log += [{'event' : 'roles', 'content':{'player':i , 'role':roles[i]}} for i in range(7)]

def game_end() : 
    if werewolves_cnt == villagers_cnt :
        log.append({'event' : 'end' , 'content': {'winner':"Werewolves"}})
        json.dump(log , open('log.json' , 'w'))
        return 1
    if werewolves_cnt == 0 : 
        log.append({'event' : 'end' , 'content': {'winner':"Villagers"}})
        json.dump(log , open('log.json' , 'w'))
        return 1
    return 0 

def render_game_intro(player_number) : 
    io = open('intro_prompt.txt' , 'r')
    return eval(io.read())

def string_aliveness(player_number) : 
    if players[player_number]['is_alive'] == True : 
        return "ALIVE"
    else :
        return "DEAD"

def render_game_report(player_number , report) :
    aliveness = [f"Player {i} : " + string_aliveness(i) for i in range(7)] 
    io = open('report_prompt.txt','r')
    return eval(io.read())

def render_speech_command() : 
    return """ATTENTION : 
!!! You MUST NOT REVEAL your role if it is Medic or Seer. you can claim that you are villager(lie or true) but for example you shouldn't say : "I'm Medic"
!!! there's no needage to remind rules to others. just focus on your own game and don't repeat things.
!!! don't use repeatitive phrases. add something to the game. be short and direct. also be somehow aggressive and start target randomely in round 1 .
NOW IS YOUR TURN TO SPEAK TO ALIVE PLAYERS : """

def render_notetaking_command(player_number) : 
    return f"""
Your notes as your memory and your strategy: 
every player has a private notepad. in each round (day and night) you can update that notes for yourself to remember for next decisions. your notepad will be only your last update and it will override. so try to summarise previous notes in new one too.
    - You should be clear and summarise important actions in the round that you think it will help you in future. it should be SHORT and don't write unneccesary things in it.
    - if you have something previously in your notepad that is not usable anymore (e.g about targeting someone that is no more alive) ignore that note and don't add it to new update.
    - ONLY you can see your notes so you don't talk to others, just create your policies for next rounds. there is no needage to show your innocent. just fix your policy for yourself.
NOW JUST SEND YOUR NEW VERSION OF NOTES : """

def kill(player_number)  :
    global villagers_cnt , werewolves_cnt
    if 'Werewolf' in players[player_number]['role'] : 
        werewolves_cnt -= 1
    else :
        villagers_cnt -= 1
    alives_index.remove(player_number)
    players[player_number]['is_alive'] = False
    log.append({'event' : 'killed' , 'content': {'player':player_number}})


memory = []
# game functions 

def day() :
    report = [] 
    for i in alives_index :
        res = send_message(render_game_intro(i), render_game_report(i , report) , render_speech_command())
        report.append(f"""Player {i} : 
{res}""")
        log.append({'event' : 'speech' , 'content': {'player':i , 'context':res}})
    votes = [0]*7
    for i in alives_index : 
        res = send_message(render_game_intro(i), render_game_report(i , report) , "Command: just send the number of the player that you want to vote for. REMINDER: you must send an alive player number")
        num = int(re.findall(r'\d+', res)[0])
        log.append({'event' : 'voted' , 'content': {'player':i , 'voted_to_player':num , 'reason':res}})
        votes[num]+=1
        report.append(f"Player{i} Voted to {num}")
        players[i]['votes_log'].append(f"Player {i}")
    # Here will be a bug due to probablity of two or more maximum voted.
    if max(votes) > 2 : 
        dead_index = votes.index(max(votes))
        kill(dead_index)
    for i in alives_index : 
        res = send_message(render_game_intro(i), render_game_report(i , report), render_notetaking_command(i))
        log.append({'event' : 'notetaking' , 'content': {'player':i , 'context':res}})
        players[i]['notes'] = (res)
    memory = report
    return

def night() :
    report = memory
    healed_guy = None
    if players[roles.index('Medic')]['is_alive'] == True : 
        res = send_message(render_game_intro(roles.index('Medic')), render_game_report(roles.index('Medic') , report) , "Command : send the number of player who you want to heal for tonight. REMINDER: you must send an alive player number")
        healed_guy = int(re.findall(r'\d+', res)[0])
        players[roles.index('Medic')]['special_actions_log'].append(f"You have healed Player number {healed_guy}")
        log.append({'event' : 'healed' , 'content': {'player':healed_guy , 'reason':res}})
    if players[roles.index('Seer')]['is_alive'] == True :     
        res = send_message(render_game_intro(roles.index('Seer')), render_game_report(roles.index('Seer'), report) , "Command : send the number of player who you want to know that is werewolf or not for tonight. REMINDER: you must send an alive player number")
        inq = int(re.findall(r'\d+', res)[0])
        players[roles.index('Seer')]['special_actions_log'].append(f"You asked moderator that Player {inq} is Werewolf or not. the answer was : {'Werewolf' in players[inq]['role']}")
        players[roles.index('Seer')]['special_actions_log'].append(f"{inq} is Werewolf? : {'Werewolf' in players[inq]['role']}")
        log.append({'event' : 'inquiried' , 'content': {'player':inq , 'context':'Werewolf' in players[inq]['role'] , 'reason':res}})
    if players[roles.index('Werewolf_simple')]['is_alive'] == True : 
        advice = send_message(render_game_intro(roles.index('Werewolf_simple')), render_game_report(roles.index('Werewolf_simple') , report) , "Command : send a short advice to Werewolf_leader to which player for eliminating for tonight")
        log.append({'event' : 'speech' , 'content': {'player': roles.index('Werewolf_simple'), 'context':advice}})
    
    res = send_message(render_game_intro(roles.index('Werewolf_leader')), render_game_report(roles.index('Werewolf_leader') , report) , "Command : JUST send the number of player who you want to heal for tonight. REMINDER: you must send an alive player number")
    targeted_guy = int(re.findall(r'\d+', res)[0])
    log.append({'event' : 'targeted' , 'content': {'player':targeted_guy , 'reason':res}})
    players[roles.index('Werewolf_leader')]['special_actions_log'].append(f"You have attemped to kill Player number {targeted_guy} at night.")
    if targeted_guy != healed_guy : 
        kill(targeted_guy)
    return


while game_end() == 0 : 
    rounds_cnt += 1
    day()
    json.dump(log , open('log.json' , 'w'))
    if game_end() != 0 : 
        break
    night()
    json.dump(log , open('log.json' , 'w'))






