from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

router = APIRouter()


def get_visible_pokedex(request: Request) -> dict:
    """Get a list of pokemons while applying a "removing filter" per user session"""
    pokedex = request.app.state.pokedex
    deleted = request.session.get("deleted", [])
    return {name: data for name, data in pokedex.items() if name not in deleted}

def get_filtered_pokedex(request: Request, type1: str = None, type2: str = None, heavy: bool = None) -> dict:
    """Applying filters to a pokemon list"""
    pokedex = get_visible_pokedex(request)

    if type1:
        pokedex = {name: data for name, data in pokedex.items() if type1.lower() in data["types"]}
    if type2:
        pokedex = {name: data for name, data in pokedex.items() if type2.lower() in data["types"]}
    if heavy:
        pokedex = {name: data for name, data in pokedex.items() if data["weight"] > 1000}

    return pokedex

@router.get("/", summary="Get a list of pokemons")
async def get_pokemon_list(request: Request, page: int = 1, size: int = 20,
                           type1: str = None, type2: str = None, heavy: bool = None):

    """Get a pokemon list that follows 'filters' criteria"""

    # Get all visible pokemon to the user
    pokedex = get_filtered_pokedex(request, type1, type2, heavy)

    # Pagination process
    items = list(pokedex.items())
    total = len(items)
    all_pages = -(-total // size) # = math.ceil(total / size)

    tmp_page = page
    if  page < 1:
        tmp_page = 0
    if tmp_page > all_pages:
        tmp_page = all_pages

    start = (tmp_page - 1) * size
    end = start + size
    page_items = dict(items[start:end])

    return {
        "data": page_items,
        "total": total,
        "page": page,
        "size": size,
        "pages": all_pages,
    }


@router.get("/types", summary="List of all types")
async def get_types(request: Request):
    """Get a list of all pokemon types"""
    return {"data": request.app.state.types}


@router.get("/{name}", summary="Get insights of a pokemon")
async def get_pokemon(request: Request, name: str):
    """Get all stored information about a pokemon"""
    pokedex = request.app.state.pokedex
    if name not in pokedex:
        return JSONResponse(status_code=404, content={"error": f"{name} not found"})
    return {"data": {name: pokedex[name]}}


@router.get("/{name}/description")
async def get_description(request: Request, name: str):
    """ Provides a funny description for a pokemon"""
    pokedex = request.app.state.pokedex

    if name not in pokedex:
        return JSONResponse(status_code=404, content={"error": f"{name} not found"})

    if request.app.state.LLMProvider.llm is None:
        return JSONResponse(status_code=503, content={"error": "LLM not available"})

    data = pokedex[name]
    prompt = (
        f"Generate a short and funny description for {name}. "
        f"It is a {', '.join(data['types'])} type Pokémon, "
        f"weighs {data['weight'] / 10} kg and is {data['height'] / 10} m tall. "
        f"Keep it under 3 sentences, imaginative and fun."
    )

    async def safe_stream(generator):
        try:
            async for chunk in generator:
                yield chunk
        except Exception:
            yield ""

    return StreamingResponse(
        safe_stream(request.app.state.LLMProvider.stream(prompt)),
        media_type="text/plain"
    )

@router.delete("/{name}", summary="Removes a pokemon from the user selection")
async def delete_pokemon(name: str, request: Request):
    """Delete a pokemon from the user selection without affecting other users"""
    pokedex = request.app.state.pokedex
    if name not in pokedex:
        return JSONResponse(status_code=404, content={"error": f"{name} not found"})

    deleted = request.session.get("deleted", [])
    if name not in deleted:
        deleted.append(name)
        request.session["deleted"] = deleted

    return {"deleted": deleted}


@router.post("/restore", summary="Bring back all pokemons")
async def restore_all(request: Request):
    """Bring back all previously deleted pokemons from the user selection"""
    request.session["deleted"] = []
    return {"message": "All pokemons have been restored"}