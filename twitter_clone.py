#! /usr/bin/python

import redis, md5
from flask import request


def getrand():
    with open("/dev/urandom", "r") as fd:
        data = fd.readline()
        m = md5.new()
        m.update(data)
        return m.digest()
 


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


def isLoggedIn():
    global User
    try:
        User
    except NameError:
        try:
            request.cookies['auth']
        except KeyError:
            return False
        else:
            r = redisLink()
            authcookie = request.cookies['auth']
            userid = r.hget('auths', authcookie)
            if userid:
                if r.hget('user:'+str(userid), "auth") != authcookie:
                    return False
                loadUserInfo(userid)
                return True      
    else:
        return True


def loadUserInfo(userid):
    global User
    r = redisLink()
    User = dict()
    User['id'] = userid
    User['username'] = r.hget('user:'+str(userid), 'username')
    return True






