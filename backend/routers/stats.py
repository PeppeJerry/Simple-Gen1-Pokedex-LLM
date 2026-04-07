from fastapi import APIRouter, Request
from .pokemon import get_filtered_pokedex

router = APIRouter()

# GET /api/stats/averages?type1=fire&type2=&heavy=false
# Peso medio (kg) e altezza media (m) dei Pokémon visibili.
@router.get("/averages")
async def get_averages(request: Request, type1: str = None, type2: str = None, heavy: bool = None):
    pokedex = get_filtered_pokedex(request, type1, type2, heavy)

    if not pokedex:
        return {"avg_weight_kg": 0, "avg_height_m": 0, "total": 0}

    total = len(pokedex)
    avg_weight = sum(d["weight"] for d in pokedex.values()) / total / 10   # hg → kg
    avg_height = sum(d["height"] for d in pokedex.values()) / total / 10   # dm → m

    return {
        "avg_weight_kg": round(avg_weight, 1),
        "avg_height_m":  round(avg_height, 2),
        "total":         total,
    }


# GET /api/stats/top-experience?type1=fire&type2=&heavy=false
# Pokémon con la maggiore base_experience tra quelli visibili.
@router.get("/top-experience")
async def get_top_experience(request: Request, type1: str = None, type2: str = None, heavy: bool = None):
    pokedex = get_filtered_pokedex(request, type1, type2, heavy)

    if not pokedex:
        return {"name": None, "base_experience": None}

    top_name = max(pokedex, key=lambda name: pokedex[name]["base_experience"] or 0)
    top_data = pokedex[top_name]

    return {
        "name":            top_name,
        "base_experience": top_data["base_experience"],
        "sprite":          top_data["sprite"],
        "types":           top_data["types"],
    }


# GET /api/stats/types-count?type1=fire&type2=&heavy=false
# Conteggio Pokémon per tipo (un Pokémon con 2 tipi conta in entrambi).
@router.get("/types-count")
async def get_types_count(request: Request, type1: str = None, type2: str = None, heavy: bool = None):
    pokedex = get_filtered_pokedex(request, type1, type2, heavy)

    counts = {}
    for data in pokedex.values():
        for t in data["types"]:
            counts[t] = counts.get(t, 0) + 1

    counts = dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))

    return {"data": counts}
