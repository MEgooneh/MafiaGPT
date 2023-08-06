"""
    This is for making the log.json readable as an article in MarkDown format.
    You should pass the log.json file to the program while excuting it.
"""
import json, sys

file = sys.argv[1]
log = json.load(open(file , 'r'))

roles = {}

text = ""

def emojing_roles(role) : 
    roles = ['Medic', 'Seer', 'Villager_simple', 'Werewolf_leader', 'Werewolf_simple']
    roles_emoji = ['🩺','🔍','👤','👤','👤','😈','😈']
    return role + roles_emoji[roles.index(role)]

def results(votes) :
    s = ""
    for i in range(7) : 
        if votes[i] > 0 :
            s += f"``` Player {i} : {'+' * votes[i]} ```"
            s += '<br>'
    return s

def new_lines_quote(s) : 
    return s.replace('\n' , "<br> ")

for i in log : 
    event = i['event']
    if 'content' in i.keys() : 
        content = i['content']
    if event == 'roles' : 
        roles[content['player']] = emojing_roles(content['role'])
        text += f"""
Player *{content['player']}* is *{emojing_roles(content['role'])}*
"""
    elif event == 'cycle' : 
        text += f"""
# It's **{content}** !
"""
    elif event == 'speech' : 
        s = new_lines_quote(content['context'])
        text +=  f"""
**Player {content['player']}** ({roles[content['player']]}) : 

> {s}
"""
    elif event == 'vote_start' : 
        text += f"""
# Voting starts
"""
    elif event == 'vote_end' : 
        text += f"""
# Voting ends
"""
    elif event == 'vote_results' : 
        text += f"""
{results(content)}
"""
    elif event == 'voted' : 
        text += f"""
Player *{content['player']}* ({roles[content['player']]}) Voted to Player *{content['voted_to_player']}* ({roles[content['voted_to_player']]}).

Reason : 

> {new_lines_quote(content['reason'])}
"""
    elif event == 'healed' : 
        text += f"""
Medic decided to heal Player *{content['player']}* ({roles[content['player']]})

Reason : 

> {new_lines_quote(content['reason'])}
"""
    elif event == 'targeted' : 
        text += f"""
Werewolves decided to kill Player *{content['player']}* ({roles[content['player']]})

Reason : 

> {new_lines_quote(content['reason'])}
"""
    elif event == 'killed' : 
       text += f"""
*{content['player']}* ({roles[content['player']]}) is DEAD! 💀
"""
    elif event == 'inquiried' : 
        text += f"""
Seer decided to inquiry Player *{content['player']}* ({roles[content['player']]})

Reason : 

> {new_lines_quote(content['reason'])}

Answer : 

{content['context']}
"""
    elif event == 'notetaking' : 
        s = new_lines_quote(content['context'])
        text +=  f"""
**Player {content['player']}** ({roles[content['player']]}) is taking note for himself :  📝

> {s}
"""
    elif event == 'end' : 
        text += f"""
# Game is over! and the winner is **{i['winner']}**
"""
    text += """
---
"""


# Saving the file
with open('new.md', 'w') as file : 
    file.write(text)
print("Saved as new.md!")
