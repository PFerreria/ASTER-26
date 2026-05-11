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
# Define node positions using a simple grid builder.
# Edit X_COORDS and Y_COORDS to reposition rows/columns.
X_COORDS = [-9.5, -7.0, -4.5, -2.0, 0.5, 3.0, 5.5, 8.0]
Y_COORDS = [8.0, 5.0, 2.0, -1.0, -4.0]

# Build nodes left-to-right, top-to-bottom.
NODE_POSITIONS = [
    (x, y)
    for y in Y_COORDS
    for x in X_COORDS
]

# If you want to override a single node position, use CUSTOM_NODE_POSITIONS.
CUSTOM_NODE_POSITIONS = {
    # Example: 0: (-10.0, 9.0),
}
for node_id, coords in CUSTOM_NODE_POSITIONS.items():
    NODE_POSITIONS[node_id] = coords

fixed_positions = {i: NODE_POSITIONS[i] for i in range(35)}

# Generate random rectangle dimensions for each node
# Width and height are independent random values between 100 and 300
random_widths = {i: random.randint(100, 300) for i in range(35)}
random_heights = {i: random.randint(100, 300) for i in range(35)}

# Create node data with fixed positions and rectangle dimensions
node_data = pd.DataFrame({
    'id': range(35),
    'x': [fixed_positions[i][0] for i in range(35)],
    'y': [fixed_positions[i][1] for i in range(35)],
    'width': [random_widths[i] for i in range(35)],
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
            button:hover {
                background: #0056b3;
            }
            .graph-container {
                background: #000000;
                border-radius: 8px;
                padding: 10px;
                border: 1px solid #404040;
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
                min=60,
                    max=94,
                step=1,
                value=60
            ),
            html.Button('Random', id='random-button', n_clicks=0),
            html.Button('Edit nodes', id='edit-button', n_clicks=0),
            html.Button('Start Loop', id='cycle-button', n_clicks=0),
            html.Button('Stop', id='stop-button', n_clicks=0),
            html.Button('Reset', id='reset-button', n_clicks=0),
        ]),
    ]),
    
    # Graph with black background
    html.Div(className='graph-container', children=[
        dcc.Graph(
            id='node-graph', 
            style={'height': '600px', 'backgroundColor': '#000000'},
            config={'displayModeBar': False}
        ),
    ]),
    
    # Hidden state (no visible elements)
    dcc.Store(id='active-nodes', data=[]),
    dcc.Store(id='cycle-active', data=False),
    dcc.Store(id='edit-mode', data=False),
    dcc.Store(id='edit-index', data=0),
    dcc.Store(id='node-positions-store', data=None),
    dcc.Interval(id='cycle-interval', interval=1000, disabled=True),
])

# ============================================
# HELPER FUNCTIONS
# ============================================
def save_positions_to_file(positions):
    """Save node positions to a JSON file in the same folder as the script."""
    try:
        folder = os.path.dirname(__file__)
    except NameError:
        folder = os.getcwd()
    path = os.path.join(folder, 'node_positions.json')
    with open(path, 'w') as f:
        json.dump(positions, f)


def load_positions_from_file():
    """Load node positions from JSON file if available, otherwise return None."""
    try:
        folder = os.path.dirname(__file__)
    except NameError:
        folder = os.getcwd()
    path = os.path.join(folder, 'node_positions.json')
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            # ensure list length 35
            if isinstance(data, list) and len(data) == 35:
                return data
        except Exception:
            pass
    return None


def create_figure(active_nodes, node_positions=None, edit_mode=False, edit_index=0):
    """Create graph with white rectangle nodes appearing on activation"""
    fig = go.Figure()
    
    # Add base nodes (small gray dots) using node_positions if provided
    if node_positions:
        xs = [p[0] for p in node_positions if p is not None]
        ys = [p[1] for p in node_positions if p is not None]
    else:
        xs = list(node_data['x'])
        ys = list(node_data['y'])

    fig.add_trace(go.Scatter(
        x=xs,
        y=ys,
        mode='markers',
        marker=dict(
            size=6,
            color='#404040',
            line=dict(width=0)
        ),
        hoverinfo='none',
        showlegend=False
    ))
    
    # Add white rectangles for active nodes
    if active_nodes:
        for node_id in active_nodes:
            # obtain node coords from provided node_positions if present
            if node_positions and node_positions[node_id] is not None:
                nx, ny = node_positions[node_id]
                width = node_data.iloc[node_id]['width']
                height = node_data.iloc[node_id]['height']
            else:
                node = node_data.iloc[node_id]
                nx, ny = node['x'], node['y']
                width = node['width']
                height = node['height']

            # Draw rectangle
            fig.add_shape(
                type="rect",
                x0=nx - width/200,
                x1=nx + width/200,
                y0=ny - height/200,
                y1=ny + height/200,
                line=dict(color="white", width=1),
                fillcolor="white",
                opacity=0.9,
                layer="above"
            )
            
            # Invisible point for hover info
            fig.add_trace(go.Scatter(
                x=[nx],
                y=[ny],
                mode='markers',
                marker=dict(size=1, color='white', opacity=0),
                text=[f"Node {node_id}<br>Input: {NODE_TO_INPUT[node_id]}<br>Width: {width}px<br>Height: {height}px"],
                hoverinfo='text',
                hoverlabel=dict(bgcolor='#2d2d2d', font=dict(color='white')),
                showlegend=False
            ))
    
    # Black background layout
    fig.update_layout(
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-12, 12]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-12, 12]),
        plot_bgcolor='#000000',
        paper_bgcolor='#000000',
        height=550,
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=False
    )
    
    # If in edit mode, add an annotation to show progress
    if edit_mode:
        fig.add_annotation(
            x=0, y=11, xref='x', yref='y', showarrow=False,
            text=f"Editing nodes: click to set node {edit_index + 1} / 35",
            font=dict(color='yellow', size=12), bgcolor='#222'
        )
    
    return fig

# ============================================
# MAIN CALLBACK
# ============================================
@app.callback(
    [Output('node-graph', 'figure'),
     Output('node-input', 'value'),
     Output('active-nodes', 'data'),
     Output('cycle-active', 'data'),
     Output('cycle-interval', 'disabled'),
     Output('edit-mode', 'data'),
     Output('edit-index', 'data'),
     Output('node-positions-store', 'data')],
    [Input('node-input', 'value'),
     Input('random-button', 'n_clicks'),
     Input('cycle-button', 'n_clicks'),
     Input('stop-button', 'n_clicks'),
     Input('reset-button', 'n_clicks'),
     Input('cycle-interval', 'n_intervals'),
     Input('edit-button', 'n_clicks'),
     Input('node-graph', 'clickData')],
    [State('active-nodes', 'data'),
     State('cycle-active', 'data'),
     State('edit-mode', 'data'),
     State('edit-index', 'data'),
     State('node-positions-store', 'data')]
)
def update_system(input_value, random_clicks, cycle_clicks, stop_clicks, 
                  reset_clicks, interval, edit_clicks, click_data,
                  active_nodes, cycle_active, edit_mode, edit_index, node_positions):
    
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
    
    # Initialize
    if active_nodes is None:
        active_nodes = []
    
    new_cycle_active = cycle_active if cycle_active else False
    cycle_disabled = not new_cycle_active
    
    # Check if all nodes are activated
    all_activated = len(active_nodes) >= 35
    
    # If all nodes are activated and cycle is active, reset and continue
    if all_activated and new_cycle_active:
        # Reset all nodes
        active_nodes = []
        input_value = 60
        
        # Start with node 0
        if len(active_nodes) == 0 and new_cycle_active:
            active_nodes.append(0)
            input_value = NODE_TO_INPUT[0]
    
    # Ensure node_positions is initialized from file or defaults
    if node_positions is None:
        loaded = load_positions_from_file()
        if loaded:
            node_positions = loaded
            # Update node_data positions to loaded ones
            for i, p in enumerate(node_positions):
                if p is not None:
                    node_data.at[i, 'x'] = p[0]
                    node_data.at[i, 'y'] = p[1]
        else:
            # default positions from node_data
            node_positions = [[float(node_data.at[i, 'x']), float(node_data.at[i, 'y'])] for i in range(35)]

    # Handle reset button
    if trigger_id == 'reset-button' and reset_clicks and reset_clicks > 0:
        active_nodes = []
        input_value = 60
        new_cycle_active = False
        cycle_disabled = True
        # also exit edit mode
        edit_mode = False
        edit_index = 0
    
    # Handle random button
    elif trigger_id == 'random-button' and random_clicks and random_clicks > 0:
        input_value = np.random.randint(60, 95)
        node_id = INPUT_TO_NODE[input_value]
        if node_id not in active_nodes:
            active_nodes.append(node_id)
        new_cycle_active = False
        cycle_disabled = True
    
    # Handle cycle button (Start Loop)
    elif trigger_id == 'cycle-button' and cycle_clicks and cycle_clicks > 0:
        new_cycle_active = True
        cycle_disabled = False
        if len(active_nodes) == 0:
            active_nodes.append(0)
            input_value = NODE_TO_INPUT[0]
    
    # Handle stop button
    elif trigger_id == 'stop-button' and stop_clicks and stop_clicks > 0:
        new_cycle_active = False
        cycle_disabled = True

    # Handle edit button: start editing (reset positions)
    elif trigger_id == 'edit-button' and edit_clicks and edit_clicks > 0:
        # Enter edit mode and reset stored positions
        edit_mode = True
        edit_index = 0
        node_positions = [None for _ in range(35)]
        # while editing, clear active highlighting
        active_nodes = []
        new_cycle_active = False
        cycle_disabled = True
    
    # Handle cycle interval
    elif trigger_id == 'cycle-interval' and new_cycle_active:
        if len(active_nodes) < 35:
            # Find next unactivated node
            for i in range(35):
                if i not in active_nodes:
                    active_nodes.append(i)
                    input_value = NODE_TO_INPUT[i]
                    break
    
    # Handle manual input
    elif trigger_id == 'node-input' and input_value is not None:
        input_value = max(60, min(94, int(input_value)))
        node_id = INPUT_TO_NODE[input_value]
        if node_id not in active_nodes and not all_activated:
            active_nodes.append(node_id)
        new_cycle_active = False
        cycle_disabled = True
    
    # Ensure input_value is set
    if input_value is None:
        input_value = 60

    # Handle graph click when in edit mode
    if edit_mode and trigger_id == 'node-graph' and click_data:
        try:
            point = click_data['points'][0]
            cx = float(point['x'])
            cy = float(point['y'])
        except Exception:
            cx = None
            cy = None

        if cx is not None and cy is not None:
            # assign to current edit index
            if 0 <= edit_index < 35:
                node_positions[edit_index] = [cx, cy]
                edit_index += 1

            # if finished editing all nodes, save and exit edit mode
            if edit_index >= 35:
                edit_mode = False
                # persist positions to file
                save_positions_to_file(node_positions)
                # update runtime node_data
                for i, p in enumerate(node_positions):
                    if p is not None:
                        node_data.at[i, 'x'] = p[0]
                        node_data.at[i, 'y'] = p[1]

    # Create figure
    fig = create_figure(active_nodes, node_positions=node_positions, edit_mode=edit_mode, edit_index=edit_index)
    
    return fig, input_value, active_nodes, new_cycle_active, cycle_disabled, edit_mode, edit_index, node_positions

# ============================================
# RUN THE APP
# ============================================
if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8050)