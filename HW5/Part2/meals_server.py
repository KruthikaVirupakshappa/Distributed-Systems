import logging
import sys

import httpx
from mcp.server.fastmcp import FastMCP


API_BASE_URL = "https://www.themealdb.com/api/json/v1/1"
DEFAULT_TIMEOUT = 20.0


logger = logging.getLogger("meals_mcp_server")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.handlers = [handler]
logger.propagate = False


mcp = FastMCP("meals")


def _validate_limit(limit, min_value=1, max_value=25):
    if isinstance(limit, str):
        limit = limit.strip()
        if not limit:
            raise ValueError("limit must be an integer")
        try:
            limit = int(limit)
        except ValueError as exc:
            raise ValueError("limit must be an integer") from exc

    if not isinstance(limit, int):
        raise ValueError("limit must be an integer")
    if limit < min_value or limit > max_value:
        raise ValueError(f"limit must be between {min_value} and {max_value}")
    return limit


def _get_json(endpoint, params=None):
    url = f"{API_BASE_URL}/{endpoint}"
    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as exc:
        logger.exception("HTTP request failed for %s", url)
        raise RuntimeError(f"Network/API error while calling TheMealDB: {exc}") from exc
    except ValueError as exc:
        logger.exception("Invalid JSON response from %s", url)
        raise RuntimeError(f"Invalid JSON received from TheMealDB: {exc}") from exc


def _extract_ingredients(meal):
    ingredients = []

    for index in range(1, 21):
        ingredient = (meal.get(f"strIngredient{index}") or "").strip()
        measure = (meal.get(f"strMeasure{index}") or "").strip()

        if ingredient:
            ingredients.append({"name": ingredient, "measure": measure})

    return ingredients


def _normalize_meal_details(meal):
    return {
        "id": meal.get("idMeal", ""),
        "name": meal.get("strMeal", ""),
        "category": meal.get("strCategory", ""),
        "area": meal.get("strArea", ""),
        "instructions": meal.get("strInstructions", ""),
        "image": meal.get("strMealThumb", ""),
        "source": meal.get("strSource", ""),
        "youtube": meal.get("strYoutube", ""),
        "ingredients": _extract_ingredients(meal),
    }


@mcp.tool()
def search_meals_by_name(query, limit=5):
    """
    Search meals by name.

    Input:
    - query: str
    - limit: int (1-25)

    Output:
    - list of { id, name, area, category, thumb }
    - if no results: {"message": "no matches", "items": []}
    """
    if not query or not query.strip():
        raise ValueError("query cannot be empty")

    limit = _validate_limit(limit)
    payload = _get_json("search.php", params={"s": query.strip()})
    meals = payload.get("meals")

    if meals is None:
        return {"message": "no matches", "items": []}

    results = [
        {
            "id": meal.get("idMeal", ""),
            "name": meal.get("strMeal", ""),
            "area": meal.get("strArea", ""),
            "category": meal.get("strCategory", ""),
            "thumb": meal.get("strMealThumb", ""),
        }
        for meal in meals[:limit]
    ]

    return results


@mcp.tool()
def meals_by_ingredient(ingredient, limit=12):
    """
    Search meals by main ingredient.

    Input:
    - ingredient: str
    - limit: int (1-25)

    Output:
    - list of { id, name, thumb }
    - if no results: {"message": "no matches", "items": []}
    """
    if not ingredient or not ingredient.strip():
        raise ValueError("ingredient cannot be empty")

    limit = _validate_limit(limit)
    payload = _get_json("filter.php", params={"i": ingredient.strip()})
    meals = payload.get("meals")

    if meals is None:
        return {"message": "no matches", "items": []}

    results = [
        {
            "id": meal.get("idMeal", ""),
            "name": meal.get("strMeal", ""),
            "thumb": meal.get("strMealThumb", ""),
        }
        for meal in meals[:limit]
    ]

    return results


@mcp.tool()
def meal_details(id):
    """
    Lookup meal details by id.

    Input:
    - id: str | int

    Output:
    - { id, name, category, area, instructions, image, source, youtube,
        ingredients: [{name, measure}] }
    - if no result: {"message": "no matches", "item": {}}
    """
    meal_id = str(id).strip()
    if not meal_id:
        raise ValueError("id cannot be empty")

    payload = _get_json("lookup.php", params={"i": meal_id})
    meals = payload.get("meals")

    if meals is None:
        return {"message": "no matches", "item": {}}

    return _normalize_meal_details(meals[0])


@mcp.tool()
def random_meal():
    """
    Fetch one random meal.

    Output:
    - same shape as meal_details
    """
    payload = _get_json("random.php")
    meals = payload.get("meals")

    if meals is None:
        return {"message": "no matches", "item": {}}

    return _normalize_meal_details(meals[0])


if __name__ == "__main__":
    mcp.run()
