#! /usr/bin/python

import redis

def static_vars(**kwargs):
    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func
    return decorate


@static_vars(r=False)
def redisLink():
    if redisLink.r:
        return redisLink.r
    redisLink.r = redis.StrictRedis(host='localhost', port=6379, db=0)
    return redisLink.r


