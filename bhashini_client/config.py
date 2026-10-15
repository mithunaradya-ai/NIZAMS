import os

BASE_URL = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"
API_KEY = os.getenv("BHASHINI_API_KEY", "").strip()
DEFAULT_TIMEOUT = 30
DEFAULT_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": "bhashini-python-client",
}
