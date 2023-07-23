from random import shuffle
from api import send_message
import json, re

roles = ['Medic', 'Seer', 'Villager_simple', 'Villager_simple', 'Villager_simple', 'Werewolf_leader', 'Werewolf_simple']

# random shuffling the roles

shuffle(roles)

#Create a players list

players = [{'role' : role , 'is_alive' : True , 'special_actions_log' : [] , 'votes_log' : [] , 'notes' : []} for role in roles]

# adding essential variables


log = []
game_summary = []
rounds_cnt = 0
werewolves_cnt = 2
villagers_cnt = 5
token_limit = 4000
time_limit_rate = 20
alives_index = list(range(7))

def game_end() : 
    if werewolves_cnt == villagers_cnt : 
        return "Werewolves Win!"
    if werewolves_cnt == 0 : 
        return "Villagers Win!"
    return 0 

def render_game_intro(player_number) : 
    game_intro = f"""
You are a meticulous agent, you are playing Mafia party game (Werewolf).
your actions must be reasonable and based on your UTILITY - that
for Werewolves : 
    eliminating Villagers and try to confuse them. also showing yourself as villager so they trust you.
for Villagers : 
    guess and find werewolves and try to kick them out by gathering vote for them. convince others that you are innocent and trustable.
--------
we have 7 players from 0 to 6 and you are one of them. 
roles : 
    Villagers:
        - 3 Villager_simple : no special ability, just try to guess werewolves and vote them and share ideas with others. finding teammates and prove that it's not werewolf.
        - 1 Medic : at nights will send a player number which wants to heal. e.g if he heal player number X and mafia target X at night, X will remain in game.
        - 1 Seer : at nights will ask moderator a player number and moderator will say that number is werewolf(True) or not(False). then he should undirectly tell this to others.(Shouldn't say "i am the Seer" i know he is werewolf) 
    Werewolves:
        - Werewolf_Leader : will make last decision at nights with considering the advice of Werewolf_simple for eliminating a player from the game.
        - Werewolf_simple : try to help Werewolf_leader to make Villagers confused. 
game logics : 
    - You are trying to convince other players that you are a village - whether or not you really are. They need to genuinely believe your statement. 
    - You should target directly some players with saying their numbers. if you are Villager and you believe someone is lying you should try to eliminate him by gathering others to vote for him.
    - You should be clear and direct and take in to account all notes you have taken before about the game and change your guesses if it's needed.
ATTENTION : 
!!! You MUST NOT REVEAL your role if it is Medic or Seer. you can claim that you are villager(lie or true) but for example you shouldn't say : "I'm Medic"
!!! there's no needage to remind rules to others they will see it. just focus on your own game and reason gathering.
!!! When you are asked to answer "JUST A NUMBER" you should just respond an integer no more details! just a simple integer of a player.
!!! don't use repeatitive phrases like you are emailing to someone. be short and direct. also be somehow aggressive and start target randomely in round 1 .
Your notepad : 
every player has a private notepad. in each round (day and night) you can add some notes for yourself to it to remember for next decisions. your notepad will be sent to you at the end of this message.
    - You should be clear and summarise important actions in the game that you think it will help you in future. it should be SHORT and don't write unneccesary things in it.
--------
Your information : 
You are player number : {player_number}
Your role is : {players[player_number]['role']}"""
    return game_intro

def render_game_status() :
    s = [{i : players[i]['is_alive']} for i in range(7)] 
    return f"""########
Game status : 
we are at round : {rounds_cnt}
alive werewolves : {werewolves_cnt}
alive Villagers : {villagers_cnt}
Players is_alive status : 
{s}
########"""

def render_notepad(player_number) : 
    return f"""
Your notepad from previous rounds : 
{players[player_number]['notes']}""" + str(players[player_number]['special_actions_log'])




def kill(player_number)  :
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
        res = send_message(render_game_intro(i), "Todays report:" + str(report) + render_game_status() + render_notepad(i) , "Command: it's your turn to speak")
        report.append(f"""Player {i} : 
{res}""")
        log.append({'event' : 'speech' , 'content': {'player':i , 'context':res}})
    votes = [0]*7
    for i in alives_index : 
        res = send_message(render_game_intro(i), "Todays report:" + str(report)+ render_game_status() + render_notepad(i) , "Command: just send the number of the player that you want to vote for")
        log.append({'event' : 'voted' , 'content': {'player':i , 'voted_to_player':int(res)}})
        num = [int(s) for s in res.split() if s.isdigit()][0]
        votes[num]+=1
        report.append(f"Player{i} Voted to {num}")
    # Here will be a bug due to probablity of two or more maximum voted.
    dead_index = votes.index(votes.max)
    kill(dead_index)
    for i in alives_index : 
        res = send_message(render_game_intro(i), "Todays report:" + str(report)+ render_game_status() + render_notepad(i) , "based on last day add some notes to your notepad : ")
        log.append({'event' : 'notetaking' , 'content': {'player':i , 'context':res}})
        players[i]['notes'] += res
    memory = report
    return

def night() :
    report = memory
    healed_guy = None
    if players[roles.index('Medic')]['is_alive'] == True : 
        res = send_message(render_game_intro(roles.index('Medic')), "Todays report:" + str(report)+ render_game_status() + render_notepad(roles.index('Medic')) , "Command : send the number of player who you want to heal for tonight.")
        healed_guy = [int(s) for s in res.split() if s.isdigit()][0]
        log.append({'event' : 'healed' , 'content': {'player':healed_guy}})
    if players[roles.index('Seer')]['is_alive'] == True :     
        res = send_message(render_game_intro(roles.index('Seer')), "Todays report:" + str(report)+ render_game_status() + render_notepad(roles.index('Seer')) , "Command : send the number of player who you want to know that is werewolf or not for tonight.")
        inq = [int(s) for s in res.split() if s.isdigit()][0]
        players[roles.index('Seer')]['special_actions_log'].append(f"{inq} is Werewolf? : {'Werewolf' in players[inq]['role']}")
        log.append({'event' : 'inquiried' , 'content': {'player':inq , 'context':'Werewolf' in players[inq]['role']}})
    if players[roles.index('Werewolf_simple')]['is_alive'] == True : 
        advice = send_message(render_game_intro(roles.index('Werewolf_simple')), "Todays report:" + str(report)+ render_game_status() + render_notepad(roles.index('Werewolf_simple')) , "Command : send a short advice to Werewolf_leader to which player for eliminating for tonight")
        log.append({'event' : 'speech' , 'content': {'player': roles.index('Werewolf_simple'), 'context':advice}})
    
    res = send_message(render_game_intro(roles.index('Werewolf_leader')), "Todays report:" + str(report)+ render_game_status() + render_notepad(roles.index('Werewolf_leader')) , "Command : send the number of player who you want to heal for tonight.")
    targeted_guy = [int(s) for s in res.split() if s.isdigit()][0]
    log.append({'event' : 'targeted' , 'content': {'player':targeted_guy}})
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






