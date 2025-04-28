import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import logging
import json
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define available widget types
WIDGET_TYPES = {
    'gauge': 'Gauge Chart',
    'line_chart': 'Line Chart',
    'bar_chart': 'Bar Chart',
    'table': 'Data Table',
    'metric': 'Value Metric',
    'device_status': 'Device Status',
    'comparison': 'Devices Comparison'
}


class Visualization:
    def __init__(self, influx_handler):
        """
        Initialize visualization handler

        Args:
            influx_handler: InfluxDB handler for data retrieval
        """
        self.influx_handler = influx_handler
        self.layouts_file = "dashboard_layouts.json"

        # Initialize layouts from file or use default
        if os.path.exists(self.layouts_file):
            try:
                with open(self.layouts_file, 'r') as f:
                    self.layouts = json.load(f)
            except Exception as e:
                logger.error(f"Error loading layouts: {e}")
                self.layouts = self._get_default_layouts()
        else:
            self.layouts = self._get_default_layouts()

    def _get_default_layouts(self):
        """Get default dashboard layouts"""
        return {
            "default": {
                "name": "Default Layout",
                "description": "Standard dashboard with key metrics",
                "widgets": [
                    {"id": "device_status", "type": "device_status",
                        "name": "Device Status", "size": "large", "row": 0, "col": 0},
                    {"id": "temperature", "type": "line_chart", "name": "Temperature",
                        "device": "all", "metric": "temperature", "size": "medium", "row": 1, "col": 0},
                    {"id": "humidity", "type": "line_chart", "name": "Humidity", "device": "all",
                        "metric": "humidity", "size": "medium", "row": 1, "col": 1},
                    {"id": "latest_data", "type": "table", "name": "Latest Data",
                        "device": "all", "size": "large", "row": 2, "col": 0}
                ]
            },
            "compact": {
                "name": "Compact View",
                "description": "Smaller widgets for more information at a glance",
                "widgets": [
                    {"id": "temp_gauge", "type": "gauge", "name": "Temperature", "device": "all",
                        "metric": "temperature", "size": "small", "row": 0, "col": 0},
                    {"id": "humidity_gauge", "type": "gauge", "name": "Humidity",
                        "device": "all", "metric": "humidity", "size": "small", "row": 0, "col": 1},
                    {"id": "pressure_gauge", "type": "gauge", "name": "Pressure",
                        "device": "all", "metric": "pressure", "size": "small", "row": 0, "col": 2},
                    {"id": "device_status", "type": "device_status",
                        "name": "Device Status", "size": "medium", "row": 1, "col": 0},
                    {"id": "temperature", "type": "line_chart", "name": "Temperature",
                        "device": "all", "metric": "temperature", "size": "medium", "row": 1, "col": 1},
                    {"id": "latest_data", "type": "table", "name": "Latest Data",
                        "device": "all", "size": "large", "row": 2, "col": 0}
                ]
            }
        }

    def save_layouts(self):
        """Save layouts to file"""
        try:
            with open(self.layouts_file, 'w') as f:
                json.dump(self.layouts, f)
            return True
        except Exception as e:
            logger.error(f"Error saving layouts: {e}")
            return False

    def get_layouts(self):
        """Get all available layouts"""
        return self.layouts

    def get_layout(self, layout_id):
        """Get specific layout by ID"""
        return self.layouts.get(layout_id, self.layouts.get("default"))

    def create_layout(self, layout_id, name, description, widgets=None):
        """Create a new layout"""
        if widgets is None:
            widgets = []

        self.layouts[layout_id] = {
            "name": name,
            "description": description,
            "widgets": widgets
        }
        self.save_layouts()
        return True

    def update_layout(self, layout_id, updates):
        """Update an existing layout"""
        if layout_id in self.layouts:
            self.layouts[layout_id].update(updates)
            self.save_layouts()
            return True
        return False

    def delete_layout(self, layout_id):
        """Delete a layout"""
        if layout_id in self.layouts and layout_id != "default":
            del self.layouts[layout_id]
            self.save_layouts()
            return True
        return False

    def add_widget_to_layout(self, layout_id, widget_data):
        """Add a widget to a layout"""
        if layout_id in self.layouts:
            # Generate a widget ID if not provided
            if "id" not in widget_data:
                widget_data["id"] = f"widget_{len(self.layouts[layout_id]['widgets'])}"

            self.layouts[layout_id]["widgets"].append(widget_data)
            self.save_layouts()
            return True
        return False

    def update_widget_in_layout(self, layout_id, widget_id, updates):
        """Update a widget in a layout"""
        if layout_id in self.layouts:
            for i, widget in enumerate(self.layouts[layout_id]["widgets"]):
                if widget["id"] == widget_id:
                    self.layouts[layout_id]["widgets"][i].update(updates)
                    self.save_layouts()
                    return True
        return False

    def delete_widget_from_layout(self, layout_id, widget_id):
        """Delete a widget from a layout"""
        if layout_id in self.layouts:
            self.layouts[layout_id]["widgets"] = [
                w for w in self.layouts[layout_id]["widgets"] if w["id"] != widget_id
            ]
            self.save_layouts()
            return True
        return False

    def display_gauge(self, title, value, min_val, max_val, label=''):
        """
        Display a gauge chart

        Args:
            title (str): Chart title
            value (float): Current value
            min_val (float): Minimum value
            max_val (float): Maximum value
            label (str): Value label
        """
        try:
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=float(value),
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': title},
                gauge={
                    'axis': {'range': [min_val, max_val]},
                    'bar': {'color': "#3498db"},
                    'steps': [
                        {'range': [min_val, min_val +
                                   (max_val - min_val) / 3], 'color': "#e74c3c"},
                        {'range': [min_val + (max_val - min_val) / 3, min_val + 2 * (
                            max_val - min_val) / 3], 'color': "#f39c12"},
                        {'range': [
                            min_val + 2 * (max_val - min_val) / 3, max_val], 'color': "#2ecc71"}
                    ],
                }
            ))

            fig.update_layout(
                height=200,
                margin=dict(l=10, r=10, t=50, b=10),
            )

            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            logger.error(f"Error displaying gauge: {e}")
            st.error(f"Error displaying gauge: {e}")

    def display_time_series(self, data, device_id=None):
        """
        Display time series data

        Args:
            data (pd.DataFrame): Time series data
            device_id (str): Device ID for title
        """
        try:
            if data is None or data.empty:
                st.info("No data available for the selected time range")
                return

            # Group by field for multiple lines
            fields = data['field'].unique() if 'field' in data.columns else []

            for field in fields:
                field_data = data[data['field'] == field]

                # Check if the field values are numeric
                try:
                    field_data['value'] = pd.to_numeric(field_data['value'])
                    is_numeric = True
                except (ValueError, TypeError):
                    is_numeric = False

                if is_numeric:
                    # Create line chart for numeric data
                    fig = px.line(
                        field_data,
                        x='timestamp',
                        y='value',
                        title=f"{field} Over Time" +
                        (f" - {device_id}" if device_id else "")
                    )

                    fig.update_layout(
                        xaxis_title="Time",
                        yaxis_title=field,
                        height=300,
                        margin=dict(l=10, r=10, t=50, b=10),
                    )

                    st.plotly_chart(fig, use_container_width=True)
                else:
                    # Display text data differently
                    st.subheader(f"{field} Values" +
                                 (f" - {device_id}" if device_id else ""))

                    # Sort by timestamp
                    field_data = field_data.sort_values(
                        'timestamp', ascending=False)

                    # Display as a table
                    st.dataframe(
                        field_data[['timestamp', 'value']].rename(
                            columns={'timestamp': 'Time', 'value': field}),
                        use_container_width=True
                    )
        except Exception as e:
            logger.error(f"Error displaying time series: {e}")
            st.error(f"Error displaying time series: {e}")

    def display_device_status(self, devices, statuses):
        """
        Display device status dashboard

        Args:
            devices (list): List of device documents
            statuses (dict): Dictionary of device statuses
        """
        try:
            # Create column layout
            cols = st.columns(3)

            # Display device status boxes
            for i, device in enumerate(devices):
                device_id = device['device_id']
                device_name = device['name']
                device_type = device.get('device_type', 'Unknown')
                location = device.get('location', 'Unknown')

                # Get status
                status = statuses.get(device_id, 'Offline')
                status_color = "green" if status == 'Online' else "red"

                # Display in columns
                with cols[i % 3]:
                    st.markdown(
                        f"""
                        <div style="padding: 10px; border: 1px solid #ddd; border-radius: 5px; margin-bottom: 10px;">
                            <h3>{device_name}</h3>
                            <p><strong>ID:</strong> {device_id}</p>
                            <p><strong>Type:</strong> {device_type}</p>
                            <p><strong>Location:</strong> {location}</p>
                            <p><strong>Status:</strong> <span style="color:{status_color};">{status}</span></p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
        except Exception as e:
            logger.error(f"Error displaying device status: {e}")
            st.error(f"Error displaying device status: {e}")

    def display_metric_comparison(self, device_ids, metric, start_time, end_time):
        """
        Display comparison of a metric across multiple devices

        Args:
            device_ids (list): List of device IDs
            metric (str): Metric to compare
            start_time (datetime): Start time
            end_time (datetime): End time
        """
        try:
            # Get data for each device
            all_data = []

            for device_id in device_ids:
                device_data = self.influx_handler.get_device_data(
                    device_id=device_id,
                    start_time=start_time,
                    end_time=end_time
                )

                if device_data is not None and not device_data.empty:
                    # Filter for specific metric
                    if 'field' in device_data.columns:
                        metric_data = device_data[device_data['field'] == metric]
                        if not metric_data.empty:
                            # Add device ID column
                            metric_data['device_id'] = device_id
                            all_data.append(metric_data)

            if all_data:
                # Combine data
                combined_data = pd.concat(all_data)

                # Create comparison chart
                fig = px.line(
                    combined_data,
                    x='timestamp',
                    y='value',
                    color='device_id',
                    title=f"{metric} Comparison Across Devices"
                )

                fig.update_layout(
                    xaxis_title="Time",
                    yaxis_title=metric,
                    height=400,
                    margin=dict(l=10, r=10, t=50, b=10),
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(
                    f"No {metric} data available for the selected devices and time range")
        except Exception as e:
            logger.error(f"Error displaying metric comparison: {e}")
            st.error(f"Error displaying metric comparison: {e}")

    def display_latest_values_table(self, devices):
        """
        Display table of latest values for all devices

        Args:
            devices (list): List of device documents
        """
        try:
            # Get latest values for each device
            latest_data = []

            for device in devices:
                device_id = device['device_id']
                device_name = device['name']

                # Get latest data
                device_latest = self.influx_handler.get_latest_data(device_id)

                if device_latest:
                    # Add device info
                    device_latest['Device ID'] = device_id
                    device_latest['Device Name'] = device_name

                    # Add to list
                    latest_data.append(device_latest)

            if latest_data:
                # Convert to DataFrame
                df = pd.DataFrame(latest_data)

                # Reorder columns to put Device ID and Name first
                cols = df.columns.tolist()
                cols = ['Device ID', 'Device Name'] + \
                    [col for col in cols if col not in ['Device ID', 'Device Name']]

                # Display table
                st.dataframe(df[cols], use_container_width=True)
            else:
                st.info("No data available for any devices")
        except Exception as e:
            logger.error(f"Error displaying latest values table: {e}")
            st.error(f"Error displaying latest values table: {e}")

    def display_bar_chart(self, data, title, x_field, y_field, color_field=None):
        """
        Display a bar chart

        Args:
            data (pd.DataFrame): Data for the chart
            title (str): Chart title
            x_field (str): Field for x-axis
            y_field (str): Field for y-axis
            color_field (str): Field for color grouping
        """
        try:
            if data is None or data.empty:
                st.info("No data available for the bar chart")
                return

            # Create bar chart
            if color_field and color_field in data.columns:
                fig = px.bar(
                    data,
                    x=x_field,
                    y=y_field,
                    color=color_field,
                    title=title
                )
            else:
                fig = px.bar(
                    data,
                    x=x_field,
                    y=y_field,
                    title=title
                )

            fig.update_layout(
                xaxis_title=x_field,
                yaxis_title=y_field,
                height=300,
                margin=dict(l=10, r=10, t=50, b=10),
            )

            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            logger.error(f"Error displaying bar chart: {e}")
            st.error(f"Error displaying bar chart: {e}")

    def display_metric_card(self, title, value, delta=None, delta_color="normal"):
        """
        Display a metric card

        Args:
            title (str): Metric title
            value: Metric value
            delta: Change in value (optional)
            delta_color (str): Color of delta (normal, inverse, off)
        """
        try:
            st.metric(label=title, value=value,
                      delta=delta, delta_color=delta_color)
        except Exception as e:
            logger.error(f"Error displaying metric card: {e}")
            st.error(f"Error displaying metric card: {e}")

    def render_dashboard(self, layout_id, devices, start_time, end_time):
        """
        Render a complete dashboard based on layout configuration

        Args:
            layout_id (str): ID of the layout to render
            devices (list): List of device documents
            start_time (datetime): Start time for data queries
            end_time (datetime): End time for data queries
        """
        try:
            # Get layout configuration
            layout = self.get_layout(layout_id)

            if not layout:
                st.error(f"Layout '{layout_id}' not found.")
                return

            # Display layout name and description
            st.header(layout["name"])
            st.write(layout["description"])

            # Organize widgets by row
            widgets_by_row = {}
            for widget in layout["widgets"]:
                row = widget.get("row", 0)
                if row not in widgets_by_row:
                    widgets_by_row[row] = []
                widgets_by_row[row].append(widget)

            # Sort rows
            sorted_rows = sorted(widgets_by_row.keys())

            # Get device statuses
            device_statuses = {}
            device_ids = [device["device_id"] for device in devices]
            for device_id in device_ids:
                device_statuses[device_id] = self.influx_handler._get_device_status(
                    device_id) if hasattr(self.influx_handler, '_get_device_status') else 'Unknown'

            # Render widgets row by row
            for row_num in sorted_rows:
                row_widgets = widgets_by_row[row_num]

                # Determine columns based on widget sizes
                cols = self._create_columns_for_widgets(row_widgets)

                # Render widgets in this row
                for i, widget in enumerate(row_widgets):
                    widget_type = widget.get("type")
                    widget_name = widget.get("name", f"Widget {i+1}")
                    device_id = widget.get("device", "all")
                    metric = widget.get("metric")

                    # Select the appropriate column based on col index
                    col_idx = min(widget.get("col", i), len(cols) - 1)
                    with cols[col_idx]:
                        st.subheader(widget_name)

                        # Render based on widget type
                        if widget_type == "gauge" and metric:
                            self._render_gauge_widget(
                                widget, device_id, devices)

                        elif widget_type == "line_chart" and metric:
                            self._render_line_chart_widget(
                                widget, device_id, devices, start_time, end_time)

                        elif widget_type == "bar_chart" and metric:
                            self._render_bar_chart_widget(
                                widget, device_id, devices, start_time, end_time)

                        elif widget_type == "table":
                            self._render_table_widget(
                                widget, device_id, devices)

                        elif widget_type == "metric" and metric:
                            self._render_metric_widget(
                                widget, device_id, devices)

                        elif widget_type == "device_status":
                            self._render_device_status_widget(
                                widget, devices, device_statuses)

                        elif widget_type == "comparison" and metric:
                            self._render_comparison_widget(
                                widget, devices, start_time, end_time)

                        else:
                            st.warning(f"Unknown widget type: {widget_type}")

        except Exception as e:
            logger.error(f"Error rendering dashboard: {e}")
            st.error(f"Error rendering dashboard: {e}")

    def _create_columns_for_widgets(self, widgets):
        """Create columns based on widget configurations"""
        # Get unique column indices
        col_indices = sorted(set(widget.get("col", i)
                             for i, widget in enumerate(widgets)))
        num_cols = max(col_indices) + 1 if col_indices else len(widgets)

        # Create columns
        return st.columns(num_cols)

    def _render_gauge_widget(self, widget, device_id, devices):
        """Render a gauge chart widget"""
        metric = widget.get("metric")
        min_val = widget.get("min", 0)
        max_val = widget.get("max", 100)

        if device_id == "all":
            # Show the first device with this metric
            for device in devices:
                latest = self.influx_handler.get_latest_data(
                    device["device_id"])
                if latest and metric in latest:
                    value = latest[metric]
                    self.display_gauge(metric, value, min_val, max_val)
                    break
            else:
                st.info(f"No data available for {metric}")
        else:
            # Show specific device
            latest = self.influx_handler.get_latest_data(device_id)
            if latest and metric in latest:
                value = latest[metric]
                self.display_gauge(metric, value, min_val, max_val)
            else:
                st.info(f"No data available for {device_id} - {metric}")

    def _render_line_chart_widget(self, widget, device_id, devices, start_time, end_time):
        """Render a line chart widget"""
        metric = widget.get("metric")

        if device_id == "all":
            # Compare this metric across devices
            self.display_metric_comparison(
                [d["device_id"] for d in devices],
                metric,
                start_time,
                end_time
            )
        else:
            # Show for specific device
            data = self.influx_handler.get_device_data(
                device_id=device_id,
                start_time=start_time,
                end_time=end_time,
                measurement=metric
            )

            if data is not None and not data.empty:
                self.display_time_series(data, device_id)
            else:
                st.info(f"No data available for {device_id} - {metric}")

    def _render_bar_chart_widget(self, widget, device_id, devices, start_time, end_time):
        """Render a bar chart widget"""
        metric = widget.get("metric")

        # Get data similar to line chart
        if device_id == "all":
            # Aggregate data across devices
            all_data = []
            for device in devices:
                data = self.influx_handler.get_device_data(
                    device_id=device["device_id"],
                    start_time=start_time,
                    end_time=end_time,
                    measurement=metric
                )

                if data is not None and not data.empty:
                    # Add device name
                    data['device'] = device["name"]
                    all_data.append(data)

            if all_data:
                combined_data = pd.concat(all_data)
                # Group by device and take mean or latest
                summary = combined_data.groupby(
                    'device')['value'].mean().reset_index()
                self.display_bar_chart(
                    summary, f"{metric} by Device", "device", "value")
            else:
                st.info(f"No data available for {metric}")
        else:
            # Single device - group by time period
            data = self.influx_handler.get_device_data(
                device_id=device_id,
                start_time=start_time,
                end_time=end_time,
                measurement=metric
            )

            if data is not None and not data.empty:
                # Group by day
                data['day'] = data['timestamp'].dt.date
                summary = data.groupby('day')['value'].mean().reset_index()
                self.display_bar_chart(
                    summary, f"{metric} by Day - {device_id}", "day", "value")
            else:
                st.info(f"No data available for {device_id} - {metric}")

    def _render_table_widget(self, widget, device_id, devices):
        """Render a table widget"""
        if device_id == "all":
            self.display_latest_values_table(devices)
        else:
            # Find device in the list
            device = next(
                (d for d in devices if d["device_id"] == device_id), None)
            if device:
                self.display_latest_values_table([device])
            else:
                st.info(f"Device {device_id} not found")

    def _render_metric_widget(self, widget, device_id, devices):
        """Render a metric widget"""
        metric = widget.get("metric")

        if device_id == "all":
            # Show average across devices
            values = []
            for device in devices:
                latest = self.influx_handler.get_latest_data(
                    device["device_id"])
                if latest and metric in latest:
                    try:
                        values.append(float(latest[metric]))
                    except (ValueError, TypeError):
                        pass

            if values:
                avg_value = sum(values) / len(values)
                self.display_metric_card(f"Avg {metric}", f"{avg_value:.2f}")
            else:
                st.info(f"No data available for {metric}")
        else:
            # Show for specific device
            latest = self.influx_handler.get_latest_data(device_id)
            if latest and metric in latest:
                self.display_metric_card(metric, latest[metric])
            else:
                st.info(f"No data available for {device_id} - {metric}")

    def _render_device_status_widget(self, widget, devices, statuses):
        """Render a device status widget"""
        self.display_device_status(devices, statuses)

    def _render_comparison_widget(self, widget, devices, start_time, end_time):
        """Render a device comparison widget"""
        metric = widget.get("metric")
        device_ids = [d["device_id"] for d in devices]
        self.display_metric_comparison(
            device_ids, metric, start_time, end_time)
