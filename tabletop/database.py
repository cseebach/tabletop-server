from collections import namedtuple

import redis
import pymongo


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

        return True

    def add_actions(self, actions):
        last_id = self.db.redis.incrby("actions:"+game_id, len(actions))
        ids = range(last_id - len(actions) + 1, last_id + 1)

        for action, action_id in zip(actions, ids):
            action["action_id"] = action_id
            action["game_id"] = self.id

        self.db.mongo.actions.insert(actions)

    def add_action(self, action):
        self.add_actions([action])

    def get_actions(self, after=0, limit=1000):
        query = {"action_id":{"$gt":after}}
        fields = {"_id":False}
        result = self.db.mongo.actions.find(query, fields, limit=limit)
        return [action for action in query]

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
