#! /usr/bin/python

import redis, md5, urllib
from flask import request
import time 
from __init__ import app

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


def showPost(postid, res):
    r = redisLink()
    post = r.hgetall("post:"+str(postid))
    if not post:
        return False
    userid = post['user_id']
    username = r.hget("user:"+str(userid), "username")
    elapsed = strElapsed(post['time'])
    userlink = "<a class=\"username\" href=\"profile.php?"+urllib.urlencode({"u":username})+"\">"+username+"</a>"
    res += '<div class="post">'+userlink+' '+post['body']+"<br>"
    res += '<i>posted '+elapsed+' ago via web</i></div>'
    return True


def showUserPosts(userid, start, count):
    r = redisLink()
    key = "timeline" if (userid == -1) else "posts:"+str(userid)
    posts = r.lrange(key, start, start+count)
    c = 0
    for p in posts:
        if(showPost(p)):
            c += 1
        if c == count:
            break
    return len(posts) == count+1    
app.jinja_env.globals['showUserPosts'] = showUserPosts


def showUserPostsWithPagination(username, userid, start, count):
    thispage = request.base_url
    nnext = start + 10
    prev = start - 10 if (start - 10) > 0 else 0
    nextlink = False
    prevlink = False
    res = ""
    u = "&" + urllib.urlencode({"u":username}) if username else ""
    if showUserPosts(userid, start, count, res):
        nextlink = "<a href=\""+thispage+"?"+urllib.urlencode({"page":nnext})+u+"\">Older posts &raquo;</a>"
    if start > 0:  
        prevlink = "<a href=\""+thispage+"?"+urllib.urlencode({"page":prev})+u+"\">&laquo; Newer posts</a>"
        prevlink = prevlink +  " | "  if nextlink else  prevlink
    if prevlink:
        res += "<div class=\"rightlink\">"+prevlink
    if nextlink:
        res += nextlink
    res += "</div>"
    return res
app.jinja_env.globals['showUserPostsWithPagination'] = showUserPostsWithPagination


def combineurl(base, param):
    return base + "?" + urllib.urlencode(param)
app.jinja_env.globals['combineurl'] = combineurl 


def get_resource_as_string(name, charset='utf-8'):
    with app.open_resource(name) as f:
        return f.read().decode(charset)
app.jinja_env.globals['get_resource_as_string'] = get_resource_as_string

