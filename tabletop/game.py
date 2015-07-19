import random

from tabletop.decks import decks

class Game(object):

    def __init__(self, db_game, client_id):
        self.db_game = db_game
        self.client_id = client_id
        self.last_action_retrieved = 0

    def add_action(self, action, source=None):
        if not source:
            action["source"] = self.client_id
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
            counter += 1
            card_id = faction+":"+str(counter)
            action = {"action":"addToDeck", "card":card_id, "template":template, "faction":faction, "source":"server"}
            new_actions.append(action)

        self.db_game.add_actions(new_actions)

    def get_new_actions(self):
        new_actions, total_size = self.db_game.get_actions(
            self.last_action_retrieved, exclude_source=self.client_id)
        self.last_action_retrieved += total_size
        return new_actions

    @staticmethod
    def create(db, name, **kwargs):
        game = db.get_game(name)
        if not game:
            game = db.new_game(name)
            game_obj = Game(game, db.new_client())
            game_obj.create_decks()
            return game_obj, None
        else:
            return None, "game already exists"

    @staticmethod
    def join(db, name, **kwargs):
        db_game = db.get_game(name)
        if db_game:
            game = Game(db_game, db.new_client())
            return game, None
        else:
            return None, "game does not exist"
