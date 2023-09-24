import random, logging
from api import send_message
import json, re
from prompts import render_prompts as render



class Player():
    def __init__(self, id):
        self.notes = ""
        self.is_alive = True
        self.id = id
        self.votes = []
        self.special_actions_log = []
    def __str__(self):
        return f"Player {self.id}"
    def targeting(self, Game, command):
        res = send_message(render.game_intro(self), render.game_report(Game, self) , command +  "REMINDER: your message must include the number of player that you want to perform action on it.")
        nums_in_res = re.findall(r'\d+', res)
        if nums_in_res == [] :
            return (None, res)
        return (int(nums_in_res[0]), res)
    def vote(self, Game):
        target, reason = self.targeting(
            Game,
            "Command: just send the number of the player that you want to vote for. You must not vote to yourself. if you don't want to vote anyone just send an empty response."
        ) 
        self.votes.append(target)
        return (target, reason)
        

class Villager(Player):
    def __init__(self, role, **kwargs):
        super().__init__(**kwargs)
        self.role = role
        self.type = "villager"


class Werewolf(Player):
    def __init__(self , role, **kwargs):
        super().__init__(**kwargs)
        self.role = role
        self.type = "werewolf"
        self.rank = "normal" # it may change to leader
    def killing(self, Game):
        target, reason = self.targeting(
            Game,
            f"Command : JUST send the number of player who you want to kill for tonight. also consider this advices : {Game.werewolves_talks}"
        )
        if target:
            Game.log_submit({'event' : 'targeted' , 'content': {'player':target , 'reason':reason}})
            player = Game.get_player(target)
            if Game.healed_guy is not player:
                Game.kill(player)
            self.special_actions_log.append(f'you attemped to kill player{target}')
    def advicing(self, Game):
        target, reason = self.targeting(
            Game,
            "Command : send a short advice on which player do you suppose for eliminating at tonight from villagers."
        )
        self.log_submit({'event' : 'speech' , 'content': {'player': self.id, 'context':reason}})
        self.werewolves_talks.append(reason)

class Medic(Villager):
    def __init__(self, role, **kwargs):
        super().__init__(role, **kwargs)
        self.type = "medic"

    def healing(self, Game):
        target, reason = self.targeting(
            Game,
            "Command : send the number of player who you want to heal for tonight."
        )
        if target:
            Game.healed_guy = Game.get_player(target)
            self.special_actions_log.append(f"You have healed Player number {target}")
            Game.log_submit({'event' : 'healed' , 'content': {'player':target , 'reason':reason}})

class Seer(Villager):
    def __init__(self, role, **kwargs):
        super().__init__(role, **kwargs)
        self.type = "seer"

    def inquiry(self, Game):
        target, reason = self.targeting(
            Game,
            "Command : send the number of player who you want to know that is werewolf or not for tonight."
        )
        if target:
            targeted_player = Game.get_player(target)
            is_werewolf = targeted_player.type == "werewolf"
            tag = "" if is_werewolf else "not"
            self.special_actions_log.append(f" Player {target} is {tag} werewolf")
            Game.log_submit({'event' : 'inquiried' , 'content': {'player':target , 'context': is_werewolf , 'reason':reason}})
       
        

class Game():
    def __init__(self, id=1):
        self.id = id
        self.alive_players = []
        self.dead_players = []
        self.report = []
        self.votes = []
        self.log = []
        self.logger = self._configure_logger()
    def _configure_logger(self):
        logger = logging.getLogger(f"Game-{self.id}")
        logger.setLevel(logging.DEBUG)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)        
        return logger
    def log_submit(self, data):
        self.log.append(data)
        self.logger.info(data)
    def set_players(self, simple_villagers_roles, werewolves_roles, medics_roles, seers_roles):
        shuffled_roles = simple_villagers_roles + werewolves_roles + medics_roles + seers_roles
        random.shuffle(shuffled_roles)
        for i, player in enumerate(shuffled_roles) : 
            if player in simple_villagers_roles :
                self.alive_players.append(Villager(role=player, id=i))
            elif player in werewolves_roles:
                self.alive_players.append(Werewolf(role=player, id=i))
            elif player in medics_roles:
                self.alive_players.append(Medic(role=player, id=i))
            elif player in seers_roles:
                self.alive_players.append(Seer(role=player, id=i))
            self.log_submit({'event' : 'roles', 'content':{'player':i , 'role':player}})
        werewolves = self.get_alive_werewolves()
        for werewolf in werewolves:
            werewolf.special_actions_log.append(f"you are werewolf and this is your team (they are all werewolf) : {werewolves}")
    def get_player(self, id):
        return self.alive_players[id]
    def get_alive_werewolves(self):
        ls = list(filter(lambda player : player.type == "werewolf", self.alive_players))
        # to make sure that last werewolf will make the last decision
        ls[-1].rank = "leader"
        return ls
    def get_alive_medics(self):
        return list(filter(lambda player : player.type == "medic", self.alive_players))
    def get_alive_seers(self):
        return list(filter(lambda player : player.type == "seer", self.alive_players))
    def get_alive_villagers(self):
        return list(filter(lambda player : player.type == "villager", self.alive_players))
    def kill(self, Player):
        self.alive_players.remove(Player)
        self.dead_players.append(Player)
        self.log_submit({'event' : 'killed' , 'content': {'player':Player.id}})
        return

    

    def is_game_end(self):
        """
        Will check that the game is over or not.
        """ 
        werewolves, villagers = self.get_alive_werewolves(), self.get_alive_villagers()
        if len(werewolves) == len(villagers) :
            self.log_submit({'event':'end','winner':'Werewolves'})
            return True
        if werewolves == []: 
            self.log_submit({'event':'end','winner':'Villagers'})
            return True
        return False 

    def check_votes(self):
        # [TODO] : debugging here
        votes = self.votes[-1]
        if max(votes.values()) > 1 : 
            votes_sorted = sorted(votes.items(), key=lambda x:x[1])
            self.kill(self.alive_players[votes_sorted[-1]])
        if self.is_game_end(): # to check if game is over by votes 
            self.save_game()
        return


    def run_day(self) :
        self.report = [] 
        for Player in self.alive_players :
            res = send_message(render.game_intro(Player), render.game_report(self, Player) , render.speech_command()).replace('\n' , ' ')
            self.report.append(str(Player) + "opinion : " + res)
            self.log_submit({'event' : 'speech' , 'content': {'player':Player.id , 'context':res}})
        votes = [0]*7
        self.log_submit({'event':'vote_start'})
        for Player in self.alive_players : 
            target_voted, reason = Player.vote(self)
            if target_voted :
                self.log_submit({'event' : 'voted' , 'content': {'player':Player.id , 'voted_to_player':target_voted , 'reason':reason}})
                votes[target_voted]+=1
                self.report.append(f"{Player} Voted to {target_voted}")
            else:
                self.logger.warning(f"{Player} skipped the voting")
        self.log_submit({'event':'vote_results' , 'content' : votes})
        self.log_submit({'event':'vote_end'})
        self.votes.append(list(enumerate(votes)))
        self.check_votes()
        for Player in self.alive_players : 
            res = send_message(render.game_intro(Player), render.game_report(self, Player), render.notetaking_command())
            self.log_submit({'event' : 'notetaking' , 'content': {'player':Player.id , 'context':res}})
            Player.notes = res
        return

    def run_night(self) :
        self.healed_guy = None
        self.werewolves_talks = []
        medics, seers, werewolves = self.get_alive_medics(), self.get_alive_seers(), self.get_alive_werewolves()
        for medic in medics:
            medic.healing(self)
        for seer in seers:    
            seer.inquiry(Game)
        for werewolf in werewolves:
            if werewolf.rank == "leader":
                werewolf.killing(Game)
            else:
                werewolf.advicing(Game)
        return


    def run_game(self):
        while True: 
            self.log_submit({'event' : 'cycle' , 'content':'day'})
            self.run_day()
            if self.is_game_end() :
                self.save_game()
                return 
            self.log_submit({'event' : 'cycle' , 'content':'night'})
            self.run_night()
            if self.is_game_end() :
                self.save_game()
                return
    def save_game(self):
        json.dump(self.log , open(f'records/game_{self.id}_log.json' , 'w') , indent=4)
    
        











