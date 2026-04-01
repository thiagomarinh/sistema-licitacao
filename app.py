from flask import Flask
from routes.main import main_bp
from routes.api import api_bp
from routes.export import export_bp

app = Flask(__name__)

app.register_blueprint(main_bp)
app.register_blueprint(api_bp)
app.register_blueprint(export_bp)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
