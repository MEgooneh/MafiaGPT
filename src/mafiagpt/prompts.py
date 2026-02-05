def game_intro(player) -> str:
    """
    Rendering game intro (The first message in every request to api)
    consisting of the rules and the player information.
    """
    return f"""
You are a meticulous agent playing the Mafia party game (Werewolf).

## Objective
- Villagers: find werewolves and eliminate them through votes.
- Werewolves: survive, mislead, and eliminate villagers at night.

## Players & Roles
There are 7 players, numbered 0 through 6.
Roles:
- Villagers: 3x Villager_simple (no power), 1x Medic (heal one player at night),
  1x Seer (learn if a player is a werewolf at night).
- Werewolves: 1x Werewolf_leader (final kill decision), 1x Werewolf_simple (advice).

## Behavior Guidelines
- Be concise, direct, and persuasive.
- Base your decisions on the current round report and your notes.
- Make concrete accusations with player numbers when appropriate.
- Do not target dead players; never vote for yourself.
- Do NOT reveal your exact role. You may claim villager, but never say "I'm Medic/Seer".

## Your Role
You are player {player.id}.
Your role is: {player.role}.
"""


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
    return f"""## Round Report
Speeches so far:
{str(game.report)}

## Game Status
- Alive werewolves: {len(werewolves)}
- Alive villagers: {len(villagers)}

## Players Status
- {aliveness}

## Confirmed Private Facts (100% true)
- {player.special_actions_log}

## Your Previous Notes
- {player.notes}
"""


def structured_output_instructions(schema: str) -> str:
    return (
        "You MUST respond with a single JSON object and nothing else. "
        "Do not wrap in markdown or add extra keys. "
        f"Schema: {schema}"
    )


def speech_command() -> str:
    schema = '{"speech": "string"}'
    return f"""## Day Speech
Speak to all alive players.
- Be short, direct, and persuasive.
- Make at least one concrete accusation or defense using player numbers.
- Do not repeat the rules; add new signal or analysis.
- Do NOT reveal your exact role (never say "I'm Medic/Seer").
Now produce your speech.
{structured_output_instructions(schema)}"""


def notetaking_command() -> str:
    schema = '{"notes": "string"}'
    return f"""
## Private Notes
Update your personal notebook for future decisions.
- Keep it short and factual.
- Remove obsolete info (dead players, disproven theories).
- Include suspicions, alliances, and key vote patterns.
Now provide the new notes.
{structured_output_instructions(schema)}"""


def targeting_command(description: str) -> str:
    schema = '{"target": "number or null", "reason": "string"}'
    return f"""## Target Selection
{description}
If you do not want to choose a target, set "target" to null.
Provide a concise reason.
{structured_output_instructions(schema)}"""
