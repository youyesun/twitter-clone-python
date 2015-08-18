from flask import Flask

app = Flask(__name__)
app.config.from_object('config')
app.jinja_env.add_extension('jinja2.ext.loopcontrols')
import views
