from dotenv import load_dotenv
from app.app import init_app

load_dotenv()
app = init_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
