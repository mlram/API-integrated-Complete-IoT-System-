"""
Device Connectivity Visualization for IoT Platform

This module provides ambient visualizations for device connectivity status
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import random
import time
import math
from datetime import datetime, timedelta


def get_device_status_color(status):
    """Get color for device status"""
    status = status.lower()
    if status == "online":
        return "#4CAF50"  # Green
    elif status == "offline":
        return "#F44336"  # Red
    elif status == "warning":
        return "#FF9800"  # Orange
    elif status == "maintenance":
        return "#2196F3"  # Blue
    else:
        return "#9E9E9E"  # Grey for unknown status


def device_connectivity_graph(devices):
    """
    Create a graph visualization of connected devices

    Args:
        devices (list): List of device dictionaries
    """
    if not devices:
        st.warning("No devices available to visualize")
        return

    container = st.container()

    with container:
        st.subheader("Device Connectivity Map")

        num_devices = len(devices)
        radius = 5
        center_x = 0
        center_y = 0

        nodes_x = [center_x]
        nodes_y = [center_y]
        node_text = ["Gateway"]
        node_size = [30]
        node_color = ["#1976D2"]

        angle_step = 2 * math.pi / num_devices
        edge_x = []
        edge_y = []

        for i, device in enumerate(devices):
            angle = i * angle_step
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)

            device_id = device['device_id']
            device_status = device.get('status', 'Unknown')

            if hasattr(st.session_state, 'simulated_device_statuses') and device_id in st.session_state.simulated_device_statuses:
                device_status = st.session_state.simulated_device_statuses[device_id]

            # Add node
            nodes_x.append(x)
            nodes_y.append(y)
            node_text.append(
                f"{device['name']}<br>{device.get('device_type', 'Unknown')}<br>{device_status}")
            node_size.append(20)
            node_color.append(get_device_status_color(device_status))

            # Add edge (connection to gateway)
            edge_x.extend([center_x, x, None])
            edge_y.extend([center_y, y, None])

        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=1, color='#888'),
            hoverinfo='none',
            mode='lines'
        )

        # Create node trace
        node_trace = go.Scatter(
            x=nodes_x, y=nodes_y,
            mode='markers',
            hoverinfo='text',
            text=node_text,
            marker=dict(
                showscale=False,
                color=node_color,
                size=node_size,
                line=dict(width=2)
            )
        )

        # Create figure
        fig = go.Figure(
            data=[edge_trace, node_trace],
            layout=go.Layout(
                showlegend=False,
                hovermode='closest',
                margin=dict(b=20, l=5, r=5, t=40),
                xaxis=dict(showgrid=False, zeroline=False,
                           showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False,
                           showticklabels=False),
                height=400,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )
        )

        st.plotly_chart(fig, use_container_width=True)


def device_status_dashboard(devices):
    """
    Create a dashboard of device statuses

    Args:
        devices (list): List of device dictionaries
    """
    if not devices:
        st.warning("No devices available to display")
        return

    st.subheader("Ambient Device Status")

    cols = st.columns(4)

    for i, device in enumerate(devices):
        with cols[i % 4]:

            with st.container():

                device_id = device['device_id']
                device_status = device.get('status', 'Unknown')

                if hasattr(st.session_state, 'simulated_device_statuses') and device_id in st.session_state.simulated_device_statuses:
                    device_status = st.session_state.simulated_device_statuses[device_id]

                color = get_device_status_color(device_status)

                st.markdown(f"""
                <div style="border:1px solid #ddd; border-radius:5px; padding:10px; margin-bottom:10px;">
                    <h3 style="margin:0; font-size:16px;">{device['name']}</h3>
                    <p style="margin:2px 0; color:#666; font-size:12px;">{device.get('device_type', 'Unknown')}</p>
                    <p style="margin:2px 0; color:#666; font-size:12px;">{device.get('location', 'Unknown')}</p>
                    <div style="background-color:{color}; color:white; padding:2px 6px; border-radius:3px; display:inline-block; margin-top:5px;">
                        {device_status}
                    </div>
                </div>
                """, unsafe_allow_html=True)


def real_time_connectivity_pulse(devices):
    """
    Create a real-time connectivity pulse visualization

    Args:
        devices (list): List of device dictionaries
    """
    if not devices:
        st.warning("No devices available to visualize")
        return

    st.subheader("Real-time Connectivity Pulse")

    updated_devices = []
    for device in devices:
        device_copy = device.copy()
        device_id = device['device_id']
        if hasattr(st.session_state, 'simulated_device_statuses') and device_id in st.session_state.simulated_device_statuses:
            device_copy['status'] = st.session_state.simulated_device_statuses[device_id]
        updated_devices.append(device_copy)

    online_devices = [d for d in updated_devices if d.get(
        'status', '').lower() == 'online']
    offline_devices = [d for d in updated_devices if d.get(
        'status', '').lower() == 'offline']
    warning_devices = [d for d in updated_devices if d.get(
        'status', '').lower() == 'warning']

    online_percentage = len(online_devices) / \
        len(updated_devices) * 100 if updated_devices else 0

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=online_percentage,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Online Devices", 'font': {'size': 24}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "#4CAF50"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 50], 'color': '#FFCDD2'},
                {'range': [50, 80], 'color': '#FFECB3'},
                {'range': [80, 100], 'color': '#C8E6C9'},
            ],
        }
    ))

    fig.update_layout(
        height=250,
        margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor='rgba(0,0,0,0)'
    )

    st.plotly_chart(fig, use_container_width=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Online Devices", f"{len(online_devices)}/{len(devices)}",
                  delta=f"{online_percentage:.1f}%" if online_percentage > 0 else "0%")

    with col2:
        st.metric("Offline Devices", len(offline_devices),
                  delta=f"-{len(offline_devices)}" if len(offline_devices) > 0 else "0",
                  delta_color="inverse")

    with col3:
        st.metric("Warnings", len(warning_devices),
                  delta=f"{len(warning_devices)}" if len(
                      warning_devices) > 0 else "0",
                  delta_color="off")


def device_data_pulse(device_data):
    """
    Create a pulsing visualization of recent device data

    Args:
        device_data (dict): Dictionary with device_id and data list
    """
    if not device_data or 'data' not in device_data or not device_data['data']:
        st.warning("No device data available to visualize")
        return

    st.subheader(
        f"Data Pulse: {device_data.get('device_id', 'Unknown Device')}")

    data = device_data['data']
    df = pd.DataFrame(data)

    if 'timestamp' not in df.columns or 'value' not in df.columns:
        st.warning("Data format is not as expected. Missing required columns.")
        return

    df['timestamp'] = pd.to_datetime(df['timestamp'])

    df = df.sort_values('timestamp')

    df = df.tail(20)

    fig = go.Figure()

    # Add main data line
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['value'],
        mode='lines+markers',
        name='Data',
        line=dict(color='#2196F3', width=3),
        marker=dict(size=8, color='#2196F3')
    ))

    # Add pulsing area below line
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=[0] * len(df),
        mode='none',
        fill='tonexty',
        fillcolor='rgba(33, 150, 243, 0.2)',
        hoverinfo='none'
    ))

    # Update layout
    fig.update_layout(
        height=250,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            showgrid=False,
            showticklabels=True,
            title=None
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(0,0,0,0.1)',
            title=None
        ),
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

    # Display latest value
    if not df.empty:
        latest = df.iloc[-1]
        # Get the field name (if it exists)
        field_name = latest.get('field', 'Value') if hasattr(
            latest, 'get') else 'Value'

        st.metric(
            label=f"Latest {field_name} reading",
            value=f"{latest['value']}",
            delta=f"{latest['value'] - df.iloc[-2]['value']:.2f}" if len(
                df) > 1 else None
        )


def full_connectivity_dashboard(api_client):
    """
    Create a full connectivity dashboard using all visualizations

    Args:
        api_client: API client instance to fetch data
    """
    st.title("Device Connectivity Dashboard")

    # Get all devices
    devices = api_client.get_devices()

    if not devices:
        st.warning("No devices found. Please add devices first.")
        return

    # Create tabs for different visualizations
    tab1, tab2, tab3, tab4 = st.tabs([
        "Network Map", "Status Dashboard", "Connectivity Pulse", "Data Pulse"
    ])

    with tab1:
        device_connectivity_graph(devices)

    with tab2:
        device_status_dashboard(devices)

    with tab3:
        real_time_connectivity_pulse(devices)

    with tab4:
        # Select a device for data pulse
        device_id = st.selectbox(
            "Select Device",
            options=[d['device_id'] for d in devices],
            format_func=lambda x: next(
                (d['name'] for d in devices if d['device_id'] == x), x)
        )

        # Get device data
        if device_id:
            device_data = api_client.get_device_data(device_id)
            device_data_pulse(device_data)


def simulate_device_status_changes(api_client, interval=5, random_seed=None):
    """Simulate random changes to device statuses for demo purposes"""
    if random_seed is not None:
        random.seed(random_seed)

    if 'last_simulation' not in st.session_state:
        st.session_state.last_simulation = time.time() - interval

    current_time = time.time()
    if current_time - st.session_state.last_simulation < interval:
        return

    # Get all devices
    devices = api_client.get_devices()

    if not devices:
        return

    if 'simulated_device_statuses' not in st.session_state:
        st.session_state.simulated_device_statuses = {}

    for device in devices:
        device_id = device['device_id']
        if random.random() < 0.1:

            statuses = ["Online", "Offline", "Warning", "Maintenance"]
            weights = [0.7, 0.1, 0.15, 0.05]
            new_status = random.choices(statuses, weights)[0]

            # Store the new status in session state
            st.session_state.simulated_device_statuses[device_id] = new_status

    # Update last simulation time
    st.session_state.last_simulation = current_time
