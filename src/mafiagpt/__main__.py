from __future__ import annotations

from mafiagpt.config import load_settings
from mafiagpt.game import Game
from mafiagpt.llm import OpenRouterClient


def main() -> None:
    settings = load_settings()
    client = OpenRouterClient(settings)
    game = Game(client=client)
    game.set_players(["simple_villager"] * 3, ["werewolf"] * 2, ["medic"], ["seer"])
    game.run_game()


if __name__ == "__main__":
    main()
