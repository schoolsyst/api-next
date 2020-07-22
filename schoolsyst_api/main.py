import uvicorn
from schoolsyst_api.auth import api

if __name__ == "__main__":
    uvicorn.run(api, host="0.0.0.0", port=8000)
