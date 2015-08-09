from wtforms import Form, TextField, BooleanField, PasswordField, validators 

class UsernamePasswordForm(Form):
    username = TextField('Username', [validators.Required()])
    password = PasswordField('Password', [validators.Required()])
    remember_me = BooleanField('remember_me', default=False)
