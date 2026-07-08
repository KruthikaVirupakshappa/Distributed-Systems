# HW5 Part 2 - Meals MCP Server

## Where things should be created

- **TheMealDB API**: You do not create this. It is a public hosted API at:
  - https://www.themealdb.com/api/json/v1/1/
- **Your MCP server**: You create this locally in this folder:
  - `Homework/HW5/Part2/meals_server.py`

So for this assignment, your work is only the local MCP server code that calls TheMealDB endpoints.

## What is already done

Implemented server file:
- `Homework/HW5/Part2/meals_server.py`

Tools exposed:
1. `search_meals_by_name(query, limit=5)`
2. `meals_by_ingredient(ingredient, limit=12)`
3. `meal_details(id)`
4. `random_meal()`

## Run with existing env

From workspace root:

```bash
cd "/Users/Kruthika/Documents/Data 236 Distributed Sys"
source env/bin/activate
mcp dev Homework/HW5/Part2/meals_server.py
```

This opens MCP Inspector.

## MCP Inspector test inputs (for screenshots)

1. **search_meals_by_name**
   - query: Arrabiata
   - limit: 3

2. **meals_by_ingredient**
   - ingredient: chicken
   - limit: 5

3. **meal_details**
   - id: 52772

4. **random_meal**
   - no args

## Claude Desktop server config (macOS)

Create or edit:

- `~/Library/Application Support/Claude/claude_desktop_config.json`

Example config entry:

```json
{
  "mcpServers": {
    "meals": {
      "command": "/Users/Kruthika/Documents/Data 236 Distributed Sys/env/bin/python",
      "args": [
        "/Users/Kruthika/Documents/Data 236 Distributed Sys/Homework/HW5/Part2/meals_server.py"
      ]
    }
  }
}
```

After saving, restart Claude Desktop and check the tools icon.

## Suggested prompts in Claude

- Find 3 Italian pasta recipes by name and show short summaries with images.
- List meals that use chicken as a main ingredient and include meal IDs.
- Show full details for meal id 52772.
- Give me one random meal with ingredients and measures.
