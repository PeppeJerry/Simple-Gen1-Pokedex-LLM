# Pokédex — First Generation

A fullstack web application that fetches, processes and displays data for all 151 first-generation Pokémon using the [PokéAPI](https://pokeapi.co). Built with **FastAPI** (Python) and **HTML/CSS/JS** with Tailwind CSS.

---

## Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
- [API Reference](#api-reference)
- [Features](#features)
- [Design Decisions](#design-decisions)
- [Future development](#future-development)

---

## Overview

The application loads all 151 first-generation Pokémon at server startup — fetching their details concurrently from the PokéAPI — and stores them in memory. All subsequent requests are served directly from memory with no external API calls, ensuring fast response times.

Users can filter, paginate, and delete Pokémon from their view. Deletions are session-based: each user maintains their own independent state without affecting others. All statistics update dynamically to reflect the current filtered and visible dataset.

---

## Project Structure

```
pokedex-app/
├── .env                        # Environment variables
├── .gitignore
├── setup.py                    # It is needed if "SECRET_KEY" has not been generated inside .env
├── README.md
├── docker-compose.yml
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                 # FastAPI Main App
│   └── routers/
│       ├── __init__.py
│       ├── pokemon.py          # Pokemon API
│       ├── stats.py            # Statistics API
│       └── views.py            # Frontend router (Jinja2)
│
└── frontend/
    ├── index.html              # UI (desktop & mobile)
    └── static/
        ├── index.js
        └── favicon.png
```

---

## Tech Stack

| Layer | Technology                                    |
|-------|-----------------------------------------------|
| Backend | Python 3.12, FastAPI, Uvicorn                 |
| HTTP Client | httpx (async)                                 |
| Sessions | Starlette `SessionMiddleware` |
| Templating | Jinja2                                        |
| Frontend | HTML, Tailwind CSS, Javascript                |
| Infrastructure | Docker                                        |

---

## Architecture

### Data loading — lifespan pattern

All external API calls happen **once at server startup** inside FastAPI's `lifespan` context manager. The server does not accept requests until the data is fully loaded.

```
Server startup
      ↓
app.lifespan():     ← fetch 151 Pokémon concurrently
                    ← fetch all type concurrently
      ↓
app.state.pokedex   ← immutable, shared across all requests
app.state.types     ← { name: icon_url } (Generation 3 icons)
      ↓
app.state.llm (Opt) ← load a LLM (ollama, OpenAI, Anthropic)
      ↓
Server ready
```

### Session-based deletion

`app.state.pokedex` is never mutated. Deletions are stored per-user in a signed cookie session (`{"deleted": ["bulbasaur", ...]}`). Every endpoint that returns Pokémon data applies the session filter before responding.

```
GET /api/pokemon/
      ↓
get_visible_pokedex()       ← excludes session["deleted"] per user session
      ↓
apply type / weight filters ← type1, type2, heavy
      ↓
paginate and return         
```

The same filter chain (`get_filtered_pokedex`) is imported by `stats.py`, ensuring statistics always match the visible list.

### Frontend — no page reloads

The UI is a single HTML page. All data is fetched via `fetch()` calls to the backend API. Pagination, filtering, deletion and statistics updates all happen without reloading the page. On page load, type icons and the first page of Pokémon are fetched in parallel.

---

## Getting Started

### Prerequisites

These are the required technologies used in this project.

| Tool | Download |
|------|---------|
| Docker Desktop | https://www.docker.com/products/docker-desktop |

- The user may use any compatible dockerization available.

- Python is **not required** on the host machine.

### 1. Clone the repository

```
git clone https://github.com/PeppeJerry/Simple-Gen1-Pokedex-LLM.git
cd pokedex-app
```

### 2. Generate the environment file

```
python setup.py
```

This creates a `.env` file in the project root with a securely generated `SECRET_KEY`. The script is idempotent: if `.env` already exists and contains `SECRET_KEY`, it does nothing.

### 3. Start the application

```
docker compose up --build
```

The first run downloads base images and installs dependencies — this may take a few minutes. Subsequent starts are immediate.

### 4. Open the application

| URL | Description                                |
|-----|--------------------------------------------|
| http://localhost:8000 | Web Application                            |
| http://localhost:8000/docs | Swagger UI — interactive API documentation |

### 5. Stop the application

```
docker compose down
```

---

## API Reference

### Pokémon

| Method | Endpoint | Description                                                                              |
|--------|----------|------------------------------------------------------------------------------------------|
| `GET` | `/api/pokemon/` | Paginated Pokémon list. Supports `page`, `size`, `type1`, `type2`, `heavy` query params. |
| `GET` | `/api/pokemon/types` | All available types with their icon URLs.                                                |
| `GET` | `/api/pokemon/{name}` | Single Pokémon detail by name. Supports `name` parameter.                                |
| `GET` | `/api/pokemon/{name}/description` | Gives a _funny_ description generated by a LLM model.                                    |
| `DELETE` | `/api/pokemon/{name}` | Remove a Pokémon from the current user's session view. Supports `name` parameter.                                  |
| `POST` | `/api/pokemon/restore` | Restore all deleted Pokémon for the current user.                                        |

### Statistics

All statistics endpoints accept the same filter query params as the list endpoint (`type1`, `type2`, `heavy`) so statistics always reflect the currently visible dataset.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/stats/averages` | Average weight (kg) and height (m) of visible Pokémon. Supports  `type1`, `type2`, `heavy` query params.|
| `GET` | `/api/stats/top-experience` | Pokémon with the highest `base_experience`. Supports  `type1`, `type2`, `heavy` query params.|
| `GET` | `/api/stats/types-count` | Count of Pokémon per type, sorted descending. Supports  `type1`, `type2`, `heavy` query params.|

### Query parameters

| Parameter | Type   | Description                                                      |
|-----------|--------|------------------------------------------------------------------|
| `name`    | string | Name of the _pokemon_ (e.g. `bulbasaur`, `Mewtwo`)               |
| `page`    | int    | Page number, default `1`                                         |
| `size`    | int    | Items per page, default `20`                                     |
| `type1`   | string | Filter by primary type (e.g. `fire`, `water`)                    |
| `type2`   | string | Filter by secondary type — combined with `type1` using AND logic |
| `heavy`   | bool   | If `true`, only returns Pokémon weighing more than 100 kg        |

---

## Features

**Core requirements**
- Fetches and displays all 151 first-generation Pokémon
- Average weight and height statistics
- Pokémon with highest base experience
- Pokémon count per type
- List of Pokémon weighing more than 100 kg
- Paginated table (20 per page on UI)
- Per-row delete button
- Filter by type (up to 2 types simultaneously)
- Responsive interface (Optimized both for desktop and mobile)

**Additional**
- Type icons fetched from PokéAPI sprites (Generation 3)
- All statistics update dynamically on filters or deletions change
- Session-based deletion: each user's view is independent
- Concurrent data loading at startup via `asyncio.gather`
- Interactive API documentation at `/docs`

---

## Design Decisions

**Why load all data at startup?**

Pokémon data is static, therefore, it never changes. Fetching 151 Pokémon on every request would add latency per call.
Loading once at startup and keeping data in memory makes every request instant.
A database may be required in the future by increasing the number of pokemons.

**Why session-based deletion instead of client-side state?**
Client-side deletion (removing from a JS array) would be simpler, but resetting on page reload is often unexpected UX.
Session-based deletion persists across page reloads within the same browser session, while remaining completely isolated per user.
A `Restore` button is added to reset every deleting action done.

**Why `get_filtered_pokedex` is shared between routers?**
Both `pokemon.py` and `stats.py` need to apply the same filter logic. Extracting it into a plain Python function (not an endpoint) in `pokemon.py` and importing it in `stats.py` ensures the two are always in sync. If a new filter type is added, it only needs to be added in one place.

## Future development

1) Database/Cache system to ensure data persists even if PokeAPI fails.
2) Login system to allow users to keep preferences across session change.
3) Implement a better UI menu for deleted pokemon (Restore of a single pokemon instead of every pokemon)