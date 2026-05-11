import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import random
import os
import json

# ============================================
# CONFIGURATION
# ============================================
app = dash.Dash(__name__, prevent_initial_callbacks=True)
app.title = "Node Activation System"

# Map input numbers (60-94) to node IDs (0-34)
INPUT_TO_NODE = {i: i - 60 for i in range(60, 95)}  # 60->0, 61->1, ..., 94->34
NODE_TO_INPUT = {v: k for k, v in INPUT_TO_NODE.items()}

# ============================================
# FIXED POSITIONS FOR 35 NODES
# ============================================
X_COORDS = [-9.5, -7.0, -4.5, -2.0, 0.5, 3.0, 5.5, 8.0]
Y_COORDS = [8.0, 5.0, 2.0, -1.0, -4.0]

NODE_POSITIONS = [
    (x, y)
    for y in Y_COORDS
    for x in X_COORDS
]

CUSTOM_NODE_POSITIONS = {}
for node_id, coords in CUSTOM_NODE_POSITIONS.items():
    NODE_POSITIONS[node_id] = coords

fixed_positions = {i: NODE_POSITIONS[i] for i in range(35)}

random_widths  = {i: random.randint(100, 300) for i in range(35)}
random_heights = {i: random.randint(100, 300) for i in range(35)}

node_data = pd.DataFrame({
    'id':     range(35),
    'x':      [fixed_positions[i][0] for i in range(35)],
    'y':      [fixed_positions[i][1] for i in range(35)],
    'width':  [random_widths[i]  for i in range(35)],
    'height': [random_heights[i] for i in range(35)]
})

# ============================================
# CSS
# ============================================
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background: #1a1a1a;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            .control-panel {
                background: #2d2d2d;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 15px;
                border: 1px solid #404040;
                display: flex;
                justify-content: center;
            }
            .input-group {
                display: flex;
                align-items: center;
                gap: 8px;
                flex-wrap: wrap;
                justify-content: center;
            }
            label {
                color: #ffffff;
                font-size: 14px;
            }
            input {
                background: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555;
                width: 80px;
                height: 30px;
                font-size: 14px;
                padding: 3px 8px;
                border-radius: 4px;
            }
            button {
                padding: 8px 16px;
                font-size: 13px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                background: #007bff;
                color: white;
                min-width: 70px;
            }
            button:hover { background: #0056b3; }

            /* Edit-mode status banner */
            .edit-status {
                display: none;
                background: #2a2a00;
                border: 1px solid #aaaa00;
                color: #ffff66;
                padding: 8px 16px;
                border-radius: 6px;
                margin-bottom: 10px;
                text-align: center;
                font-size: 14px;
                letter-spacing: 0.03em;
            }
            .edit-status.active { display: block; }

            .graph-container {
                background: #000000;
                border-radius: 8px;
                padding: 10px;
                border: 1px solid #404040;
            }
            /* Crosshair cursor during edit mode */
            .graph-container.edit-mode {
                cursor: crosshair;
                border-color: #aaaa00;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        {%config%}
        {%scripts%}
        {%renderer%}
    </body>
</html>
'''

# ============================================
# LAYOUT
# ============================================
app.layout = html.Div(className='container', children=[

    # Control Panel
    html.Div(className='control-panel', children=[
        html.Div(className='input-group', children=[
            html.Label("Input:", style={'fontWeight': 'bold'}),
            dcc.Input(
                id='node-input',
                type='number',
                min=60, max=94, step=1,
                value=60
            ),
            html.Button('Random',     id='random-button', n_clicks=0),
            html.Button('Edit nodes', id='edit-button',   n_clicks=0),
            html.Button('Start Loop', id='cycle-button',  n_clicks=0),
            html.Button('Stop',       id='stop-button',   n_clicks=0),
            html.Button('Reset',      id='reset-button',  n_clicks=0),
        ]),
    ]),

    # Edit-mode status banner (shown/hidden via className)
    html.Div(id='edit-status-banner', className='edit-status',
             children="Edit mode — click on the graph to place each node in order"),

    # Graph
    html.Div(id='graph-container', className='graph-container', children=[
        dcc.Graph(
            id='node-graph',
            style={'height': '600px', 'backgroundColor': '#000000'},
            config={'displayModeBar': False}
        ),
    ]),

    # Hidden state stores
    dcc.Store(id='active-nodes',          data=[]),
    dcc.Store(id='cycle-active',          data=False),
    dcc.Store(id='edit-mode',             data=False),
    dcc.Store(id='edit-index',            data=0),
    dcc.Store(id='node-positions-store',  data=None),
    dcc.Interval(id='cycle-interval',     interval=1000, disabled=True),
])

# ============================================
# HELPER FUNCTIONS
# ============================================
def _positions_file_path():
    try:
        folder = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        folder = os.getcwd()
    return os.path.join(folder, 'node_positions.json')


def save_positions_to_file(positions):
    """Save node positions list to JSON beside this script."""
    with open(_positions_file_path(), 'w') as f:
        json.dump(positions, f, indent=2)


def load_positions_from_file():
    """Return saved positions (list of [x,y]) or None."""
    path = _positions_file_path()
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        if isinstance(data, list) and len(data) == 35:
            return data
    except Exception:
        pass
    return None


def default_positions():
    return [[float(node_data.at[i, 'x']), float(node_data.at[i, 'y'])] for i in range(35)]


def create_figure(active_nodes, node_positions=None, edit_mode=False, edit_index=0):
    """
    Render the node graph.

    In normal mode:  grey dots for all nodes, white rectangles for active ones.
    In edit mode:
      - invisible dense mesh covering the whole canvas to capture any click
      - green dots for already-placed nodes (index < edit_index)
      - yellow marker showing where the next node will land
      - white rectangles are hidden (active_nodes ignored while editing)
    """
    fig = go.Figure()

    positions = node_positions if node_positions else default_positions()

    if edit_mode:
        # ── Dense invisible click-capture mesh ────────────────────────────
        # A fine grid of transparent points filling the entire plot area.
        # Plotly snaps clickData to the nearest point, giving us free-form
        # coordinates anywhere on the canvas.
        mesh_xs, mesh_ys = [], []
        for gx in np.arange(-12, 12.1, 0.5):   # step 0.5 → ~48 cols
            for gy in np.arange(-7, 12.1, 0.5): # step 0.5 → ~38 rows
                mesh_xs.append(round(float(gx), 2))
                mesh_ys.append(round(float(gy), 2))

        fig.add_trace(go.Scatter(
            x=mesh_xs, y=mesh_ys,
            mode='markers',
            marker=dict(size=12, color='rgba(0,0,0,0)', opacity=0),
            hoverinfo='none',
            showlegend=False,
            name='__clickmesh__'
        ))
        # ── Edit mode rendering ───────────────────────────────────────────
        # Split nodes into: placed, pending (next), and remaining
        placed_xs, placed_ys, placed_labels = [], [], []
        next_xs, next_ys = [], []
        remaining_xs, remaining_ys = [], []

        for i in range(35):
            p = positions[i]
            if p is None:
                # Not yet placed — use default position as a ghost
                gx, gy = float(node_data.at[i, 'x']), float(node_data.at[i, 'y'])
                if i == edit_index:
                    next_xs.append(gx)
                    next_ys.append(gy)
                else:
                    remaining_xs.append(gx)
                    remaining_ys.append(gy)
            else:
                if i < edit_index:
                    # Already placed
                    placed_xs.append(p[0])
                    placed_ys.append(p[1])
                    placed_labels.append(f"Node {i} ✓")
                elif i == edit_index:
                    next_xs.append(p[0])
                    next_ys.append(p[1])
                else:
                    remaining_xs.append(p[0])
                    remaining_ys.append(p[1])

        # Remaining (unplaced, not current) — dim grey
        if remaining_xs:
            fig.add_trace(go.Scatter(
                x=remaining_xs, y=remaining_ys,
                mode='markers',
                marker=dict(size=6, color='#303030'),
                hoverinfo='none', showlegend=False
            ))

        # Placed nodes — bright green
        if placed_xs:
            fig.add_trace(go.Scatter(
                x=placed_xs, y=placed_ys,
                mode='markers+text',
                marker=dict(size=10, color='#00dd88',
                            line=dict(color='#00ff99', width=1)),
                text=placed_labels,
                textposition='top center',
                textfont=dict(color='#00dd88', size=9),
                hoverinfo='text', showlegend=False
            ))

        # Next node to place — bright yellow, larger
        if next_xs:
            fig.add_trace(go.Scatter(
                x=next_xs, y=next_ys,
                mode='markers',
                marker=dict(size=16, color='#ffee00',
                            symbol='circle',
                            line=dict(color='#ffffff', width=2)),
                hoverinfo='none', showlegend=False
            ))

        # Annotation: instruction
        label_text = (
            f"Click to place node <b>{edit_index}</b> "
            f"(input {NODE_TO_INPUT.get(edit_index, '?')})  —  "
            f"{edit_index} / 35 placed"
        )
        fig.add_annotation(
            x=0, y=11, xref='x', yref='y',
            showarrow=False, text=label_text,
            font=dict(color='#ffee00', size=13),
            bgcolor='#1a1a00', bordercolor='#aaaa00',
            borderwidth=1, borderpad=6
        )

    else:
        # ── Normal mode rendering ─────────────────────────────────────────
        xs = [p[0] if p else node_data.at[i, 'x'] for i, p in enumerate(positions)]
        ys = [p[1] if p else node_data.at[i, 'y'] for i, p in enumerate(positions)]

        fig.add_trace(go.Scatter(
            x=xs, y=ys,
            mode='markers',
            marker=dict(size=6, color='#404040', line=dict(width=0)),
            hoverinfo='none', showlegend=False
        ))

        if active_nodes:
            for node_id in active_nodes:
                p = positions[node_id]
                if p:
                    nx, ny = p[0], p[1]
                else:
                    nx, ny = node_data.at[node_id, 'x'], node_data.at[node_id, 'y']
                width  = node_data.iloc[node_id]['width']
                height = node_data.iloc[node_id]['height']

                fig.add_shape(
                    type="rect",
                    x0=nx - width  / 200,
                    x1=nx + width  / 200,
                    y0=ny - height / 200,
                    y1=ny + height / 200,
                    line=dict(color="white", width=1),
                    fillcolor="white",
                    opacity=0.9,
                    layer="above"
                )
                fig.add_trace(go.Scatter(
                    x=[nx], y=[ny],
                    mode='markers',
                    marker=dict(size=1, color='white', opacity=0),
                    text=[f"Node {node_id}<br>Input: {NODE_TO_INPUT[node_id]}"
                          f"<br>Width: {width}px<br>Height: {height}px"],
                    hoverinfo='text',
                    hoverlabel=dict(bgcolor='#2d2d2d', font=dict(color='white')),
                    showlegend=False
                ))

    # Shared layout
    fig.update_layout(
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-12, 12]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-7, 12]),
        plot_bgcolor='#000000',
        paper_bgcolor='#000000',
        height=550,
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=False
    )

    return fig


# ============================================
# MAIN CALLBACK
# ============================================
@app.callback(
    [Output('node-graph',           'figure'),
     Output('node-input',           'value'),
     Output('active-nodes',         'data'),
     Output('cycle-active',         'data'),
     Output('cycle-interval',       'disabled'),
     Output('edit-mode',            'data'),
     Output('edit-index',           'data'),
     Output('node-positions-store', 'data'),
     Output('edit-status-banner',   'className'),
     Output('graph-container',      'className')],
    [Input('node-input',     'value'),
     Input('random-button',  'n_clicks'),
     Input('cycle-button',   'n_clicks'),
     Input('stop-button',    'n_clicks'),
     Input('reset-button',   'n_clicks'),
     Input('cycle-interval', 'n_intervals'),
     Input('edit-button',    'n_clicks'),
     Input('node-graph',     'clickData')],
    [State('active-nodes',          'data'),
     State('cycle-active',          'data'),
     State('edit-mode',             'data'),
     State('edit-index',            'data'),
     State('node-positions-store',  'data')]
)
def update_system(input_value, random_clicks, cycle_clicks, stop_clicks,
                  reset_clicks, interval, edit_clicks, click_data,
                  active_nodes, cycle_active, edit_mode, edit_index, node_positions):

    ctx = dash.callback_context
    trigger_id = (ctx.triggered[0]['prop_id'].split('.')[0]
                  if ctx.triggered else None)

    # ── Defaults ──────────────────────────────────────────────────────────
    if active_nodes is None:
        active_nodes = []
    if edit_mode is None:
        edit_mode = False
    if edit_index is None:
        edit_index = 0

    new_cycle_active = bool(cycle_active)
    cycle_disabled   = not new_cycle_active

    # Initialise positions from file or defaults on first load
    if node_positions is None:
        loaded = load_positions_from_file()
        node_positions = loaded if loaded else default_positions()

    # ── Button / trigger handling ─────────────────────────────────────────

    if trigger_id == 'reset-button':
        active_nodes     = []
        input_value      = 60
        new_cycle_active = False
        cycle_disabled   = True
        edit_mode        = False
        edit_index       = 0

    elif trigger_id == 'random-button':
        input_value      = int(np.random.randint(60, 95))
        node_id          = INPUT_TO_NODE[input_value]
        if node_id not in active_nodes:
            active_nodes.append(node_id)
        new_cycle_active = False
        cycle_disabled   = True

    elif trigger_id == 'cycle-button':
        new_cycle_active = True
        cycle_disabled   = False
        if not active_nodes:
            active_nodes.append(0)
            input_value = NODE_TO_INPUT[0]

    elif trigger_id == 'stop-button':
        new_cycle_active = False
        cycle_disabled   = True

    elif trigger_id == 'edit-button':
        # Enter edit mode — wipe stored positions so user places all 35 fresh
        edit_mode        = True
        edit_index       = 0
        node_positions   = [None] * 35
        active_nodes     = []
        new_cycle_active = False
        cycle_disabled   = True

    elif trigger_id == 'cycle-interval' and new_cycle_active:
        if len(active_nodes) >= 35:
            # Full cycle done — restart
            active_nodes = [0]
            input_value  = NODE_TO_INPUT[0]
        else:
            for i in range(35):
                if i not in active_nodes:
                    active_nodes.append(i)
                    input_value = NODE_TO_INPUT[i]
                    break

    elif trigger_id == 'node-input' and input_value is not None and not edit_mode:
        input_value = max(60, min(94, int(input_value)))
        node_id     = INPUT_TO_NODE[input_value]
        if node_id not in active_nodes and len(active_nodes) < 35:
            active_nodes.append(node_id)
        new_cycle_active = False
        cycle_disabled   = True

    # ── Graph click: place node in edit mode ──────────────────────────────
    if edit_mode and trigger_id == 'node-graph' and click_data:
        try:
            point = click_data['points'][0]
            cx = float(point['x'])
            cy = float(point['y'])
        except (KeyError, IndexError, ValueError, TypeError):
            cx = cy = None

        if cx is not None and 0 <= edit_index < 35:
            node_positions = list(node_positions)   # ensure mutable copy
            node_positions[edit_index] = [cx, cy]
            edit_index += 1

            # All 35 placed → save and exit edit mode
            if edit_index >= 35:
                edit_mode = False
                save_positions_to_file(node_positions)
                # Sync runtime node_data so rectangle rendering uses new coords
                for i, p in enumerate(node_positions):
                    if p:
                        node_data.at[i, 'x'] = p[0]
                        node_data.at[i, 'y'] = p[1]

    if input_value is None:
        input_value = 60

    # ── UI class helpers ──────────────────────────────────────────────────
    banner_class    = 'edit-status active' if edit_mode else 'edit-status'
    container_class = 'graph-container edit-mode' if edit_mode else 'graph-container'

    fig = create_figure(
        active_nodes,
        node_positions=node_positions,
        edit_mode=edit_mode,
        edit_index=edit_index
    )

    return (fig, input_value, active_nodes, new_cycle_active, cycle_disabled,
            edit_mode, edit_index, node_positions, banner_class, container_class)


# ============================================
# RUN THE APP
# ============================================
if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8050)