from fastapi.middleware.cors import CORSMiddleware

# To be used with (FastAPI).add_middleware(**middleware_params)
middleware_params = {
    "middleware_class": CORSMiddleware,
    "allow_origins": [
        "http://localhost",
        "http://localhost:3000",
        "https://app.schoolsyst.com",
        "https://schoolsyst.com",
        "https://ewen.works",
        "https://github.com",
    ],
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}
