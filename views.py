from __init__ import app
from flask import render_template, make_response, redirect, url_for, request, flash 
from forms import * 
import twitter_clone
from twitter_clone import *
import pprint


PER_PAGE = 5

@app.route('/', methods=["GET", "POST"])
@app.route('/login', methods=["GET", "POST"])
def login():
    if isLoggedIn():
        resp = make_response(redirect(url_for('home')))
        return resp
    form = UsernamePasswordForm(request.form)
    if request.method == "POST" and form.validate():
        r = redisLink()
        userid =  r.hget('users', form.username.data)
	if not userid:
            flash('User doesn\'t exists ...')
        else:
            realpass = r.hget('user:' + userid, 'password')
            if realpass == form.password.data:
                authsecret = r.hget('user:' + userid, 'auth')
                resp = make_response(redirect(url_for('home')))
                pprint.pprint(authsecret)
                resp.set_cookie('auth', authsecret.decode('latin1'))
                return resp
            else:
                flash('Wrong password ...')
    return render_template('login.html', form=form)


@app.route('/home/', defaults={'page':0}, methods=["GET", "POST"])
@app.route('/home/page/<int:page>', methods=["GET","POST"])
def home(page):
    form = StatusForm(request.form)
    r = redisLink()
    page = 0 if page < 0 else page
    if not isLoggedIn():
	resp = make_response(redirect(url_for('login')))
        return resp
    if request.method == "POST" and form.validate():
        postid = r.incr("next_post_id")
        status = form.status.data.replace('\n', ' ')
        r.hmset("post:"+str(postid), {"user_id": twitter_clone.User['id'], "time": time.time(), "body": status})
        followers = r.zrange("followers:"+str(twitter_clone.User['id']), 0, -1)
        followers.append(twitter_clone.User['id']) 
        for f in followers:
            r.lpush("posts:"+str(f),postid)
        r.lpush("timeline",postid)
        r.ltrim("timeline", 0, 1000)       
    return render_template('home.html', form=form, r=r, User=twitter_clone.User,page=page)



@app.route('/logoff', methods=["GET", "POST"])
def logoff():
    if not isLoggedIn():
        resp = make_response(redirect(url_for('login')))
        return resp
    r = redisLink()
    newauthsecrect = getrand()
    userid = twitter_clone.User['id']
    oldauthsecret = r.hget('user:'+str(userid), 'auth')
    r.hset('user:'+str(userid), 'auth', newauthsecrect)
    r.hset('auths', newauthsecret, userid)
    r.hdel('auths', oldauthsecret)
    resp = make_response(redirect(url_for('login')))
    return resp

