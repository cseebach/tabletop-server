import socketserver
import logging
import datetime
import json

from tabletop.database import Database
from tabletop.game import Game

timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%d_%H-%M-%S')
logging.basicConfig(filename=timestamp+".log", level=logging.DEBUG)
logger = logging.getLogger(__name__)

class GameHandler(socketserver.StreamRequestHandler):

    def write(self, data):
        self.wfile.write((json.dumps(data)+"\n").encode("utf-8"))
        self.wfile.flush()
        if data["action"] != "newActions" or data["updates"]:
            logger.debug("written: "+repr(data))

    def read(self):
        data = json.loads(self.rfile.readline().decode("utf-8"))
        if data["action"] != "ping":    
            logger.debug("received: "+repr(data))
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

    def join(self, name, **kwargs):
        game, error = Game.join(self.db, name)
        if game:
            self.write({"action":"joined"})
            self.game = game
            self.connected = True
        else:
            self.write({"action":"joinError", "error":error})

    def create(self, name, **kwargs):
        game, error = Game.create(self.db, name)
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
    HOST, PORT = "0.0.0.0", 56789



    # Create the server, binding to localhost on port 9999
    server = ThreadedTCPServer((HOST, PORT), GameHandler)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
