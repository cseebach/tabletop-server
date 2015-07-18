import socketserver
import pymongo
import json
import uuid

from tabletop import decks
from tabletop.database import Database

class Game(object):

    def __init__(self, db, game_id, faction):
        self.id = game_id
        self.faction = faction

    def add_actions(self, actions):
        for action in actions:
            action["game_id"] = self.id
        return self.db.actions.insert(actions)

    def queue_actions(self, action_ids):
        to_queue = []
        for action_id in action_ids:
            for faction in factions:
                action = {"action_id":action_id, "game_id": self.id, "faction": self.faction}

        self.db.action_queue.insert()

    def createCardsFor(self, faction):
        deck = decks[faction]
        newActions = []
        counter = 0
        for template, quantity in deck:
            for i in range(quantity):
                card_id = faction+str(counter)
                action = {"action":"newCard", "id":card_id, "data":template}
                new_actions.append(action)
        action_ids = self.add_actions(new_actions)
        self.queue_actions(action_ids)

    @staticmethod
    def create(db, name, password, faction, **kwargs):
        insert = {"name": name, "factions":[faction]}
        game_id = db.games.insert(insert)
        self.createCardsFor(faction)
        return Game(db, game_id, faction)

    @staticmethod
    def can_create(db, name, password, **kwargs):
        extant = db.games.find_one({"name":name})
        if not extant:
            return True, None
        else:
            return False, "game with that name already exists"

    @staticmethod
    def join(db, name, password, faction, **kwargs):
        extant = db.games.find_one({"name":name})
        game_id = extant["factions"].append(faction)
        db.games.save(extant)
        return Game(db, game_id, faction)

    @staticmethod
    def can_join(db, name, password, faction, **kwargs):
        extant = db.games.find_one({"name":name})
        if extant and faction not in extant["factions"]:
            return True, None
        elif not extant:
            return False, "game with that name already exists"
        elif faction in extant:
            return False, "already a player with that faction there"

class GameHandler(socketserver.StreamRequestHandler):

    def write(self, data):
        as_bytes = (json.dumps(data)+"\n").encode("utf-8")
        self.wfile.write(as_bytes)
        self.wfile.flush()
        print("written: ", data)

    def read(self):
        data = json.loads(str(self.rfile.readline().strip(), "utf-8"))
        print("receive: ", data)
        return data

    def sendNewCommands(self):
        pass

    def storeCommand(self):
        pass

    def loop(self):
        #read a ping, send out any new actions
        #or read an action, store it in db
        pass

    def join(self, name, faction, **kwargs):
        game = self.db.get_game(name)
        if game and game.join(faction):
            self.write({"action":"joined"})
            self.game = game
            print("game joined")
        else:
            self.write({"action":"joinError", "error":"no such game or that slot unavailable"})
            print("error in game joining")

    def create(self, name, faction, **kwargs):
        game = self.db.get_game(name)
        if not game:
            self.game = self.db.new_game(name)
            self.game.join(faction)
            self.write({"action":"created"})
            print("game created")
        else:
            self.writeJSON({"action":"createError", "error":"game already exists"})
            print("error in game creation")

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
