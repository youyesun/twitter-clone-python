from __init__ import app
from flask import * 
from forms import * 
import twitter_clone
from twitter_clone import *
import pprint


@app.route('/', methods=["GET", "POST"])
@app.route('/login', methods=["GET", "POST"])
def login():
    if isLoggedIn():
        return make_response(redirect(url_for('home')))
    """
    handle registration using a different approach from 
    UsernamePasswordForm instance. 
    """
    if request.method == 'POST' and 'doit' in request.form.keys():
        if request.form['username'] == "" or request.form['password'] == "" or\
        request.form['password2'] == "":
            flash('Each field of the registration form is needed!')
        elif request.form['password'] != request.form['password2']:
            flash('The two password fileds don\'t match!')
        elif not registration(request.form['username'], request.form['password']):
            flash('Username is already in use!')
        return make_response(redirect(url_for('login')))
    """
    handle log in using UsernamePasswordForm 
    """
    form = UsernamePasswordForm(request.form)
    if request.method == "POST" and 'login' in request.form.keys() and\
    form.validate():
        userid = getUserid(form.username.data)
	if not userid:
            flash('User doesn\'t exists ...')
        else:
            realpass = getPassword(userid)
            if realpass == form.password.data:
                authsecret = getAuthSecret(userid)
                resp = make_response(redirect(url_for('home')))
                resp.set_cookie('auth', authsecret.decode('latin1'))
                return resp
            else:
                flash('Wrong password ...')
    return render_template('login.html', form=form)


"""
handle GET request for getting files, e.g. images. 
"""
@app.route('/css/<path:path>')
def get_file(path):
    return send_from_directory('css', path)

 

@app.route('/home/', defaults={'page':0}, methods=["GET", "POST"])
@app.route('/home/page/<int:page>', methods=["GET","POST"])
def home(page):
    form = StatusForm(request.form)
    r = redisLink()
    page = 0 if page < 0 else page
    if not isLoggedIn():
	return make_response(redirect(url_for('login')))
    if request.method == "POST" and form.validate():
        postid = r.incr("next_post_id")
        status = form.status.data.replace('\n', ' ')
        r.hmset("post:"+str(postid), {"user_id": twitter_clone.User['id'], 
                "time": time.time(), "body": status})
        r.lpush("userposts:"+str(twitter_clone.User['id']),postid)
        followers = r.zrange("followers:"+str(twitter_clone.User['id']), 0, -1)
        followers.append(twitter_clone.User['id']) 
        for f in followers:
            r.lpush("posts:"+str(f),postid)
        r.lpush("timeline",postid)
        r.ltrim("timeline", 0, 1000)
        return make_response(redirect(url_for('home')))       
    return render_template('home.html', form=form, r=r, 
                           User=twitter_clone.User,page=page)


@app.route('/timeline/', defaults={'page':0}, methods=["GET"])
@app.route('/timeline/page/<int:page>', methods=["GET"])
def timeline(page):
    form = StatusForm(request.form)
    r = redisLink()
    page = 0 if page < 0 else page
    return render_template('timeline.html', r=r, page=page)


@app.route('/profile/', defaults={'username':None,'page':0,'f':-1}, methods=["GET","POST"])
@app.route('/profile/<string:username>/', defaults={'page':0, 'f':-1}, methods=["GET","POST"])
@app.route('/profile/<string:username>/page/<int:page>', defaults={'f':-1}, methods=["GET","POST"])
def profile(username, page, f):
    r = redisLink()
    userid = getUserid(username)
    cur_userid = getCurrentUserid()
    if not userid:
        if not isLoggedIn():
            resp = make_response(redirect(url_for('login')))
        else:
            resp = make_response(redirect(url_for('home')))
        flash('User doesn\'t exist!')
        return resp
    page = 0 if page < 0 else page
    return render_template('profile.html', r=r, cur_userid=cur_userid, userid=userid, page=page) 


@app.route('/follow/', defaults={'userid':-1,'f':-1}, methods=["GET","POST"])
@app.route('/follow/<int:userid>/', defaults={'f':-1}, methods=["GET","POST"])
@app.route('/follow/<int:userid>/<int:f>', methods=["GET","POST"])
def follow(userid, f):
    if not isLoggedIn():
        return make_response(redirect(url_for('login')))
    if not userid:
        return make_response(redirect(url_for('home')))
    r = redisLink()
    cur_userid = getCurrentUserid()
    username = getUsername(userid)
    if (f!= 0 and f!=1) or cur_userid == userid:
        return make_response(redirect('/profile/'+username))
    if f==1:
        followUser(userid, cur_userid)
    if f==0:
        unfollowUser(userid, cur_userid) 
    return make_response(redirect('profile/'+username))

"""
    r = redisLink()
    userid = getUserid(username)
    cur_userid = getCurrentUserid()
    if not userid:
        if not isLoggedIn():
            resp = make_response(redirect(url_for('login')))
        else:
            resp = make_response(redirect(url_for('home')))
        flash('User doesn\'t exist!')
        return resp
    page = 0 if page < 0 else page
    return render_template('profile.html', r=r, cur_userid=cur_userid, userid=userid, page=page)

"""


@app.route('/logoff', methods=["GET", "POST"])
def logoff():
    if not isLoggedIn():
        return make_response(redirect(url_for('login')))
    r = redisLink()
    newauthsecret = getrand()
    userid = twitter_clone.User['id']
    oldauthsecret = r.hget('user:'+str(userid), 'auth')
    r.hset('user:'+str(userid), 'auth', newauthsecret)
    r.hset('auths', newauthsecret, userid)
    r.hdel('auths', oldauthsecret)
    """
    delete User. 'try None' will not throw an Exception. Undefined var will.
    """
    del twitter_clone.User 
    return make_response(redirect(url_for('login')))

