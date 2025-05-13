cmake_minimum_required(VERSION 3.8)
project(m1u_description)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
# find_package(rclcpp REQUIRED) # Keep only if you add C++ code to this package that needs it
# find_package(xacro REQUIRED)  # Keep only if you use ament_xacro_process_once() below

# The following packages are primarily runtime dependencies for launch files or Python scripts.
# Their presence in package.xml is what matters most for rosdep and runtime discovery.
# find_package(rclpy REQUIRED)
# find_package(robot_state_publisher REQUIRED)
# find_package(joint_state_publisher_gui REQUIRED) # This was causing the error
# find_package(gazebo_ros REQUIRED)
# find_package(gazebo_plugins REQUIRED)
# find_package(rviz2 REQUIRED)
# find_package(tf2_ros REQUIRED)
# find_package(launch_ros REQUIRED)


# =================================================================================
# CRITICAL: Install rules for your URDF, meshes, launch files, and config files
# =================================================================================
install(
  DIRECTORY urdf meshes launch config
  DESTINATION share/${PROJECT_NAME}
)

# If you have .xacro files and want to process one into a .urdf at build time (less common now, usually done at runtime in launch):
# Example:
# include(ament_xacro) # You would need find_package(xacro REQUIRED) above for this
# ament_xacro_process_once(
#   INPUT_FILE urdf/your_robot.urdf.xacro # Your main xacro file
#   OUTPUT_FILE ${CMAKE_CURRENT_BINARY_DIR}/your_robot.urdf
# )
# install(
#   FILES ${CMAKE_CURRENT_BINARY_DIR}/your_robot.urdf
#   DESTINATION share/${PROJECT_NAME}/urdf
# )
# =================================================================================

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()