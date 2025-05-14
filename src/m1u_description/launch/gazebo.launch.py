import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, TimerAction
from launch.substitutions import LaunchConfiguration, Command, FindExecutable
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

def generate_launch_description():
    # Get the share directory of your m1u_description package
    m1u_description_pkg_share_dir = get_package_share_directory('m1u_description')

    # --- Launch Arguments ---
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time', default_value='true',
        description='Use simulation (Gazebo) clock if true'
    )
    # World file argument (currently, gz_sim_server_process uses default world)
    world_file_arg = DeclareLaunchArgument(
        'world',
        default_value=os.path.join(m1u_description_pkg_share_dir, 'worlds', 'empty.world'),
        description='Full path to the Gazebo world file to load.'
    )

    # --- Robot Description ---
    xacro_file_path = os.path.join(m1u_description_pkg_share_dir, 'urdf', 'm1u_robot.urdf.xacro')
    robot_description_content = ParameterValue(Command(['xacro ', xacro_file_path]), value_type=str)

    # --- Construct Environment Variables for Gz Sim Processes ---
    # Path to the directory containing your 'm1u_description' model directory
    # This is .../install/m1u_description/share
    package_model_parent_dir = os.path.abspath(os.path.join(m1u_description_pkg_share_dir, '..'))

    # Get any existing GZ_SIM_RESOURCE_PATH from the environment (e.g., from /opt/ros/jazzy/setup.bash)
    existing_gz_resource_path = os.environ.get('GZ_SIM_RESOURCE_PATH', '')
    if not existing_gz_resource_path: # Fallback to deprecated IGN var if GZ_SIM is not set
        existing_gz_resource_path = os.environ.get('IGN_GAZEBO_RESOURCE_PATH', '')
    
    # Construct the new resource path string
    # Prepend your package's model parent directory to the existing path
    new_gz_sim_resource_path = package_model_parent_dir
    if existing_gz_resource_path:
        # Avoid adding duplicate paths if it's already there (unlikely for this specific custom path)
        if package_model_parent_dir not in existing_gz_resource_path.split(':'):
            new_gz_sim_resource_path = f"{package_model_parent_dir}:{existing_gz_resource_path}"
        else:
            new_gz_sim_resource_path = existing_gz_resource_path # It was already included

    # Other critical environment variables from the current environment
    current_gz_config_path = os.environ.get('GZ_CONFIG_PATH', '')
    current_ld_library_path = os.environ.get('LD_LIBRARY_PATH', '')
    current_path_env = os.environ.get('PATH', '')
    current_home_env = os.environ.get('HOME', '')
    current_display_env = os.environ.get('DISPLAY', '')
    current_wayland_display_env = os.environ.get('WAYLAND_DISPLAY', '') # For WSLg
    if not current_home_env: # Fallback for HOME
        try:
            current_home_env = '/home/' + os.getlogin()
        except OSError:
            current_home_env = os.path.expanduser("~")

    # Path to the 'gz' command-line tool
    gz_executable_explicit_path = "/opt/ros/jazzy/opt/gz_tools_vendor/bin/gz"

    # Shared environment dictionary for both Gazebo server and client processes
    gz_process_env = {
        'GZ_SIM_RESOURCE_PATH': new_gz_sim_resource_path,
        'GZ_CONFIG_PATH': current_gz_config_path,
        'LD_LIBRARY_PATH': current_ld_library_path,
        'PATH': current_path_env,
        'HOME': current_home_env,
        'DISPLAY': current_display_env,               # <--- ADD DISPLAY
        'WAYLAND_DISPLAY': current_wayland_display_env # <--- ADD WAYLAND_DISPLAY (harmless if not set)
    }
    # --- Gazebo Simulation ---
    # 1. Gazebo Sim Server
    gz_sim_server_process = ExecuteProcess(
        cmd=[gz_executable_explicit_path, 'sim', '-s', '-v', '4'], # Using default world from server
        # To use your custom empty.world (once standard model paths are resolved or world is self-contained):
        # cmd=[gz_executable_explicit_path, 'sim', '-s', '-v', '4', LaunchConfiguration('world')],
        output='screen',
        env=gz_process_env
    )

    # 2. Gazebo Sim Client (GUI)
    gz_sim_client_process = ExecuteProcess(
        cmd=[gz_executable_explicit_path, 'sim'],
        output='screen',
        env=gz_process_env # Ensure this is passed
    )
    # Delay client start until server is likely up
    delayed_gz_client = TimerAction(
        period=3.0, # Adjust delay as needed (e.g., 3-5 seconds)
        actions=[gz_sim_client_process]
    )

    # --- ROS 2 Nodes ---
    # 3. Robot State Publisher
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'robot_description': robot_description_content
        }]
    )

    # 4. Spawn Robot Entity
    spawn_entity_node = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-world', 'default',
            '-topic', 'robot_description',
            '-name', 'm1u_robot',
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.1',
            '-Y', '0.0'
        ],
        output='screen'
    )

    # Delay the spawner to give Gazebo server (and client) time to start
    delayed_spawn_entity = TimerAction(
        period=7.0, # Increased delay to ensure server AND client have had time to start/connect
        actions=[spawn_entity_node]
    )

    return LaunchDescription([
        use_sim_time_arg,
        world_file_arg, # Declared, though server currently uses its default world

        gz_sim_server_process,
        delayed_gz_client,
        robot_state_publisher_node,
        delayed_spawn_entity
    ])