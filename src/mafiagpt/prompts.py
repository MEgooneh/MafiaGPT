def game_intro(player) -> str:
    """
    Rendering game intro (The first message in every request to api)
    consisting of the rules and the player information.
    """
    return f"""
You are a meticulous agent, you are playing Mafia party game (also known as Werewolf).
your actions must be reasonable and based on your UTILITY - that is
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
    - You are trying to convince other players that you are a villager - whether or not you really are. They need to genuinely believe your statement.
    - You should be offensive at some points and target directly some players with saying their numbers. if you are Villager and you believe someone is lying you should try to eliminate him by gathering others to vote for him.
    - You should be clear and direct and take in to account all notes you have taken before about the game and change your guesses if it's needed.
    - You should vote to someone that is alive and you want to kick him out. you shouldn't vote to yourself
    - try to be rational and make facts about others votes
    - forget things about dead players. they are not alive and shouldn't be targeted or ...
----------------
YOUR information In the game :
YOU are player number : {player.id}
YOUR role is : {player.role}"""


def game_report(game, player) -> str:
    """
    Rendering game report (The second message in every request to api)
    consisting of game status and the player special informations and what happened in the game till now.
    """
    werewolves = game.get_alive_werewolves()
    villagers = game.get_alive_villagers()
    aliveness = [
        f"{active_player} is {'ALIVE' if active_player.is_alive else 'DEAD'}"
        for active_player in (game.alive_players + game.dead_players)
    ]
    return f"""This Round speeches till now :
##############
{str(game.report)}
##############
GAME STATUS NOW :
    - alive werewolves : {len(werewolves)}
    - alive Villagers : {len(villagers)}
##############
Players Status :
    - {aliveness}
##############
YOU MUST CONSIDER this important details. They are 100% True and you can use them :
    - {player.special_actions_log}
##############
YOUR PREVIOUS NOTE for yourself :
    - {player.notes}
##############"""


def structured_output_instructions(schema: str) -> str:
    return (
        "You MUST respond with a single JSON object and nothing else. "
        f"Schema: {schema}"
    )


def speech_command() -> str:
    schema = '{"speech": "string"}'
    return f"""ATTENTION :
!!! You MUST NOT REVEAL your exact role. you can claim that you are villager(lie or true) but for example you shouldn't say : "I'm Medic"
!!! there's no needage to remind rules to others. just focus on your own game and don't repeat things.
!!! don't use repeatitive phrases. add something to the game. be short and direct. also be somehow aggressive and start targetting.
NOW IS YOUR TURN TO SPEAK TO ALIVE PLAYERS.
{structured_output_instructions(schema)}"""


def notetaking_command() -> str:
    schema = '{"notes": "string"}'
    return f"""
Your notes as your memory and your strategy:
every player has a private notebook. in each round (day and night) you can update that notes for yourself to remember for next decisions. your notebook will be only your last update and it will override. so try to summarise previous notes in new one too.
    - You should be clear and summarise important actions in the round that you think it will help you in future. it should be SHORT and don't write unneccesary things in it.
    - if you have something previously in your notebook that is not usable anymore (e.g about targeting someone that is no more alive) ignore that note and don't add it to new update.
    - ONLY you can see your notes so you don't talk to others, just create your policies for next rounds. there is no needage to show your innocent. just fix your policy for yourself.
NOW JUST SEND YOUR NEW VERSION OF NOTES.
{structured_output_instructions(schema)}"""


def targeting_command(description: str) -> str:
    schema = '{"target": "number or null", "reason": "string"}'
    return f"""{description}
If you do not want to choose a target, set "target" to null.
{structured_output_instructions(schema)}"""
