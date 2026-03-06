import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import random

# ============================================
# CONFIGURATION
# ============================================
app = dash.Dash(__name__, prevent_initial_callbacks=True)
app.title = "Node Activation System"

# Map input numbers (60-99) to node IDs (0-39)
INPUT_TO_NODE = {i: i - 60 for i in range(60, 100)}  # 60->0, 61->1, ..., 99->39
NODE_TO_INPUT = {v: k for k, v in INPUT_TO_NODE.items()}

# ============================================
# FIXED POSITIONS FOR 40 NODES
# ============================================
np.random.seed(42)  # For reproducible random positions

# Generate fixed random positions (x, y coordinates between -10 and 10)
fixed_positions = {
    i: (np.random.uniform(-10, 10), np.random.uniform(-10, 10)) 
    for i in range(40)
}

# Generate random rectangle dimensions for each node
# Width and height are independent random values between 100 and 300
random_widths = {i: random.randint(100, 300) for i in range(40)}
random_heights = {i: random.randint(100, 300) for i in range(40)}

# Create node data with fixed positions and rectangle dimensions
node_data = pd.DataFrame({
    'id': range(40),
    'x': [fixed_positions[i][0] for i in range(40)],
    'y': [fixed_positions[i][1] for i in range(40)],
    'width': [random_widths[i] for i in range(40)],
    'height': [random_heights[i] for i in range(40)]
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
                max=99,
                step=1,
                value=60
            ),
            html.Button('Random', id='random-button', n_clicks=0),
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
    dcc.Interval(id='cycle-interval', interval=1000, disabled=True),
])

# ============================================
# HELPER FUNCTIONS
# ============================================
def create_figure(active_nodes):
    """Create graph with white rectangle nodes appearing on activation"""
    fig = go.Figure()
    
    # Add all base nodes (small gray dots)
    fig.add_trace(go.Scatter(
        x=node_data['x'],
        y=node_data['y'],
        mode='markers',
        marker=dict(
            size=4,
            color='#404040',
            line=dict(width=0)
        ),
        hoverinfo='none',
        showlegend=False
    ))
    
    # Add white rectangles for active nodes
    if active_nodes:
        for node_id in active_nodes:
            node = node_data.iloc[node_id]
            
            # Draw rectangle
            fig.add_shape(
                type="rect",
                x0=node['x'] - node['width']/200,
                x1=node['x'] + node['width']/200,
                y0=node['y'] - node['height']/200,
                y1=node['y'] + node['height']/200,
                line=dict(color="white", width=1),
                fillcolor="white",
                opacity=0.9,
                layer="above"
            )
            
            # Invisible point for hover info
            fig.add_trace(go.Scatter(
                x=[node['x']],
                y=[node['y']],
                mode='markers',
                marker=dict(size=1, color='white', opacity=0),
                text=[f"Node {node_id}<br>Input: {NODE_TO_INPUT[node_id]}<br>Width: {node['width']}px<br>Height: {node['height']}px"],
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
    
    return fig

# ============================================
# MAIN CALLBACK
# ============================================
@app.callback(
    [Output('node-graph', 'figure'),
     Output('node-input', 'value'),
     Output('active-nodes', 'data'),
     Output('cycle-active', 'data'),
     Output('cycle-interval', 'disabled')],
    [Input('node-input', 'value'),
     Input('random-button', 'n_clicks'),
     Input('cycle-button', 'n_clicks'),
     Input('stop-button', 'n_clicks'),
     Input('reset-button', 'n_clicks'),
     Input('cycle-interval', 'n_intervals')],
    [State('active-nodes', 'data'),
     State('cycle-active', 'data')]
)
def update_system(input_value, random_clicks, cycle_clicks, stop_clicks, 
                  reset_clicks, interval, active_nodes, cycle_active):
    
    ctx = dash.callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
    
    # Initialize
    if active_nodes is None:
        active_nodes = []
    
    new_cycle_active = cycle_active if cycle_active else False
    cycle_disabled = not new_cycle_active
    
    # Check if all nodes are activated
    all_activated = len(active_nodes) >= 40
    
    # If all nodes are activated and cycle is active, reset and continue
    if all_activated and new_cycle_active:
        # Reset all nodes
        active_nodes = []
        input_value = 60
        
        # Start with node 0
        if len(active_nodes) == 0 and new_cycle_active:
            active_nodes.append(0)
            input_value = NODE_TO_INPUT[0]
    
    # Handle reset button
    if trigger_id == 'reset-button' and reset_clicks and reset_clicks > 0:
        active_nodes = []
        input_value = 60
        new_cycle_active = False
        cycle_disabled = True
    
    # Handle random button
    elif trigger_id == 'random-button' and random_clicks and random_clicks > 0:
        input_value = np.random.randint(60, 100)
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
    
    # Handle cycle interval
    elif trigger_id == 'cycle-interval' and new_cycle_active:
        if len(active_nodes) < 40:
            # Find next unactivated node
            for i in range(40):
                if i not in active_nodes:
                    active_nodes.append(i)
                    input_value = NODE_TO_INPUT[i]
                    break
    
    # Handle manual input
    elif trigger_id == 'node-input' and input_value is not None:
        input_value = max(60, min(99, int(input_value)))
        node_id = INPUT_TO_NODE[input_value]
        if node_id not in active_nodes and not all_activated:
            active_nodes.append(node_id)
        new_cycle_active = False
        cycle_disabled = True
    
    # Ensure input_value is set
    if input_value is None:
        input_value = 60
    
    # Create figure
    fig = create_figure(active_nodes)
    
    return fig, input_value, active_nodes, new_cycle_active, cycle_disabled

# ============================================
# RUN THE APP
# ============================================
if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8050)