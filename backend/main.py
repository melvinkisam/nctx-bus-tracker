from fastapi import FastAPI

from api_routes import router

app = FastAPI(title="NCTX Bus Tracker")
app.include_router(router)


@app.get("/")
def root():
    return {"message": "NCTX Bus Tracker API"}