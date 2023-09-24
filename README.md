# MafiaGPT

a program that moderate a [Mafia(Werewolf)](https://en.wikipedia.org/wiki/Mafia_(party_game)) game with 7 players between GPT models.

to see communication, team work and social/logical abilities of GPT model.(it is fun and educational)

the roles are : 

- 1 Medical
- 1 Seer
- 3 Villagers
- 2 Werewolves

## Get started

install openai via pip : 
```bash
pip install openai
```

set your Openai API key as an enivronmental variable with key : OPENAI_API_KEY

- you can configure your model(Default is 'gpt-3.5-turbo') and your rate_limit and token_limit in api.py

run the "game.py"

## log.json format

every event in the game is a dictionary.

```javascript
{
  'event':"<event_name>",
  'content':"<...>"
}
```

events are : 

- roles :
```javascript
'content':{
  'player':"<player_number>"
  'role':"<role_string>"
}
```

- cycle :
```javascript
'content':"<day/night>"
```

- speech :
```javascript
'content':{
  'player':"<player_number>"
  'context':"<speech_string>"
}
```

- voted :
```javascript
'content':{
  'player':"<player_number>"
  'voted_to_player':"<player_number>"
  'reason':"<complete response>"
}
```

- vote_start :
```javascript
'content':{
  'player':"<player_number>"
  'voted_to_player':"<player_number>"
  'reason':"<complete response>"
}
```

- healed :
```javascript
'content':{
  'player':"<player_number>"
  'reason':"<complete response>"
}
```
- targeted :
```javascript
'content':{
  'player':"<player_number>"
  'reason':"<complete response>"
}
```
- killed :
```javascript
'content':{
  'player':"<player_number>"
}
```
- inquiried :
```javascript
'content':{
  'player':"<player_number>"
  'context':"<True: if player is werewolf>"
  'reason':"<complete response>"
}
```
- notetaking :
```javascript
'content':{
  'player':"<player_number>"
  'context':"<speech_string>"
}
```
- end :
```javascript
'content':{
  'winner':"<Werewolves/Villagers>"
}
```

## Prompts
- Game Introduction('/intro_prompt.txt') : rules and the role of the player
- Game Reports('/report_prompt.txt) :
    - Speeches in last round
    - Game status : alive players in seperation of the teams.
    - Players status : alivness of players based on their number
    - Agent previous SPEACIAL actions
    - Agent previous VOTES
    - Notes that have taken by the agent
- Commands('/game.py') :
    - Speak command
    - Vote command
    - targetting/healing/killing/inquiring command
      

## Tasks  

- [ ] optimizing prompts
- [ ] a web interface to play natively a log-file as an animation
- [ ] allowing a player/players to play with GPT (Probably tricky prompts will lead to game hacking.) 
- [ ] allowing more chat models or different GPT tempretures to compete 
