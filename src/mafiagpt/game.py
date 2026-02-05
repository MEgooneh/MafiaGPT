from __future__ import annotations

from dataclasses import dataclass, field
import json
import logging
from pathlib import Path
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Iterable

from mafiagpt.llm import OpenRouterClient
from mafiagpt import prompts


@dataclass
class Player:
    id: int
    notes: str = ""
    is_alive: bool = True
    votes: list[int | None] = field(default_factory=list)
    special_actions_log: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        return f"Player {self.id}"

    def targeting(self, game: Game, command: str) -> tuple[int | None, str]:
        response = game.client.send_structured(
            prompts.game_intro(self),
            prompts.game_report(game, self),
            prompts.targeting_command(command),
        )
        data = response.require_keys(["target", "reason"])
        target = data["target"]
        reason = str(data["reason"])
        if target is None:
            return None, reason
        if isinstance(target, bool) or not isinstance(target, (int, float)):
            game.logger.warning("No valid target provided in response.")
            return None, reason
        target = int(target)
        if target not in [player.id for player in game.alive_players]:
            game.logger.warning("Targeting a wrong player")
            return None, reason
        return target, reason

    def vote(self, game: Game) -> tuple[int | None, str]:
        target, reason = self.targeting(
            game,
            "Command: send the number of the player that you want to vote for. "
            "You must not vote to yourself.",
        )
        self.votes.append(target)
        return target, reason


@dataclass
class Villager(Player):
    role: str = ""
    type: str = "villager"


@dataclass
class Werewolf(Player):
    role: str = ""
    type: str = "werewolf"
    rank: str = "normal"

    def killing(self, game: Game) -> None:
        target, reason = self.targeting(
            game,
            "Command: send the number of player who you want to kill for tonight. "
            f"Consider this advice: {game.werewolves_talks}",
        )
        if target is not None:
            game.log_submit(
                {"event": "targeted", "content": {"player": target, "reason": reason}}
            )
            player = game.get_player(target)
            if game.healed_guy is not player:
                game.kill(player)
            self.special_actions_log.append(f"you attempted to kill player {target}")

    def advicing(self, game: Game) -> None:
        _target, reason = self.targeting(
            game,
            "Command: send a short advice on which player do you suppose for eliminating "
            "tonight from villagers.",
        )
        game.log_submit(
            {"event": "speech", "content": {"player": self.id, "context": reason}}
        )
        game.add_werewolf_talk(reason)


@dataclass
class Medic(Villager):
    type: str = "medic"

    def healing(self, game: Game) -> None:
        target, reason = self.targeting(
            game,
            "Command: send the number of player who you want to heal for tonight.",
        )
        if target is not None:
            game.healed_guy = game.get_player(target)
            self.special_actions_log.append(f"You have healed Player number {target}")
            game.log_submit(
                {"event": "healed", "content": {"player": target, "reason": reason}}
            )


@dataclass
class Seer(Villager):
    type: str = "seer"

    def inquiry(self, game: Game) -> None:
        target, reason = self.targeting(
            game,
            "Command: send the number of player who you want to know is werewolf or not.",
        )
        if target is not None:
            targeted_player = game.get_player(target)
            is_werewolf = targeted_player.type == "werewolf"
            tag = "" if is_werewolf else "not"
            self.special_actions_log.append(f"Player {target} is {tag} werewolf")
            game.log_submit(
                {
                    "event": "inquiried",
                    "content": {
                        "player": target,
                        "context": is_werewolf,
                        "reason": reason,
                    },
                }
            )


class Game:
    def __init__(self, client: OpenRouterClient, game_id: int = 1) -> None:
        self.id = game_id
        self.client = client
        self.all_players: list[Player] = []
        self.alive_players: list[Player] = []
        self.dead_players: list[Player] = []
        self.report: list[str] = []
        self.votes: list[dict[int, int]] = []
        self.log: list[dict[str, Any]] = []
        self.logger = self._configure_logger()
        self._lock = threading.Lock()
        self.healed_guy: Player | None = None
        self.werewolves_talks: list[str] = []

    def _configure_logger(self) -> logging.Logger:
        logger = logging.getLogger(f"Game-{self.id}")
        logger.setLevel(logging.DEBUG)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(formatter)
        if not logger.handlers:
            logger.addHandler(console_handler)
        return logger

    def log_submit(self, data: dict[str, Any]) -> None:
        with self._lock:
            self.log.append(data)
            self.logger.info(data)

    def add_werewolf_talk(self, talk: str) -> None:
        with self._lock:
            self.werewolves_talks.append(talk)

    def set_players(
        self,
        simple_villagers_roles: Iterable[str],
        werewolves_roles: Iterable[str],
        medics_roles: Iterable[str],
        seers_roles: Iterable[str],
    ) -> None:
        simple_villagers = list(simple_villagers_roles)
        werewolves = list(werewolves_roles)
        medics = list(medics_roles)
        seers = list(seers_roles)
        shuffled_roles = simple_villagers + werewolves + medics + seers
        random.shuffle(shuffled_roles)
        for i, role in enumerate(shuffled_roles):
            if role in simple_villagers:
                self.alive_players.append(Villager(role=role, id=i))
            elif role in werewolves:
                self.alive_players.append(Werewolf(role=role, id=i))
            elif role in medics:
                self.alive_players.append(Medic(role=role, id=i))
            elif role in seers:
                self.alive_players.append(Seer(role=role, id=i))
            self.log_submit({"event": "roles", "content": {"player": i, "role": role}})
        werewolves = self.get_alive_werewolves()
        if werewolves:
            for werewolf in werewolves:
                werewolf.special_actions_log.append(
                    "you are werewolf and this is your team (they are all werewolf) : "
                    f"{werewolves}"
                )
        self.all_players = list(self.alive_players)

    def get_player(self, player_id: int) -> Player:
        return self.all_players[player_id]

    def get_alive_werewolves(self) -> list[Werewolf]:
        werewolves = [
            player for player in self.alive_players if player.type == "werewolf"
        ]
        if werewolves:
            werewolves[-1].rank = "leader"
        return werewolves

    def get_alive_medics(self) -> list[Medic]:
        return [player for player in self.alive_players if player.type == "medic"]

    def get_alive_seers(self) -> list[Seer]:
        return [player for player in self.alive_players if player.type == "seer"]

    def get_alive_villagers(self) -> list[Player]:
        return [player for player in self.alive_players if player.type != "werewolf"]

    def kill(self, player: Player) -> None:
        if player not in self.alive_players:
            self.logger.warning("Killing an already dead player! Skipped!")
            return
        self.alive_players.remove(player)
        player.is_alive = False
        self.dead_players.append(player)
        self.log_submit({"event": "killed", "content": {"player": player.id}})

    def is_game_end(self) -> bool:
        """Check that the game is over or not."""
        werewolves = self.get_alive_werewolves()
        villagers = self.get_alive_villagers()
        if len(werewolves) == len(villagers):
            self.log_submit({"event": "end", "winner": "Werewolves"})
            return True
        if not werewolves:
            self.log_submit({"event": "end", "winner": "Villagers"})
            return True
        return False

    def check_votes(self) -> None:
        votes = self.votes[-1]
        if votes and max(votes.values()) > 1:
            votes_sorted = dict(sorted(votes.items(), key=lambda item: item[1]))
            self.kill(self.get_player(list(votes_sorted.keys())[-1]))
        if self.is_game_end():
            self.save_game()

    def run_day(self) -> None:
        self.report = []
        with ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(self._generate_speech, player): player
                for player in self.alive_players
            }
            speeches = []
            for future in as_completed(futures):
                speeches.append(future.result())
        for player_id, speech in sorted(speeches, key=lambda item: item[0]):
            player = self.get_player(player_id)
            self.report.append(f"{player} opinion : {speech}")
            self.log_submit(
                {"event": "speech", "content": {"player": player_id, "context": speech}}
            )
        votes = [0] * len(self.all_players)
        self.log_submit({"event": "vote_start"})
        with ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(self._collect_vote, player): player
                for player in self.alive_players
            }
            vote_results = []
            for future in as_completed(futures):
                vote_results.append(future.result())
        for player_id, target_voted, reason in sorted(vote_results, key=lambda item: item[0]):
            player = self.get_player(player_id)
            if target_voted is not None:
                self.log_submit(
                    {
                        "event": "voted",
                        "content": {
                            "player": player.id,
                            "voted_to_player": target_voted,
                            "reason": reason,
                        },
                    }
                )
                votes[target_voted] += 1
                self.report.append(f"{player} voted to {target_voted}")
            else:
                self.logger.warning("%s skipped the voting", player)
        self.log_submit({"event": "vote_results", "content": votes})
        self.log_submit({"event": "vote_end"})
        self.votes.append(dict(enumerate(votes)))
        self.check_votes()
        with ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(self._generate_notes, player): player
                for player in self.alive_players
            }
            notes_results = []
            for future in as_completed(futures):
                notes_results.append(future.result())
        for player_id, notes in sorted(notes_results, key=lambda item: item[0]):
            player = self.get_player(player_id)
            self.log_submit(
                {"event": "notetaking", "content": {"player": player.id, "context": notes}}
            )
            player.notes = notes

    def run_night(self) -> None:
        self.healed_guy = None
        self.werewolves_talks = []
        werewolves = self.get_alive_werewolves()
        leader = next((werewolf for werewolf in werewolves if werewolf.rank == "leader"), None)
        non_leaders = [werewolf for werewolf in werewolves if werewolf.rank != "leader"]

        with ThreadPoolExecutor() as executor:
            futures = []
            for medic in self.get_alive_medics():
                futures.append(executor.submit(medic.healing, self))
            for seer in self.get_alive_seers():
                futures.append(executor.submit(seer.inquiry, self))
            for werewolf in non_leaders:
                futures.append(executor.submit(werewolf.advicing, self))
            for future in as_completed(futures):
                future.result()

        if leader:
            leader.killing(self)

    def run_game(self) -> None:
        while True:
            self.log_submit({"event": "cycle", "content": "day"})
            self.run_day()
            if self.is_game_end():
                self.save_game()
                return
            self.log_submit({"event": "cycle", "content": "night"})
            self.run_night()
            if self.is_game_end():
                self.save_game()
                return

    def save_game(self) -> None:
        records_dir = Path("records")
        records_dir.mkdir(parents=True, exist_ok=True)
        output_path = records_dir / f"game_{self.id}_log.json"
        output_path.write_text(json.dumps(self.log, indent=4))

    def _generate_speech(self, player: Player) -> tuple[int, str]:
        response = self.client.send_structured(
            prompts.game_intro(player),
            prompts.game_report(self, player),
            prompts.speech_command(),
        )
        data = response.require_keys(["speech"])
        speech = str(data["speech"]).replace("\n", " ")
        return player.id, speech

    def _collect_vote(self, player: Player) -> tuple[int, int | None, str]:
        target_voted, reason = player.vote(self)
        return player.id, target_voted, reason

    def _generate_notes(self, player: Player) -> tuple[int, str]:
        response = self.client.send_structured(
            prompts.game_intro(player),
            prompts.game_report(self, player),
            prompts.notetaking_command(),
        )
        data = response.require_keys(["notes"])
        notes = str(data["notes"])
        return player.id, notes
