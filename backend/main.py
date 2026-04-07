from contextlib import asynccontextmanager
from fastapi import FastAPI
from routers import pokemon, stats, views
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
import asyncio
import httpx
import os
from dotenv import load_dotenv
import uvicorn
from llm import LLMProvider

# env variables
dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path)

async def fetch_gen1pokemon():
    """ Fetches every Pokémon of the first gen"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("https://pokeapi.co/api/v2/pokemon?limit=151")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"Error fetching Gen 1 Pokémon: {e}")
            return None

async def fetch_pokemon(client: httpx.AsyncClient, url: str):
    """Fetches a single Pokémon data"""
    try:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        print(f"Error fetching Pokémon at {url}: {e}")
        return None

async def fetch_type(client: httpx.AsyncClient, url: str):
    """Fetches a single type's details."""
    try:
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()
        icon = data["sprites"]["generation-iii"]["emerald"]["name_icon"]
        return icon
    except (httpx.HTTPError, KeyError):
        return None

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting lifespan")
    print("Downloading...")
    pokemons = await fetch_gen1pokemon()

    app.state.pokedex = {}
    app.state.types = {}

    async with httpx.AsyncClient() as client:
        print("Fetching individual Pokémon data concurrently...")

        tasks = [fetch_pokemon(client, pokemon['url']) for pokemon in pokemons['results']]
        results = await asyncio.gather(*tasks)
        for data in results:
            if data:
                name = data["name"]
                app.state.pokedex[name] = {
                    "base_experience": data["base_experience"],
                    "sprite": data["sprites"]["front_default"],
                    "types": [t["type"]["name"] for t in data["types"]],
                    "weight": data["weight"],
                    "height": data["height"],
                }

        print("Fetching types...")
        response = await client.get("https://pokeapi.co/api/v2/type/")
        response.raise_for_status()
        types = response.json()
        types = {t["name"]: t["url"] for t in types["results"]}

        names = list(types.keys())
        type_tasks = [fetch_type(client, url) for url in types.values()]
        type_results = await asyncio.gather(*type_tasks)

        app.state.types = {
            name: icon
            for name, icon in zip(names, type_results)
            if icon
        }
    print("Download finished!")

    print("Loading LLM...")
    app.state.LLMProvider = LLMProvider(provider=os.getenv("LLM_PROVIDER"))

    # Not being able to load the LLM should not be a reason not to load the whole application
    print("LLM loaded!" if app.state.LLMProvider.llm else "LLM not loaded")

    yield

    pass

secret_key = os.getenv("SECRET_KEY")
if not secret_key:
    raise RuntimeError("SECRET_KEY missing. It is required to run setup.py")

app = FastAPI(title="Pokedex_API", lifespan=lifespan)

# Frontend dependencies
app.mount("/static", StaticFiles(directory=os.getenv("FRONTEND_FOLDER", "../frontend/static")), name="static")

# Needed to handle sessions
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY"),
)

# Router
app.include_router(pokemon.router, prefix="/api/pokemon", tags=["Pokemon"])
app.include_router(stats.router, prefix="/api/stats", tags=["Stats"])
app.include_router(views.router, tags=["Views"])

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
