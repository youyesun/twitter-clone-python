from __init__ import app
from flask import render_template, make_response, redirect, url_for, request, flash 
from forms import UsernamePasswordForm 
from twitter_clone import *


@app.route('/', methods=["GET", "POST"])
@app.route('/login', methods=["GET", "POST"])
def login():
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
                resp.set_cookie('auth', authsecret)
                return resp
            else:
                flash('Wrong password ...')
    return render_template('login.html', form=form)


@app.route('/home', methods=["GET", "POST"])
def home():
    print "hahah log in!!!"


@app.route('/logoff', methods=["GET", "POST"])
def logoff():
    if not isLoggedIn():
        resp = make_response(redirect(url_for('login')))
        return resp
    r = redisLink()
    newauthsecrect = getrand()
    userid = User['id']
    oldauthsecret = r.hget('user:'+str(userid), 'auth')
    r.hset('user:'+str(userid), 'auth', newauthsecrect)
    r.hset('auths', newauthsecrect, userid)
    r.hdel('auths', oldauthsecrect)
    resp = make_response(redirect(url_for('login')))
    return resp

