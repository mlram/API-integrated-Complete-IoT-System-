import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import time

from api_client import APIClient
from device_connectivity import full_connectivity_dashboard, simulate_device_status_changes

# Page configuration
st.set_page_config(
    page_title="API Demo",
    page_icon="🔌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize API client


@st.cache_resource
def get_api_client():
    """Get API client with connection retry logic

    The client will attempt multiple URLs and display connection status
    """
    from settings import API_URL

    client = APIClient(base_url=API_URL)

    # Check if API is available
    try:
        health = client.check_health()
        if health and health.get("success", False):
            st.success(f"Connected to API at {client.base_url}")
        else:
            st.warning(
                "API health check failed, but connection was established")
    except Exception as e:
        st.error(f"Could not connect to API: {e}")
        st.info("The app will continue to retry connecting in the background")

    return client


api_client = get_api_client()

# Initialize session state for login status
if "api_logged_in" not in st.session_state:
    st.session_state.api_logged_in = False

# Main content
st.title("IoT Platform Demo")

# Show login form if not logged in
if not st.session_state.api_logged_in:
    st.subheader("Login")

    col1, col2 = st.columns([1, 2])

    with col1:
        username = st.text_input("Username", value="admin")
        password = st.text_input("Password", type="password", value="admin123")

        if st.button("Login to API"):
            with st.spinner("Logging in..."):
                success = api_client.login(
                    username=username, password=password)

                if success:
                    st.session_state.api_logged_in = True
                    st.success("Successfully logged in to API!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(
                        "Failed to login. Check credentials and API availability.")

    with col2:
        # Check API health
        health = api_client.check_health()

        st.subheader("API Health")
        if health.get("success", False):
            st.success("API is healthy")
        else:
            st.warning("API has some issues")

        # Display health details
        services = health.get("data", {})
        for service, status in services.items():
            if status:
                st.markdown(f"- ✅ {service}")
            else:
                st.markdown(f"- ❌ {service}")
else:

    user_info = api_client.get_user_info()

    if user_info:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(
                f"Logged in as: {user_info.get('username')} ({user_info.get('role')})")
            with col2:
                if st.button("Logout"):
                    st.session_state.api_logged_in = False
                    st.success("Successfully logged out!")
                    time.sleep(1)
                    st.rerun()

    tabs = st.tabs(["Connectivity", "Projects", "Devices", "Data", "Users"])
    connectivity_tab, projects_tab, devices_tab, data_tab, users_tab = tabs

    simulate_device_status_changes(api_client, interval=15, random_seed=42)

    with connectivity_tab:
        full_connectivity_dashboard(api_client)

    # Projects tab
    with projects_tab:
        st.subheader("Projects from API")

        if st.button("Refresh Projects"):
            st.rerun()

        # Get projects from API
        projects = api_client.get_projects()

        if projects:

            projects_df = pd.DataFrame(projects)
            st.dataframe(projects_df)

            project_ids = [p["project_id"] for p in projects]
            selected_project = st.selectbox(
                "Select Project for Details", project_ids)

            if selected_project:

                project_details_tab, project_devices_tab = st.tabs(
                    ["Project Details", "Project Devices"])

                with project_details_tab:

                    project = next(
                        (p for p in projects if p["project_id"] == selected_project), None)
                    if project:
                        st.subheader(f"{project['name']} Details")
                        st.write(f"**ID:** {project['project_id']}")
                        st.write(f"**Owner:** {project.get('owner', 'N/A')}")
                        st.write(
                            f"**Description:** {project.get('description', 'N/A')}")
                        st.write(
                            f"**Created:** {project.get('created_at', 'N/A')}")

                        # Delete project button (admin only)
                        if user_info.get('role') == "Admin" or project.get('owner') == user_info.get('username'):
                            if st.button("Delete Project"):
                                if st.session_state.get("confirm_delete_project") != selected_project:
                                    st.session_state.confirm_delete_project = selected_project
                                    st.warning(
                                        "Are you sure you want to delete this project? Click Delete Project again to confirm.")
                                else:
                                    success = api_client.delete_project(
                                        selected_project)
                                    if success:
                                        st.success(
                                            "Project deleted successfully!")
                                        st.session_state.confirm_delete_project = None
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error("Failed to delete project.")

                with project_devices_tab:
                    # Get devices in this project
                    project_devices = api_client.get_project_devices(
                        selected_project)
                    if project_devices:
                        st.subheader(f"Devices in {project['name']}")
                        project_devices_df = pd.DataFrame(project_devices)
                        st.dataframe(project_devices_df)
                    else:
                        st.info(
                            f"No devices found in project {project['name']}.")

                    add_to_project = st.button("Add Device to Project")
                    if add_to_project:
                        st.session_state.add_device_to_project = selected_project

            # Create a new project form
            with st.expander("Add New Project"):
                new_project_id = st.text_input(
                    "Project ID", key="new_project_id")
                new_project_name = st.text_input(
                    "Project Name", key="new_project_name")
                new_project_desc = st.text_area(
                    "Description", key="new_project_desc")

                if st.button("Add Project"):
                    if new_project_id and new_project_name:
                        success = api_client.create_project(
                            project_id=new_project_id,
                            name=new_project_name,
                            description=new_project_desc
                        )

                        if success:
                            st.success(
                                f"Project {new_project_name} added successfully!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Failed to add project")
                    else:
                        st.warning("Project ID and Name are required")
        else:
            st.warning(
                "No projects found. Add a project or check API connection.")

            # Create a new project form
            with st.expander("Add New Project", expanded=True):
                new_project_id = st.text_input(
                    "Project ID", key="new_project_id")
                new_project_name = st.text_input(
                    "Project Name", key="new_project_name")
                new_project_desc = st.text_area(
                    "Description", key="new_project_desc")

                if st.button("Add Project"):
                    if new_project_id and new_project_name:
                        success = api_client.create_project(
                            project_id=new_project_id,
                            name=new_project_name,
                            description=new_project_desc
                        )

                        if success:
                            st.success(
                                f"Project {new_project_name} added successfully!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Failed to add project")
                    else:
                        st.warning("Project ID and Name are required")

    # Devices tab
    with devices_tab:
        st.subheader("Devices from API")

        if st.button("Refresh Devices"):
            st.rerun()

        # Get devices from API
        devices = api_client.get_devices()

        if devices:

            st.write("### Device Management")

            cols = st.columns([2, 2, 2, 2, 2])
            cols[0].write("**Device ID**")
            cols[1].write("**Name**")
            cols[2].write("**Type**")
            cols[3].write("**Status**")
            cols[4].write("**Actions**")

            st.write("---")

            for device in devices:
                device_id = device.get("device_id", "")
                cols = st.columns([2, 2, 2, 2, 2])
                cols[0].write(device_id)
                cols[1].write(device.get("name", ""))
                cols[2].write(device.get("device_type", ""))

                status = device.get("status", "Unknown")
                if status == "Online":
                    cols[3].markdown(f"**:green[{status}]**")
                elif status == "Offline":
                    cols[3].markdown(f"**:red[{status}]**")
                else:
                    cols[3].write(status)

                if user_info and user_info.get('role') == 'Admin':

                    if cols[4].button("🗑️ Delete", key=f"delete_device_{device_id}"):
                        confirm_key = f"confirm_delete_device_{device_id}"
                        if st.session_state.get(confirm_key, False):

                            success = api_client.delete_device(device_id)
                            if success:
                                st.success(
                                    f"Device {device_id} deleted successfully")
                                st.session_state[confirm_key] = False
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(
                                    f"Failed to delete device {device_id}")
                                st.session_state[confirm_key] = False
                        else:
                            # Show confirmation message
                            st.session_state[confirm_key] = True
                            st.warning(
                                f"Are you sure you want to delete device {device_id}? This cannot be undone. Click Delete again to confirm.")
                else:
                    # Non-admin users cannot delete devices
                    cols[4].write("View only")

            st.write("---")

            with st.expander("View All Device Details"):
                devices_df = pd.DataFrame(devices)
                st.dataframe(devices_df)

            # Create a new device form
            with st.expander("Add New Device"):
                new_device_id = st.text_input("Device ID")
                new_device_name = st.text_input("Device Name")
                new_device_type = st.selectbox(
                    "Device Type",
                    ["Temperature Sensor", "Humidity Sensor",
                        "Motion Sensor", "Light Sensor", "Other"]
                )
                new_device_location = st.text_input("Location")

                projects = api_client.get_projects()
                project_options = [p["project_id"] for p in projects]
                project_options.insert(0, "")

                new_device_project = st.selectbox(
                    "Project (Required)",
                    project_options,
                    format_func=lambda x: f"{x} - {next((p['name'] for p in projects if p['project_id'] == x), '')}" if x else "Select a project"
                )

                if st.button("Add Device"):
                    if new_device_id and new_device_name and new_device_project:
                        success = api_client.create_device(
                            device_id=new_device_id,
                            name=new_device_name,
                            device_type=new_device_type,
                            location=new_device_location,
                            project_id=new_device_project
                        )

                        if success:
                            st.success(
                                f"Device {new_device_name} added successfully!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Failed to add device")
                    else:
                        st.warning(
                            "Device ID, Name, and Project selection are required")
        else:
            st.warning(
                "No devices found. Add a device or check API connection.")

    # Data tab
    with data_tab:
        st.subheader("Device Data from API")

        # Get devices for selection
        devices = api_client.get_devices()
        device_ids = [d["device_id"] for d in devices]

        if device_ids:

            selected_device = st.selectbox("Select Device", device_ids)

            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input(
                    "Start Date", datetime.now() - timedelta(days=1))
            with col2:
                end_date = st.date_input("End Date", datetime.now())

            data = api_client.get_device_data(
                device_id=selected_device,
                start=datetime.combine(start_date, datetime.min.time()),
                end=datetime.combine(end_date, datetime.max.time())
            )

            if data:

                st.write("Raw data structure received from API:")
                st.json(data, expanded=False)

                if 'data' in data and isinstance(data['data'], list):

                    data_points = data['data']
                    data_df = pd.DataFrame(data_points)
                else:

                    data_df = pd.DataFrame(data)

                if 'timestamp' in data_df.columns:
                    data_df['timestamp'] = pd.to_datetime(data_df['timestamp'])

                # Get latest data for the device
                latest_data = api_client.get_device_latest_data(
                    selected_device)

                # Display latest data with gauges for numeric values
                if latest_data:
                    st.subheader("Latest Readings")
                    latest_cols = st.columns(min(len(latest_data), 3))
                    col_idx = 0

                    for field, value in latest_data.items():
                        if isinstance(value, (int, float)):

                            with latest_cols[col_idx % len(latest_cols)]:

                                min_val, max_val = 0, 100
                                if 'temp' in field.lower():
                                    min_val, max_val = -20, 50
                                elif 'humid' in field.lower():
                                    min_val, max_val = 0, 100
                                elif 'pressure' in field.lower():
                                    min_val, max_val = 900, 1100

                                fig = px.gauge(
                                    value=value,
                                    min=min_val,
                                    max=max_val,
                                    title=f"{field}",
                                    labels={"value": field}
                                )
                                fig.update_layout(
                                    height=200, margin=dict(l=20, r=20, t=50, b=20))
                                st.plotly_chart(fig, use_container_width=True)
                            col_idx += 1
                        elif isinstance(value, bool):

                            with latest_cols[col_idx % len(latest_cols)]:
                                st.metric(
                                    label=field,
                                    value="ON" if value else "OFF",
                                    delta=None
                                )
                            col_idx += 1
                        else:

                            with latest_cols[col_idx % len(latest_cols)]:
                                st.metric(
                                    label=field,
                                    value=str(value),
                                    delta=None
                                )
                            col_idx += 1

                # Display raw data
                st.subheader("Raw Data")
                st.dataframe(data_df)

                st.subheader("Historical Data Visualization")

                if 'field' in data_df.columns:

                    fields = data_df['field'].unique()

                    st.write(f"Fields found in data: {', '.join(fields)}")

                    for field in fields:
                        st.subheader(f"{field.capitalize()} Data")
                        field_data = data_df[data_df['field'] == field]

                        is_temperature = "temp" in field.lower()

                        if is_temperature:

                            st.write("Temperature visualization:")

                            chart_tabs = st.tabs(
                                ["Line Chart", "Bar Chart", "Area Chart"])

                            # Line Chart tab
                            with chart_tabs[0]:
                                fig = px.line(
                                    field_data,
                                    x='timestamp',
                                    y='value',
                                    title=f"{field.capitalize()} over time",
                                    markers=True  # Show markers for better readability
                                )
                                st.plotly_chart(fig, use_container_width=True)

                            # Bar Chart tab
                            with chart_tabs[1]:
                                fig = px.bar(
                                    field_data,
                                    x='timestamp',
                                    y='value',
                                    title=f"{field.capitalize()} over time"
                                )
                                st.plotly_chart(fig, use_container_width=True)

                            # Area Chart tab
                            with chart_tabs[2]:
                                fig = px.area(
                                    field_data,
                                    x='timestamp',
                                    y='value',
                                    title=f"{field.capitalize()} over time"
                                )
                                st.plotly_chart(fig, use_container_width=True)
                        else:
                            # For non-temperature fields, keep the simple options only
                            chart_type = st.selectbox(
                                f"Select visualization for {field}",
                                ["Line Chart", "Bar Chart", "Area Chart"],
                                key=f"chart_type_simple_{field}"
                            )

                            if chart_type == "Line Chart":
                                fig = px.line(
                                    field_data,
                                    x='timestamp',
                                    y='value',
                                    title=f"{field.capitalize()} over time"
                                )
                                st.plotly_chart(fig, use_container_width=True)

                            elif chart_type == "Bar Chart":
                                fig = px.bar(
                                    field_data,
                                    x='timestamp',
                                    y='value',
                                    title=f"{field.capitalize()} over time"
                                )
                                st.plotly_chart(fig, use_container_width=True)

                            elif chart_type == "Area Chart":
                                fig = px.area(
                                    field_data,
                                    x='timestamp',
                                    y='value',
                                    title=f"{field.capitalize()} over time"
                                )
                                st.plotly_chart(fig, use_container_width=True)
                else:

                    st.write(
                        "No specific fields found in data, displaying all values")

                    # Create basic chart
                    if 'timestamp' in data_df.columns and 'value' in data_df.columns:
                        fig = px.line(
                            data_df,
                            x='timestamp',
                            y='value',
                            title="Device data over time"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning(
                            "Data format doesn't contain required fields for visualization")
            else:
                st.info(
                    f"No data available for device {selected_device} in the selected time range")
        else:
            st.warning("No devices available for data visualization")

    # Users tab
    with users_tab:
        st.subheader("User Management")

        # Only admins can see all users
        if user_info and user_info.get('role') == 'Admin':
            # Get all users
            users = api_client.get_users()

            if users:
                # Display user table
                users_df = pd.DataFrame(users)
                st.dataframe(users_df)

                # Add user deletion functionality
                st.subheader("Delete User")
                user_to_delete = st.selectbox(
                    "Select user to delete",
                    [u["username"]
                        for u in users if u["username"] != user_info.get('username')]
                )

                if st.button("Delete Selected User"):
                    if st.session_state.get("confirm_delete_user") != user_to_delete:
                        st.session_state.confirm_delete_user = user_to_delete
                        st.warning(
                            f"Are you sure you want to delete user {user_to_delete}? This cannot be undone. Click Delete again to confirm.")
                    else:
                        success = api_client.delete_user(user_to_delete)
                        if success:
                            st.success(
                                f"User {user_to_delete} deleted successfully")
                            st.session_state.confirm_delete_user = None
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"Failed to delete user {user_to_delete}")
                            st.session_state.confirm_delete_user = None

                # Add user creation functionality
                with st.expander("Add New User"):
                    new_username = st.text_input("Username")
                    new_password = st.text_input("Password", type="password")
                    new_role = st.selectbox("Role", ["Admin", "User", "Guest"])

                    if st.button("Create User"):
                        if new_username and new_password:
                            success = api_client.create_user(
                                username=new_username,
                                password=new_password,
                                role=new_role
                            )

                            if success:
                                st.success(
                                    f"User {new_username} created successfully!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Failed to create user")
                        else:
                            st.warning("Username and Password are required")
            else:
                st.warning(
                    "No users found or you don't have permission to view them.")
        else:
            st.info("Only administrators can manage users.")
            st.write("Your role: " + user_info.get('role', 'Unknown'))

# Hi
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True
)
