from core import game

new = game.Game()
new.set_players(["simple_villager"] * 3, ["werewolf"] * 2, ["medic"], ["seer"])
new.run_game()
