from flask import Flask

from routes.auth import auth
from routes.panel import panel
from core.config import settings


app = Flask(__name__)
app.config["SECRET_KEY"] = settings.SECRET_KEY


app.register_blueprint(auth)
app.register_blueprint(panel)




if __name__ == "__main__":
    app.run(debug=True)