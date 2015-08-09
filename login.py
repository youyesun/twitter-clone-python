from __init__ import app
from flask import render_template, redirect, url_for
from forms import UsernamePasswordForm 


@app.route('/', methods=["GET", "POST"])
@app.route('/login', methods=["GET", "POST"])
def login():
    form = UsernamePasswordForm()
    if form.validate():
        print "hahah"
	return redirect(url_for('home'))
    return render_template('login.html', form=form)
