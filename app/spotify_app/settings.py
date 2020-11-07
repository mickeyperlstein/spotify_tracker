# settings.py
from dotenv import load_dotenv

load_dotenv()

# OR, the same with increased verbosity
load_dotenv(verbose=True)

redis_credentials = {"password": "password123"}
