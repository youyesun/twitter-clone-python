#! /usr/bin/python

import redis, md5, urllib
from flask import request
import time 
from __init__ import app
import pprint
import unicodedata
import base64


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


def registration(username, userpass):
    r = redisLink()
    if r.hget("users",username):
        return False
    userid = r.incr("next_user_id")
    print str(userid)
    authsecret = getrand()
    r.hset("users", username, userid)
    r.hmset("user:"+str(userid), {"username":username,"password":userpass,
            "auth":authsecret})
    r.hset("auths", authsecret, userid)
    return True


def followUser(userid, followerid):
    r = redisLink()
    t = time.time()
    r.zadd("followers:"+str(userid), t, followerid)
    r.zadd("following:"+str(followerid), t, userid)


def unfollowUser(userid, followerid):
    r = redisLink()
    r.zrem("followers:"+str(userid), followerid)
    r.zrem("following:"+str(followerid), userid)


def isLoggedIn():
    global User
    try:
        User
    except NameError:
        try:
            request.cookies['auth']
        except KeyError:
            print "cookie missed"
            return False
        else:
            r = redisLink()
            authcookie = request.cookies['auth']
            """
            Internally Unicode is exclusively used for text except 
            for literal strings with only ASCII character points.
            User secret is 16-byte string which may contain non-ASCII chars.
            """
            userid = r.hget('auths', authcookie.encode('latin1'))
            storedsecret = r.hget('user:'+str(userid), "auth")
            if userid:
                if storedsecret != authcookie.encode('latin1'):
                    return False
                loadUserInfo(userid)
                return True      
    else:
        return True
app.jinja_env.globals['isLoggedIn'] = isLoggedIn


def resetUserAuthSecret():
    r = redisLink()
    newauthsecret = getrand()
    userid = getCurrentUserid()
    oldauthsecret = r.hget('user:'+str(userid), 'auth')
    r.hset('user:'+str(userid), 'auth', newauthsecret)
    r.hset('auths', newauthsecret, userid)
    r.hdel('auths', oldauthsecret)
    

def getUsername(userid):
    r = redisLink()
    return r.hget("user:"+str(userid), "username")


def getUserid(username):
    r = redisLink()
    return r.hget('users', username)


def getCurrentUserid():
    global User
    try:
        return User['id']
    except Exception as e:
        return -1 


def getPassword(userid):
    r = redisLink()
    return r.hget('user:' + userid, 'password')


def getAuthSecret(userid):
    r = redisLink()
    return r.hget('user:' + userid, 'auth')


def post(body):
    r = redisLink()
    postid = r.incr("next_post_id")
    cur_userid = getCurrentUserid()
    r.hmset("post:"+str(postid), {"user_id": cur_userid, "time": time.time(), 
            "body": body})
    r.lpush("userposts:"+str(cur_userid),postid)
    followers = r.zrange("followers:"+str(cur_userid), 0, -1)
    followers.append(cur_userid)
    for f in followers:
        r.lpush("posts:"+str(f),postid)
    r.lpush("timeline",postid)
    r.ltrim("timeline", 0, 1000)


def reply(postid, body):
    r = redisLink()
    replyid = r.incr("next_reply_id")
    cur_userid = getCurrentUserid()
    r.hmset("reply:"+str(replyid), {"user_id": cur_userid, "time": time.time(), 
            "body": body})
    r.lpush("replys:"+str(postid),replyid)
 

def loadUserInfo(userid):
    global User
    r = redisLink()
    User = dict()
    User['id'] = userid
    User['username'] = r.hget('user:'+str(userid), 'username')
    return True


def deleteUserInfo():
    global User
    del User


def strElapsed(t):
    d = int(time.time() - float(t))
    if d < 60: 
        return str(d)+" seconds"
    if d < 3600: 
        m = (int)(d/60)
        return str(m)+" minute"+("s" if m > 1 else "")
    if d < 3600*24:
        h = (int)(d/3600)
        return str(h)+" hour"+("s" if h > 1 else "")
    d = (int)(d/(3600*24))
    return str(d)+" day"+("s" if d > 1 else "")
app.jinja_env.globals['strElapsed'] = strElapsed


def combineurl(base, param):
    return base + "?" + urllib.urlencode(param)
app.jinja_env.globals['combineurl'] = combineurl 


def get_resource_as_string(name, charset='utf-8'):
    with app.open_resource(name) as f:
        return f.read().decode(charset)
app.jinja_env.globals['get_resource_as_string'] = get_resource_as_string

