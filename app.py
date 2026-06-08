from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import streamlit as st
from streamlit.components.v1 import html as components_html

ROOT = Path(__file__).resolve().parent
SWIPL = r"C:\Program Files\swipl\bin\swipl.exe"
PROLOG_FILE = ROOT / "eight_puzzle.pl"

PRESETS = {
    "Near Goal": [1, 2, 3, 4, 5, 6, 0, 7, 8],
    "Balanced": [1, 2, 3, 5, 0, 6, 4, 7, 8],
    "Deeper": [7, 2, 4, 5, 0, 6, 8, 3, 1],
}

st.set_page_config(
  page_title="8 Puzzle Problem Solver",
    page_icon="▣",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
      --bg: #07111f;
      --panel: rgba(10, 18, 35, 0.84);
      --panel-2: rgba(14, 27, 49, 0.92);
      --line: rgba(255, 255, 255, 0.09);
      --text: #e9f2ff;
      --muted: #94a8c6;
      --accent: #5be7c4;
      --accent-2: #7fb2ff;
      --warn: #ffcf70;
    }

    .stApp {
      background:
        radial-gradient(circle at top left, rgba(91, 231, 196, 0.16), transparent 24%),
        radial-gradient(circle at top right, rgba(127, 178, 255, 0.16), transparent 22%),
        linear-gradient(160deg, #040911 0%, #08101b 35%, #0c1726 100%);
      color: var(--text);
    }

    .block-container {
      padding-top: 1.4rem;
      padding-bottom: 2rem;
    }

    [data-testid="stSidebar"] {
      background: linear-gradient(180deg, rgba(6, 11, 22, 0.96), rgba(10, 18, 35, 0.92));
      border-right: 1px solid var(--line);
    }

    .hero {
      padding: 1.2rem 1.3rem;
      border: 1px solid var(--line);
      border-radius: 28px;
      background: linear-gradient(135deg, rgba(16, 29, 52, 0.92), rgba(7, 17, 31, 0.82));
      box-shadow: 0 28px 80px rgba(0, 0, 0, 0.34);
      position: relative;
      overflow: hidden;
    }

    .hero::after {
      content: "";
      position: absolute;
      inset: -40% auto auto 65%;
      width: 220px;
      height: 220px;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(91, 231, 196, 0.2), transparent 65%);
      pointer-events: none;
    }

    .eyebrow {
      display: inline-flex;
      align-items: center;
      gap: 0.45rem;
      padding: 0.35rem 0.75rem;
      margin-bottom: 0.65rem;
      border-radius: 999px;
      border: 1px solid rgba(91, 231, 196, 0.25);
      background: rgba(91, 231, 196, 0.08);
      color: var(--accent);
      font-size: 0.8rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }

    .hero h1 {
      margin: 0;
      font-size: clamp(2rem, 4vw, 3.5rem);
      line-height: 1;
      color: var(--text);
    }

    .hero p {
      margin: 0.85rem 0 0;
      max-width: 64ch;
      color: var(--muted);
      font-size: 1rem;
      line-height: 1.65;
    }

    .glass-card {
      border: 1px solid var(--line);
      border-radius: 22px;
      background: linear-gradient(180deg, rgba(13, 23, 42, 0.92), rgba(7, 16, 29, 0.84));
      box-shadow: 0 18px 60px rgba(0, 0, 0, 0.26);
      padding: 1rem 1.1rem;
    }

    .metric-shell {
      display: grid;
      gap: 0.35rem;
    }

    .metric-shell .label {
      color: var(--muted);
      font-size: 0.82rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }

    .metric-shell .value {
      color: var(--text);
      font-size: 1.6rem;
      font-weight: 800;
    }

    .metric-shell .hint {
      color: var(--muted);
      font-size: 0.88rem;
    }

    .sidebar-title {
      color: var(--text);
      font-weight: 700;
      font-size: 1rem;
      margin-bottom: 0.5rem;
    }

    .stButton > button {
      border-radius: 14px;
      border: 1px solid rgba(91, 231, 196, 0.24);
      background: linear-gradient(180deg, rgba(91, 231, 196, 0.14), rgba(91, 231, 196, 0.07));
      color: var(--text);
      padding: 0.65rem 1rem;
      font-weight: 700;
      transition: transform 0.18s ease, border-color 0.18s ease, background 0.18s ease;
    }

    .stButton > button:hover {
      transform: translateY(-1px);
      border-color: rgba(91, 231, 196, 0.44);
      background: linear-gradient(180deg, rgba(91, 231, 196, 0.2), rgba(91, 231, 196, 0.1));
    }

    .muted-copy {
      color: var(--muted);
      font-size: 0.95rem;
      line-height: 1.6;
    }

    .status-chip {
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      padding: 0.4rem 0.8rem;
      border-radius: 999px;
      background: rgba(127, 178, 255, 0.12);
      border: 1px solid rgba(127, 178, 255, 0.22);
      color: #cfe1ff;
      font-size: 0.85rem;
      font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def parse_state(raw: str) -> list[int]:
    values = [int(match) for match in re.findall(r"\d+", raw)]
    if len(values) != 9:
        raise ValueError("Enter exactly 9 numbers from 0 to 8.")
    if sorted(values) != list(range(9)):
        raise ValueError("State must contain each tile 0 through 8 exactly once.")
    return values


def prolog_list(values: list[int]) -> str:
    return "[" + ",".join(str(value) for value in values) + "]"


def run_solver(start_state: list[int], strategy: str, heuristic: str) -> dict:
    query = (
        f"gui_solution({prolog_list(start_state)}, {strategy}, {heuristic}, Payload), "
        "json_write_dict(current_output, Payload, [width(0)])"
    )
    command = [SWIPL, "-q", "-s", str(PROLOG_FILE), "-g", query, "-t", "halt"]
    completed = subprocess.run(command, capture_output=True, text=True, cwd=ROOT)
    if completed.returncode != 0:
        message = (completed.stderr or completed.stdout or "Unknown solver error").strip()
        return {"ok": False, "error": message}

    output = completed.stdout.strip()
    if not output:
        return {"ok": False, "error": "The solver returned no output."}

    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return {"ok": False, "error": output}


if "start_state" not in st.session_state:
    st.session_state.start_state = PRESETS["Near Goal"]
if "solution" not in st.session_state:
    st.session_state.solution = None
if "active_preset" not in st.session_state:
    st.session_state.active_preset = "Near Goal"
if "solution_signature" not in st.session_state:
  st.session_state.solution_signature = None

st.sidebar.markdown('<div class="sidebar-title">Solver Controls</div>', unsafe_allow_html=True)
st.sidebar.caption("Pick a starting board, choose a strategy, and animate the solution path.")

preset_buttons = st.sidebar.columns(3)
for idx, preset_name in enumerate(PRESETS):
    if preset_buttons[idx].button(preset_name, use_container_width=True):
        st.session_state.start_state = PRESETS[preset_name]
        st.session_state.active_preset = preset_name

custom_state_text = st.sidebar.text_input(
    "Custom start state",
    value=", ".join(str(value) for value in st.session_state.start_state),
    help="Enter the board as 9 numbers in row-major order, for example 1,2,3,4,5,6,0,7,8.",
)

strategy = st.sidebar.selectbox("Strategy", ["astar", "bfs", "dfs"], format_func=lambda value: {"astar": "A*", "bfs": "BFS", "dfs": "DFS"}[value])
heuristic = st.sidebar.selectbox(
    "Heuristic",
    ["manhattan", "misplaced"],
    format_func=lambda value: {"manhattan": "Manhattan distance", "misplaced": "Misplaced tiles"}[value],
    disabled=strategy != "astar",
)

st.sidebar.markdown("---")
playback_speed = st.sidebar.slider("Playback speed", 120, 1400, 420, 20)
auto_run = st.sidebar.toggle("Auto-run animation", value=True)

try:
    parsed_state = parse_state(custom_state_text)
    st.session_state.start_state = parsed_state
    start_state_error = None
except ValueError as error:
    start_state_error = str(error)

solve_clicked = st.sidebar.button("Solve puzzle", use_container_width=True)

current_signature = None
if start_state_error is None:
    current_signature = (
        tuple(st.session_state.start_state),
        strategy,
        heuristic if strategy == "astar" else "none",
    )

should_solve = start_state_error is None and (
    st.session_state.solution is None
    or st.session_state.solution_signature != current_signature
    or solve_clicked
)

if should_solve:
    st.session_state.solution = run_solver(
        st.session_state.start_state,
        strategy,
        heuristic if strategy == "astar" else "none",
    )
    st.session_state.solution_signature = current_signature

st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">8 Puzzle Problem Solver</div>
      <h1>8 Puzzle Problem Solver</h1>
      <p>
        Use BFS, DFS, or A* to solve the board, then replay each move with an animated tile transition.
        The interface is optimized for quick comparisons, clean metrics, and readable playback.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")

if start_state_error:
    st.error(start_state_error)

if st.session_state.solution is None:
    st.info("Choose a preset or type a custom board, then click Solve puzzle.")
else:
    solution = st.session_state.solution
    if not solution.get("ok", False):
        st.error(solution.get("error", "Unable to solve this puzzle."))
    else:
        result = solution["result"]
        stats = result["stats"]
        path = result["path"]
        top = st.columns(4)
        top[0].markdown(
            f'<div class="glass-card metric-shell"><div class="label">Moves</div><div class="value">{stats["moves"]}</div><div class="hint">Solution depth</div></div>',
            unsafe_allow_html=True,
        )
        top[1].markdown(
            f'<div class="glass-card metric-shell"><div class="label">Expanded</div><div class="value">{stats["expanded"]}</div><div class="hint">Visited search nodes</div></div>',
            unsafe_allow_html=True,
        )
        top[2].markdown(
            f'<div class="glass-card metric-shell"><div class="label">Runtime</div><div class="value">{stats["runtime_ms"]} ms</div><div class="hint">Measured in Prolog</div></div>',
            unsafe_allow_html=True,
        )
        top[3].markdown(
            f'<div class="glass-card metric-shell"><div class="label">States</div><div class="value">{len(path)}</div><div class="hint">Including start and goal</div></div>',
            unsafe_allow_html=True,
        )

        st.write("")

        status = st.columns([1.2, 2.2, 1.6])
        status[0].markdown(
            f'<span class="status-chip">Strategy: {solution["strategy"].upper()}</span>',
            unsafe_allow_html=True,
        )
        status[1].markdown(
            f'<span class="status-chip">Heuristic: {solution["heuristic"].replace("_", " ").title()}</span>',
            unsafe_allow_html=True,
        )
        status[2].markdown(
            f'<span class="status-chip">Start: {solution["start"]}</span>',
            unsafe_allow_html=True,
        )

        animation_height = 760 if auto_run else 720
        path_json = json.dumps(path)
        solution_json = json.dumps(solution)
        board_html = """
            <div class="board-shell">
              <style>
                .board-shell {{
                  display: grid;
                  grid-template-columns: 1.2fr 0.9fr;
                  gap: 22px;
                  align-items: start;
                  padding: 24px;
                  border-radius: 30px;
                  border: 1px solid rgba(255, 255, 255, 0.08);
                  background: linear-gradient(160deg, rgba(12, 22, 39, 0.94), rgba(7, 14, 27, 0.92));
                  box-shadow: 0 30px 90px rgba(0, 0, 0, 0.35);
                  color: #e9f2ff;
                  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif;
                }}
                .panel {{
                  border-radius: 24px;
                  border: 1px solid rgba(255, 255, 255, 0.09);
                  background: rgba(8, 16, 31, 0.9);
                  padding: 18px;
                }}
                .panel h2, .panel h3 {{
                  margin: 0;
                }}
                .panel .sub {{
                  margin-top: 6px;
                  color: #9ab0ce;
                  line-height: 1.55;
                  font-size: 0.95rem;
                }}
                .board-wrap {{
                  display: grid;
                  justify-items: center;
                  gap: 14px;
                }}
                .board {{
                  width: 336px;
                  height: 336px;
                  position: relative;
                  padding: 12px;
                  border-radius: 28px;
                  background:
                    linear-gradient(180deg, rgba(24, 38, 64, 0.92), rgba(9, 17, 31, 0.98));
                  box-shadow:
                    inset 0 1px 0 rgba(255, 255, 255, 0.1),
                    0 24px 50px rgba(0, 0, 0, 0.28);
                  overflow: hidden;
                }}
                .board::before {{
                  content: '';
                  position: absolute;
                  inset: 12px;
                  border-radius: 18px;
                  background-image:
                    linear-gradient(rgba(255,255,255,0.08) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(255,255,255,0.08) 1px, transparent 1px);
                  background-size: 108px 108px;
                  pointer-events: none;
                }}
                .tile {{
                  position: absolute;
                  width: 96px;
                  height: 96px;
                  display: grid;
                  place-items: center;
                  border-radius: 20px;
                  font-size: 2rem;
                  font-weight: 800;
                  letter-spacing: -0.04em;
                  color: #091422;
                  background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(185, 232, 255, 0.92));
                  box-shadow:
                    0 10px 24px rgba(0, 0, 0, 0.25),
                    inset 0 1px 0 rgba(255, 255, 255, 0.72);
                  transform: translate(12px, 12px);
                  transition:
                    transform {playback_speed}ms cubic-bezier(0.22, 1, 0.36, 1),
                    box-shadow 180ms ease,
                    filter 180ms ease,
                    opacity 180ms ease;
                  will-change: transform;
                }}
                .tile.active {{
                  box-shadow:
                    0 0 0 2px rgba(91, 231, 196, 0.24),
                    0 16px 30px rgba(91, 231, 196, 0.25),
                    inset 0 1px 0 rgba(255, 255, 255, 0.72);
                  filter: saturate(1.1);
                }}
                .controls {{
                  display: flex;
                  flex-wrap: wrap;
                  gap: 10px;
                  align-items: center;
                  justify-content: center;
                }}
                .btn, .chip, .range {{
                  border-radius: 999px;
                  border: 1px solid rgba(255,255,255,0.1);
                  background: rgba(255,255,255,0.04);
                  color: #e9f2ff;
                }}
                .btn {{
                  padding: 10px 16px;
                  font-size: 0.92rem;
                  font-weight: 700;
                  cursor: pointer;
                }}
                .btn.primary {{
                  background: linear-gradient(180deg, rgba(91,231,196,0.22), rgba(91,231,196,0.1));
                  border-color: rgba(91,231,196,0.25);
                }}
                .btn:hover {{ transform: translateY(-1px); }}
                .chip {{
                  padding: 8px 12px;
                  color: #bcd0ef;
                  font-size: 0.85rem;
                }}
                .timeline {{
                  display: grid;
                  gap: 10px;
                  margin-top: 16px;
                }}
                .timeline-row {{
                  display: flex;
                  gap: 8px;
                  overflow-x: auto;
                  padding-bottom: 6px;
                }}
                .step-pill {{
                  min-width: 44px;
                  padding: 8px 10px;
                  text-align: center;
                  border-radius: 12px;
                  border: 1px solid rgba(255,255,255,0.1);
                  background: rgba(255,255,255,0.05);
                  color: #c6d7ee;
                  cursor: pointer;
                  flex: 0 0 auto;
                }}
                .step-pill.active {{
                  border-color: rgba(91,231,196,0.32);
                  background: rgba(91,231,196,0.14);
                  color: #f4fffb;
                }}
                .status {{
                  display: grid;
                  gap: 12px;
                }}
                .headline {{
                  font-size: 1.3rem;
                  font-weight: 800;
                  color: #f5fbff;
                }}
                .move {{
                  color: #5be7c4;
                  font-weight: 700;
                }}
                .meta-grid {{
                  display: grid;
                  grid-template-columns: repeat(2, minmax(0, 1fr));
                  gap: 10px;
                }}
                .meta-card {{
                  padding: 14px;
                  border-radius: 18px;
                  background: rgba(255,255,255,0.04);
                  border: 1px solid rgba(255,255,255,0.08);
                }}
                .meta-card .k {{
                  color: #90a4c0;
                  font-size: 0.78rem;
                  text-transform: uppercase;
                  letter-spacing: 0.1em;
                }}
                .meta-card .v {{
                  margin-top: 6px;
                  font-weight: 800;
                  font-size: 1.06rem;
                  color: #f2f7ff;
                }}
                .state-preview {{
                  margin-top: 12px;
                  padding: 14px;
                  border-radius: 18px;
                  border: 1px solid rgba(255,255,255,0.08);
                  background: rgba(255,255,255,0.03);
                  color: #c0d1ea;
                  font-size: 0.92rem;
                  line-height: 1.5;
                }}
                .range {{
                  width: 100%;
                  accent-color: #5be7c4;
                }}
                @media (max-width: 980px) {{
                  .board-shell {{
                    grid-template-columns: 1fr;
                  }}
                }}
              </style>
              <div class="panel board-wrap">
                <h2>Animated Playback</h2>
                <div class="sub">Use the controls below to move through the solution one state at a time.</div>
                <div class="board" id="board"></div>
                <div class="controls">
                  <button class="btn" id="prevBtn">Previous</button>
                  <button class="btn primary" id="playBtn">Play</button>
                  <button class="btn" id="pauseBtn">Pause</button>
                  <button class="btn" id="nextBtn">Next</button>
                </div>
                <input class="range" type="range" id="slider" min="0" max="0" value="0" step="1" />
                <div class="chip" id="stepChip">Step 1 of 1</div>
              </div>
              <div class="panel status">
                <div>
                  <div class="headline" id="headline">Ready to replay the path</div>
                  <div class="sub" id="moveText">Press Play to see the tiles move across the board.</div>
                </div>
                <div class="meta-grid">
                  <div class="meta-card"><div class="k">Strategy</div><div class="v">__STRATEGY__</div></div>
                  <div class="meta-card"><div class="k">Heuristic</div><div class="v">__HEURISTIC__</div></div>
                  <div class="meta-card"><div class="k">Moves</div><div class="v">__MOVES__</div></div>
                  <div class="meta-card"><div class="k">Expanded</div><div class="v">__EXPANDED__</div></div>
                </div>
                <div class="timeline">
                  <div class="sub" style="margin: 0;">Jump to any state in the path</div>
                  <div class="timeline-row" id="timeline"></div>
                </div>
                <div class="state-preview" id="statePreview"></div>
              </div>
            </div>
            <script id="payload" type="application/json">__SOLUTION_JSON__</script>
            <script>
              const solution = JSON.parse(document.getElementById('payload').textContent);
              const path = __PATH_JSON__;
              const board = document.getElementById('board');
              const slider = document.getElementById('slider');
              const playBtn = document.getElementById('playBtn');
              const pauseBtn = document.getElementById('pauseBtn');
              const nextBtn = document.getElementById('nextBtn');
              const prevBtn = document.getElementById('prevBtn');
              const stepChip = document.getElementById('stepChip');
              const headline = document.getElementById('headline');
              const moveText = document.getElementById('moveText');
              const statePreview = document.getElementById('statePreview');
              const timeline = document.getElementById('timeline');
              const speed = __PLAYBACK_SPEED__;
              const tileSize = 96;
              const tileGap = 12;
              const boardPadding = 12;
              const boardStep = tileSize + tileGap;
              const tiles = {};
              let currentIndex = 0;
              let timer = null;
              let isPlaying = false;

              function pos(index) {
                return {{ row: Math.floor(index / 3), col: index % 3 }};
              }

              function moveDescriptor(previousState, nextState) {
                if (!previousState || !nextState) return 'Initial board loaded';
                let movedTile = null;
                let fromIndex = null;
                let toIndex = null;
                for (let index = 0; index < previousState.length; index++) {{
                  if (previousState[index] !== nextState[index]) {{
                    if (previousState[index] === 0) {{
                      toIndex = index;
                    }} else if (nextState[index] === 0) {{
                      movedTile = previousState[index];
                      fromIndex = index;
                    }}
                  }}
                }}
                if (movedTile === null || fromIndex === null || toIndex === null) return 'Advancing to next state';
                const start = pos(fromIndex);
                const end = pos(toIndex);
                if (end.row < start.row) return `Tile ${movedTile} moved up`;
                if (end.row > start.row) return `Tile ${movedTile} moved down`;
                if (end.col < start.col) return `Tile ${movedTile} moved left`;
                return `Tile ${movedTile} moved right`;
              }

              function boardText(state) {{
                return state.map((value, index) => value === 0 ? 'blank' : `${value}@${index}`).join('  •  ');
              }}

              function setActiveTile(previousState, nextState) {{
                for (const tile of Object.values(tiles)) tile.classList.remove('active');
                if (!previousState || !nextState) return;
                for (let index = 0; index < previousState.length; index++) {{
                  if (previousState[index] !== nextState[index] && nextState[index] !== 0) {{
                    const moved = nextState[index];
                    if (tiles[moved]) tiles[moved].classList.add('active');
                  }}
                }}
              }}

              function renderTimeline() {{
                timeline.innerHTML = '';
                path.forEach((_, index) => {{
                  const button = document.createElement('button');
                  button.className = 'step-pill' + (index === currentIndex ? ' active' : '');
                  button.textContent = index + 1;
                  button.title = `Go to step ${index + 1}`;
                  button.addEventListener('click', () => {{
                    pause();
                    currentIndex = index;
                    render();
                  }});
                  timeline.appendChild(button);
                }});
              }}

              function createTiles() {{
                for (let value = 1; value <= 8; value++) {{
                  const tile = document.createElement('div');
                  tile.className = 'tile';
                  tile.textContent = value;
                  tile.style.transform = `translate(${boardPadding}px, ${boardPadding}px)`;
                  board.appendChild(tile);
                  tiles[value] = tile;
                }}
              }}

              function layoutState(state) {{
                for (let value = 1; value <= 8; value++) {{
                  const location = state.indexOf(value);
                  const grid = pos(location);
                  tiles[value].style.transform = `translate(${boardPadding + grid.col * boardStep}px, ${boardPadding + grid.row * boardStep}px)`;
                }}
              }}

              function render() {{
                const state = path[currentIndex];
                const previousState = currentIndex > 0 ? path[currentIndex - 1] : null;
                const nextState = currentIndex < path.length - 1 ? path[currentIndex + 1] : null;
                slider.value = String(currentIndex);
                slider.max = String(path.length - 1);
                stepChip.textContent = `Step ${currentIndex + 1} of ${path.length}`;
                headline.textContent = currentIndex === 0 ? 'Start state' : currentIndex === path.length - 1 ? 'Goal state reached' : `Transition ${currentIndex}`;
                moveText.textContent = moveDescriptor(previousState, state);
                statePreview.textContent = boardText(state);
                layoutState(state);
                setActiveTile(previousState, state);
                renderTimeline();
              }}

              function stopTimer() {{
                if (timer) {{
                  clearInterval(timer);
                  timer = null;
                }}
              }}

              function pause() {{
                stopTimer();
                isPlaying = false;
                playBtn.textContent = 'Play';
              }}

              function play() {{
                stopTimer();
                isPlaying = true;
                playBtn.textContent = 'Playing';
                timer = setInterval(() => {{
                  if (currentIndex >= path.length - 1) {{
                    pause();
                    return;
                  }}
                  currentIndex += 1;
                  render();
                }}, speed);
              }}

              slider.addEventListener('input', () => {{
                pause();
                currentIndex = Number(slider.value);
                render();
              }});
              prevBtn.addEventListener('click', () => {{
                pause();
                currentIndex = Math.max(0, currentIndex - 1);
                render();
              }});
              nextBtn.addEventListener('click', () => {{
                pause();
                currentIndex = Math.min(path.length - 1, currentIndex + 1);
                render();
              }});
              playBtn.addEventListener('click', () => {{
                if (isPlaying) {{
                  pause();
                }} else {{
                  play();
                }}
              }});
              pauseBtn.addEventListener('click', pause);

              createTiles();
              render();
              if (__AUTO_RUN__) play();
            </script>
            """
        board_html = board_html.replace("{{", "{").replace("}}", "}")
        board_html = board_html.replace("__STRATEGY__", solution["strategy"].upper())
        board_html = board_html.replace("__HEURISTIC__", solution["heuristic"].replace("_", " ").title())
        board_html = board_html.replace("__MOVES__", str(stats["moves"]))
        board_html = board_html.replace("__EXPANDED__", str(stats["expanded"]))
        board_html = board_html.replace("__SOLUTION_JSON__", solution_json)
        board_html = board_html.replace("__PATH_JSON__", path_json)
        board_html = board_html.replace("__PLAYBACK_SPEED__", str(playback_speed))
        board_html = board_html.replace("__AUTO_RUN__", str(auto_run).lower())
        components_html(board_html, height=animation_height, scrolling=False)
