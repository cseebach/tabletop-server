from collections import namedtuple

import redis
import pymongo

class DatabaseGameActions(object):

    def add(actions):
        pass

    def retrieve_new():
        pass


class DatabaseGame(object):

    def __init__(self, db, game_id):
        self.db = db
        self.id = game_id

    @staticmethod
    def new(db, name):
        game_id = str(db.mongo.games.insert({"name":name}))
        return DatabaseGame(db, game_id)

    def join(self, faction):
        key = "players:"+self.id
        already_there = self.db.redis.sismember(key, faction)
        if already_there:
            return False

        added = self.db.redis.sadd(key, faction)
        if not added:
            return False

        self.faction = faction
        return True

class Database(object):

    def __init__(self):
        self._mongo_client = pymongo.MongoClient()

        self.mongo = self._mongo_client.tabletop
        self.redis = redis.StrictRedis(host='localhost', port=6379, db=0)

    #may not need to make public
    # def getNewActionNumbers(game_id, size=1):
    #     result = self.redis.incrby("actions:"+game_id, size)
    #     return list(range(result - size + 1, result + 1))

    def new_game(self, name):
        return DatabaseGame.new(self, name)

    def get_game(self, name):
        game = self.mongo.games.find_one({"name":name})
        if game:
            return DatabaseGame(self, str(game["_id"]))
