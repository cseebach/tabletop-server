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
        last_id = self.db.redis.incrby("actions:"+self.id, len(actions))
        ids = range(last_id - len(actions) + 1, last_id + 1)

        for action, action_id in zip(actions, ids):
            action["action_id"] = action_id
            action["game_id"] = self.id

        self.db.mongo.actions.insert(actions)

    def add_action(self, action):
        self.add_actions([action])

    def get_actions(self, after, limit=1000, exclude_source=None):
        query = {"action_id":{"$gt":after}, "game_id":self.id}
        fields = {"_id":False}
        results = self.db.mongo.actions.find(query, fields, limit=limit)
        results = [action for action in results]
        total_size = len(results)
        if exclude_source:
            results = [action for action in results if action["source"] != exclude_source]
        return results, total_size

class Database(object):

    def __init__(self):
        self._mongo_client = pymongo.MongoClient()

        self.mongo = self._mongo_client.tabletop
        self.redis = redis.StrictRedis(host='localhost', port=6379, db=0)

    def new_game(self, name):
        return DatabaseGame.new(self, name)

    def get_game(self, name):
        game = self.mongo.games.find_one({"name":name})
        if game:
            return DatabaseGame(self, str(game["_id"]))
