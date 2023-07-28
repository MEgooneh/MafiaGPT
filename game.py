from random import shuffle
from api import send_message
import json, re

roles = ['Medic', 'Seer', 'Villager_simple', 'Villager_simple', 'Villager_simple', 'Werewolf_leader', 'Werewolf_simple']

# random shuffling the roles

shuffle(roles)

#Create the players list

players = [{'role' : role , 'is_alive' : True , 'special_actions_log' : [] , 'votes_log' : [] , 'notes' : ""} for role in roles]

# adding essential variables

log = [] #it will keep all logs and then dump it to 'log.json'
werewolves_cnt = 2 #alive werewolves counter
villagers_cnt = 5 #alive villagers counter
alives_index = list(range(7)) # a list consisting of alive players number


# let Werewolves to know their teammates
players[roles.index('Werewolf_simple')]['special_actions_log'].append(f"Werewolf_leader .aka your teammate is Player {roles.index('Werewolf_leader')}")
players[roles.index('Werewolf_leader')]['special_actions_log'].append(f"Werewolf_simple .aka your teammate is Player {roles.index('Werewolf_simple')}")


# add players and their roles to log : 
log += [{'event' : 'roles', 'content':{'player':i , 'role':roles[i]}} for i in range(7)]

#logging function
logging = lambda : json.dump(log , open('log.json' , 'w') , indent=4)

def game_end() :
    """
     Will check that the game is over or not. 1 if it's over 0 otherwise
    """ 
    ans = 0 
    if werewolves_cnt == villagers_cnt :
        log.append({'event':'end','winner':'Werewolves'})
        ans = 1 
    if werewolves_cnt == 0 : 
        log.append({'event':'end','winner':'Villagers'})
        ans = 1
    logging()
    return ans 

def render_game_intro(player_number) : 
    """
    Rendering game intro (The first message in every request to api) 
    consisting of the rules and the player information
    
    """
    io = open('intro_prompt.txt' , 'r')
    return eval(io.read())

def string_aliveness(player_number) : 
    """
    Showing the aliveness of players in better format for "render_game_report" function
    
    """
    if players[player_number]['is_alive'] == True : 
        return "ALIVE"
    else :
        return "DEAD"
 
def render_game_report(player_number , report) :
    """
    Rendering game report (The second message in every request to api) 
    consisting of game status and the player special informations and what happened in the game till now
    
    """
    aliveness = [f"Player {i} : " + string_aliveness(i) for i in range(7)] 
    dead_players = [f"Player {i} was : {players[i]['role']}" for i in set(range(7))-set(alives_index)]
    io = open('report_prompt.txt','r')
    return eval(io.read())

# a simple string to command player to speak

def render_speech_command() : 
    return """ATTENTION : 
!!! You MUST NOT REVEAL your exact role. you can claim that you are villager(lie or true) but for example you shouldn't say : "I'm Medic"
!!! there's no needage to remind rules to others. just focus on your own game and don't repeat things.
!!! don't use repeatitive phrases. add something to the game. be short and direct. also be somehow aggressive and start targetting.
NOW IS YOUR TURN TO SPEAK TO ALIVE PLAYERS : """

# a simple string to command player to take a note of the game

def render_notetaking_command(player_number) : 
    return """
Your notes as your memory and your strategy: 
every player has a private notebook. in each round (day and night) you can update that notes for yourself to remember for next decisions. your notebook will be only your last update and it will override. so try to summarise previous notes in new one too.
    - You should be clear and summarise important actions in the round that you think it will help you in future. it should be SHORT and don't write unneccesary things in it.
    - if you have something previously in your notebook that is not usable anymore (e.g about targeting someone that is no more alive) ignore that note and don't add it to new update.
    - ONLY you can see your notes so you don't talk to others, just create your policies for next rounds. there is no needage to show your innocent. just fix your policy for yourself.
NOW JUST SEND YOUR NEW VERSION OF NOTES : """


def kill(player_number)  :
    """
    Will delete information of a player who has eliminated from the game.
    """
    global villagers_cnt , werewolves_cnt
    if 'Werewolf' in roles[player_number] : 
        werewolves_cnt -= 1
    else :
        villagers_cnt -= 1
    alives_index.remove(player_number)
    players[player_number]['is_alive'] = False
    log.append({'event' : 'killed' , 'content': {'player':player_number}})

# a temproray memory to have day's game report for night.
memory = []

############
# game main functions 

def day() :
    report = [] 
    for i in alives_index :
        res = send_message(render_game_intro(i), render_game_report(i , report) , render_speech_command())
        report.append(f"""Player {i} : 
{res}""")
        log.append({'event' : 'speech' , 'content': {'player':i , 'context':res}})
    votes = [0]*7
    log.append({'event':'vote_start'})
    for i in alives_index : 
        res = send_message(render_game_intro(i), render_game_report(i , report) , "Command: just send the number of the player that you want to vote for. REMINDER: you must send an alive player number. You must not vote to yourself")
        nums_in_res = re.findall(r'\d+', res)
        if len(nums_in_res) > 0 :
            num = int(nums_in_res[0]) 
            log.append({'event' : 'voted' , 'content': {'player':i , 'voted_to_player':num , 'reason':res}})
            votes[num]+=1
            report.append(f"Player {i} Voted to {num}")
            players[i]['votes_log'].append(f"Player {num}")
    # Here will be a bug due to probablity of two or more maximum voted.
    log.append({'event':'vote_results' , 'content' : votes})
    log.append({'event':'vote_end'})
    if max(votes) > 1 : 
        dead_index = votes.index(max(votes))
        kill(dead_index)
        if game_end() == 1 : # to check if game is over by votes 
            return
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
        is_werewolf = 'Werewolf' in roles[inq]
        players[roles.index('Seer')]['special_actions_log'].append(f"You asked moderator that Player {inq} is Werewolf or not. the answer was : {is_werewolf}")
        players[roles.index('Seer')]['special_actions_log'].append(f"{inq} is Werewolf? : {is_werewolf}")
        log.append({'event' : 'inquiried' , 'content': {'player':inq , 'context': is_werewolf , 'reason':res}})
    if players[roles.index('Werewolf_simple')]['is_alive'] == True : 
        advice = send_message(render_game_intro(roles.index('Werewolf_simple')), render_game_report(roles.index('Werewolf_simple') , report) , "Command : send a short advice to Werewolf_leader to which player for eliminating for tonight")
        log.append({'event' : 'speech' , 'content': {'player': roles.index('Werewolf_simple'), 'context':advice}})
    
    res = send_message(render_game_intro(roles.index('Werewolf_leader')), render_game_report(roles.index('Werewolf_leader') , report) , "Command : JUST send the number of player who you want to kill for tonight. REMINDER: you must send an alive player number")
    targeted_guy = int(re.findall(r'\d+', res)[0])
    log.append({'event' : 'targeted' , 'content': {'player':targeted_guy , 'reason':res}})
    players[roles.index('Werewolf_leader')]['special_actions_log'].append(f"You have attemped to kill Player number {targeted_guy} at night.")
    if targeted_guy != healed_guy : 
        kill(targeted_guy)
    return

# main game loop

while game_end() == 0 : 
    log.append({'event' : 'cycle' , 'content':'day'})
    day()
    if game_end() != 0 : 
        break
    log.append({'event' : 'cycle' , 'content':'night'})
    night()






