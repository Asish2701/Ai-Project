# 8 Puzzle Problem Solver

This workspace contains a self-contained 8-puzzle solver with:

- State representation as a list of 9 integers
- Legal move generation
- BFS
- DFS
- A*
- Two heuristics for A*
- Performance comparison support

## Files

- [eight_puzzle.pl](eight_puzzle.pl)
- [app.py](app.py)
- [requirements.txt](requirements.txt)

## Representation

A board state is a list in row-major order. The blank tile is `0`.

Example:

```prolog
[1,2,3,4,5,6,0,7,8]
```

## Main Predicates

- `solve_bfs(Start, Goal, Result).`
- `solve_dfs(Start, Goal, Result).`
- `solve_astar(Start, Goal, Heuristic, Result).`
- `compare_strategies(Result).`
- `compare_strategies(Start, Result).`

Heuristic values for A*:

- `misplaced`
- `manhattan`

## Example Queries

```prolog
?- [eight_puzzle].
?- goal_state(Goal).
?- solve_bfs([1,2,3,4,5,6,0,7,8], Goal, Result).
?- solve_dfs([1,2,3,4,5,6,0,7,8], Goal, Result).
?- solve_astar([1,2,3,4,5,6,0,7,8], Goal, manhattan, Result).
?- compare_strategies([1,2,3,4,5,6,0,7,8], Results).
```

## GUI

Run the modern animated dashboard with:

```bash
streamlit run app.py
```

The GUI includes:

- A SaaS-style layout with custom cards and gradients
- BFS, DFS, and A* controls
- Step-by-step tile playback with play, pause, previous, and next controls
- A timeline for jumping directly to any board state

## Result Shape

Each solver returns a dict like this:

```prolog
result{path:[...], stats:stats{moves:N, expanded:M, runtime_ms:T}}
```

## Notes

- The solver checks solvability before searching.
- A* uses a closed set plus sorted frontier insertion.
- For best results, run this in SWI-Prolog.
