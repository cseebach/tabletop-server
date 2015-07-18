import random

from tabletop.decks import decks

class Game(object):

    def __init__(self, db_game, faction):
        self.db_game = db_game
        self.faction = faction
        self.last_action_retrieved = 0

    def add_action(self, action, source=None):
        action["faction"] = self.faction
        if not source:
            action["source"] = self.faction
        self.db_game.add_action(action)

    def create_decks(self):
        for faction in ["dryad", "gearpunk", "ice", "minotaur"]:
            self.create_deck(faction)

    def create_deck(self, faction):
        templates = []
        for template, quantity in decks[faction]:
            for i in range(quantity):
                templates.append(template)

        random.shuffle(templates)

        new_actions = []
        counter = 0
        for template in templates:
            card_id = self.faction+":"+str(counter)
            action = {"action":"addToDeck", "card":card_id, "template":template, "faction":faction, "source":"server"}
            new_actions.append(action)

        self.db_game.add_actions(new_actions)

    def get_new_actions(self):
        new_actions, total_size = self.db_game.get_actions(
            self.last_action_retrieved, exclude_source=self.faction)
        self.last_action_retrieved += total_size
        return new_actions

    @staticmethod
    def create(db, name, faction, **kwargs):
        game = db.get_game(name)
        if not game:
            game = db.new_game(name)
            game.join(faction)
            game_obj = Game(game, faction)
            game_obj.create_decks()
            return game_obj, None
        else:
            return None, "game already exists"

    @staticmethod
    def join(db, name, faction, **kwargs):
        db_game = db.get_game(name)
        if db_game:
            if db_game.join(faction):
                game = Game(db_game, faction)
                return game, None
            else:
                return None, "game exists but slot is filled"
        else:
            return None, "game does not exist"
