import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import numpy as np

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

# Create node data with fixed positions
node_data = pd.DataFrame({
    'id': range(40),
    'x': [fixed_positions[i][0] for i in range(40)],
    'y': [fixed_positions[i][1] for i in range(40)]
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
                color: #ffffff;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            .header {
                background: #2d2d2d;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                text-align: center;
                color: #ffffff;
                border: 1px solid #404040;
            }
            .header h2 {
                color: #ffffff;
            }
            .header p {
                color: #b0b0b0 !important;
            }
            .control-panel {
                background: #2d2d2d;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                border: 1px solid #404040;
            }
            .input-group {
                display: flex;
                align-items: center;
                gap: 10px;
                flex-wrap: wrap;
                justify-content: center;
            }
            label {
                color: #ffffff;
            }
            input {
                background: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555 !important;
            }
            button {
                padding: 10px 20px;
                font-size: 14px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                background: #007bff;
                color: white;
            }
            button:hover {
                background: #0056b3;
            }
            .status {
                margin-top: 15px;
                padding: 10px;
                background: #3d3d3d;
                border-radius: 4px;
                text-align: center;
                color: #ffffff;
                border: 1px solid #555;
            }
            .footer {
                text-align: center;
                margin-top: 20px;
                color: #b0b0b0;
                font-size: 12px;
            }
            .completion-message {
                background: #28a745;
                color: white;
                padding: 10px;
                border-radius: 4px;
                margin-top: 10px;
                font-weight: bold;
                text-align: center;
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
    # Header
    html.Div(className='header', children=[
        html.H2("Node Activation System", style={'margin': 0}),
        html.P("Enter a number between 60-99", style={'margin': '5px 0 0 0', 'color': '#b0b0b0'})
    ]),
    
    # Control Panel
    html.Div(className='control-panel', children=[
        html.Div(className='input-group', children=[
            html.Div([
                html.Label("Input:", style={'fontWeight': 'bold', 'marginRight': '10px'}),
                dcc.Input(
                    id='node-input',
                    type='number',
                    min=60,
                    max=99,
                    step=1,
                    value=60,
                    style={
                        'width': '100px', 'height': '35px', 'fontSize': 16,
                        'padding': '5px', 'borderRadius': '4px',
                        'border': '1px solid #555',
                        'backgroundColor': '#3d3d3d',
                        'color': '#ffffff'
                    }
                ),
            ]),
            
            html.Button('Random', id='random-button', n_clicks=0),
            html.Button('Cycle', id='cycle-button', n_clicks=0),
            html.Button('Stop', id='stop-button', n_clicks=0),
            html.Button('Reset', id='reset-button', n_clicks=0),
        ]),
        
        # Status
        html.Div(id='status', className='status'),
        html.Div(id='completion-message'),
    ]),
    
    # Graph with black background container
    html.Div(className='graph-container', children=[
        dcc.Graph(
            id='node-graph', 
            style={'height': '500px', 'backgroundColor': '#000000'},
            config={'displayModeBar': False}  # Hide plotly toolbar for cleaner look
        ),
    ]),
    
    # Hidden state
    dcc.Store(id='active-nodes', data=[]),  # Track all active nodes
    dcc.Store(id='cycle-active', data=False),
    dcc.Interval(id='cycle-interval', interval=1000, disabled=True),
    
    # Footer
    html.Div(className='footer', children=[
        "40 Nodes | Inputs 60-99 | System restarts when all nodes are activated"
    ])
])

# ============================================
# HELPER FUNCTIONS
# ============================================
def create_figure(active_nodes):
    """Create graph with active nodes highlighted on black background"""
    fig = go.Figure()
    
    # Color mapping - red for active, dark gray for inactive (to stand out on black)
    node_colors = []
    node_sizes = []
    node_line_colors = []
    
    for i in range(40):
        if i in active_nodes:
            node_colors.append('#ff4444')  # Bright red for active
            node_sizes.append(14)
            node_line_colors.append('#ffffff')  # White border for active
        else:
            node_colors.append('#404040')  # Dark gray for inactive (visible on black)
            node_sizes.append(8)
            node_line_colors.append('#666666')  # Light gray border
    
    # Add nodes
    fig.add_trace(go.Scatter(
        x=node_data['x'],
        y=node_data['y'],
        mode='markers',
        marker=dict(
            size=node_sizes,
            color=node_colors,
            line=dict(width=1, color=node_line_colors)
        ),
        text=[f"Node {i}<br>Input: {NODE_TO_INPUT[i]}" for i in range(40)],
        hoverinfo='text',
        hoverlabel=dict(
            bgcolor='#2d2d2d',
            font=dict(color='white')
        ),
        showlegend=False
    ))
    
    # Layout with black background
    fig.update_layout(
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            range=[-12, 12],
            showline=False
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            range=[-12, 12],
            showline=False
        ),
        plot_bgcolor='#000000',  # Black background
        paper_bgcolor='#000000',  # Black background for the entire figure
        height=450,
        margin=dict(l=20, r=20, t=20, b=20),
        font=dict(color='#ffffff')  # White text if any appears
    )
    
    return fig

# ============================================
# MAIN CALLBACK
# ============================================
@app.callback(
    [Output('node-graph', 'figure'),
     Output('status', 'children'),
     Output('completion-message', 'children'),
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
    completion_message = ""
    
    # Check if all nodes are activated and restart if needed
    all_activated = len(active_nodes) >= 40
    
    if all_activated and trigger_id != 'reset-button':
        # System completed - show message and reset
        active_nodes = []
        input_value = 60
        new_cycle_active = False
        cycle_disabled = True
        completion_message = html.Div("✨ All nodes activated! System restarted.", 
                                      className='completion-message')
    
    # Handle reset button
    if trigger_id == 'reset-button' and reset_clicks and reset_clicks > 0:
        active_nodes = []
        input_value = 60
        new_cycle_active = False
        cycle_disabled = True
        completion_message = ""
    
    # Handle random button
    elif trigger_id == 'random-button' and random_clicks and random_clicks > 0 and not all_activated:
        input_value = np.random.randint(60, 100)
        node_id = INPUT_TO_NODE[input_value]
        if node_id not in active_nodes:
            active_nodes.append(node_id)
        new_cycle_active = False
        cycle_disabled = True
    
    # Handle cycle button
    elif trigger_id == 'cycle-button' and cycle_clicks and cycle_clicks > 0 and not all_activated:
        new_cycle_active = True
        cycle_disabled = False
    
    # Handle stop button
    elif trigger_id == 'stop-button' and stop_clicks and stop_clicks > 0:
        new_cycle_active = False
        cycle_disabled = True
    
    # Handle cycle interval
    elif trigger_id == 'cycle-interval' and new_cycle_active and not all_activated:
        if len(active_nodes) < 40:
            # Find next unactivated node
            for i in range(40):
                if i not in active_nodes:
                    active_nodes.append(i)
                    input_value = NODE_TO_INPUT[i]
                    break
    
    # Handle manual input
    elif trigger_id == 'node-input' and input_value is not None and not all_activated:
        input_value = max(60, min(99, int(input_value)))
        node_id = INPUT_TO_NODE[input_value]
        if node_id not in active_nodes:
            active_nodes.append(node_id)
        new_cycle_active = False
        cycle_disabled = True
    
    # Ensure input_value is set
    if input_value is None:
        input_value = 60
    
    # Create figure
    fig = create_figure(active_nodes)
    
    # Create status message
    active_count = len(active_nodes)
    if active_count == 0:
        status = "No nodes activated yet"
    elif active_count == 40:
        status = "🎉 All 40 nodes activated! System ready to restart."
    else:
        status = f"{active_count} of 40 nodes activated"
    
    # Sort active nodes for display (only show if less than 40)
    if active_count < 40:
        active_nodes_sorted = sorted(active_nodes)
        status_display = html.Div([
            html.Div(status, style={'fontWeight': 'bold', 'marginBottom': '5px'}),
            html.Div(f"Active: {', '.join([str(i) for i in active_nodes_sorted[:15]])}" + 
                     ("..." if len(active_nodes_sorted) > 15 else ""))
        ])
    else:
        status_display = html.Div([
            html.Div(status, style={'fontWeight': 'bold', 'color': '#28a745'})
        ])
    
    return fig, status_display, completion_message, input_value, active_nodes, new_cycle_active, cycle_disabled

# ============================================
# RUN THE APP
# ============================================
if __name__ == '__main__':
    print("=" * 50)
    print("NODE ACTIVATION SYSTEM")
    print("=" * 50)
    print("\nFeatures:")
    print("• 40 nodes with fixed random positions")
    print("• Black background for node map")
    print("• Inputs 60-99 map to nodes 0-39")
    print("• Nodes stay active once highlighted")
    print("• System auto-restarts when all nodes activated")
    print("• NO node names or values displayed")
    print("\nControls:")
    print("• Manual input (60-99)")
    print("• Random - activates random node")
    print("• Cycle - activates one new node per second")
    print("• Stop - stops cycling")
    print("• Reset - clears all activations")
    print("\n" + "=" * 50)
    print("\nStarting server...")
    print("http://127.0.0.1:8050")
    print("\n" + "=" * 50)
    
    app.run(debug=True, host='127.0.0.1', port=8050)