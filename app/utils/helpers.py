import json
from pathlib import Path
from starlette.requests import Request
from starlette.responses import JSONResponse


# directory containing json files (one level up from app/)
DATA_DIR = Path(__file__).parent.parent.joinpath("data")


def _load_json(name: str):
    try:
        p = DATA_DIR.joinpath(name)
        with p.open() as f:
            return json.load(f)
    except Exception:
        return []


def _save_json(name: str, data):
    try:
        p = DATA_DIR.joinpath(name)
        with p.open("w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


# load data once and export
DATA = _load_json("data.json")


def _find_post_index(post_id: int):
    for i, post in enumerate(DATA):
        if post.get("id") == post_id:
            return i
    return None


class AppException(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.detail)


async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )
