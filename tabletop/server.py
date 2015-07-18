import socketserver
import random
import json

from tabletop import decks
from tabletop.database import Database

class Game(object):

    def __init__(self, db_game, faction):
        self.db_game = db_game
        self.faction = faction
        self.last_action_retrieved = 0

    def add_action(self, action):
        action["faction"] = self.faction
        self.db_game.add_action(action)

    def create_deck(self):
        templates = []
        for template, quantity in decks.decks[self.faction]:
            for i in range(quantity):
                templates.append(template)

        random.shuffle(templates)

        new_actions = []
        counter = 0
        for template in templates:
            card_id = self.faction+":"+str(counter)
            action = {"action":"addToDeck", "card":card_id, "template":template, "faction":self.faction}
            new_actions.append(action)

        self.db_game.add_actions(new_actions)

    def get_new_actions(self):
        new_actions = self.db_game.get_actions(self.last_action_retrieved)
        self.last_action_retrieved += len(new_actions)
        return new_actions

    @staticmethod
    def create(db, name, faction, **kwargs):
        game = db.get_game(name)
        if not game:
            game = db.new_game(name)
            game.join(faction)
            game_obj = Game(game, faction)
            game_obj.create_deck()
            return game_obj, None
        else:
            return None, "game already exists"

    @staticmethod
    def join(db, name, faction, **kwargs):
        db_game = db.get_game(name)
        if db_game:
            if db_game.join(faction):
                game = Game(db_game, faction)
                game.create_deck()
                return game, None
            else:
                return None, "game exists but slot is filled"
        else:
            return None, "game does not exist"

class GameHandler(socketserver.StreamRequestHandler):

    def write(self, data):
        as_bytes = (json.dumps(data)+"\n").encode("utf-8")
        self.wfile.write(as_bytes)
        self.wfile.flush()
        print("written: ", data)

    def read(self):
        data = json.loads(str(self.rfile.readline().strip(), "utf-8"))
        if data["action"] != "ping":
            print("receive: ", data)
        return data

    def respond_to_ping(self):
        new_actions = self.game.get_new_actions()
        self.write({"action":"newActions", "updates":new_actions})

    def loop(self):
        while True:
            action = self.read()
            if action["action"] == "ping":
                self.respond_to_ping()
            else:
                self.game.add_action(action)

    def join(self, name, faction, **kwargs):
        game, error = Game.join(self.db, name, faction)
        if game:
            self.write({"action":"joined"})
            self.game = game
            self.connected = True
        else:
            self.write({"action":"joinError", "error":error})

    def create(self, name, faction, **kwargs):
        game, error = Game.create(self.db, name, faction)
        if game:
            self.write({"action":"created"})
            self.game = game
            self.connected = True
        else:
            self.write({"action":"createError", "error":error})

    def joinOrCreate(self):
        while not self.connected:
            action = self.read()
            if action["action"] == "joinGame":
                self.join(**action)
            elif action["action"] == "createGame":
                self.create(**action)

    def handle(self):
        self.db = Database()

        self.connected = False
        self.joinOrCreate()
        self.loop()

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

if __name__ == "__main__":
    HOST, PORT = "localhost", 56789



    # Create the server, binding to localhost on port 9999
    server = ThreadedTCPServer((HOST, PORT), GameHandler)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
