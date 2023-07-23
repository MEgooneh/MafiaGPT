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
}
```
- healed :
```javascript
'content':{
  'player':"<player_number>"
}
```
- targeted :
```javascript
'content':{
  'player':"<player_number>"
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
  'result':"<True: if player is werewolf>"
}
```


## Tasks  

- [ ] optimizing prompts
- [ ] a web interface to play natively a log-file as an animation
- [ ] allowing a player/players to play with GPT (Probably tricky prompts will lead to game hacking.) 
- [ ] allowing more chat models or different GPT tempretures to compete 
