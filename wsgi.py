import os

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from main import router

DEBUG = False


def get_application() -> FastAPI:
    app = FastAPI(debug=DEBUG)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # app.include_router(api_router, prefix="/api")
    app.include_router(router, prefix="")

    return app


app = get_application()


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("HEADLESS_CHROME_PORT", 8009))
    uvicorn.run(app, port=port)
