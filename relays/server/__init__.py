from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# app_settings = os.getenv('APP_SETTINGS',
#                          'project.server.config.DevelopmentConfig')
# app.config.from_object(app_settings)
app.config.from_pyfile('config/api/default.py')
# app.config.from_pyfile('config/api/%s.py' % env, silent=True)
db = SQLAlchemy(app)

from server.views import relays_blueprint, static_blueprint

app.register_blueprint(relays_blueprint)
app.register_blueprint(static_blueprint)


def launch_api():
    print('RUNNING APP')
    app.run(use_reloader=False, port=app.config['PORT'],
            host=app.config['HOST'])
