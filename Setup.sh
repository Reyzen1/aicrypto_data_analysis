#!/bin/bash

# --- Environment Setup for aicrypto_data_analysis ---

# This script automates the setup of the aicrypto_data_analysis project environment.
# It creates and configures a virtual environment, and installs all necessary dependencies.

# Usage: ./setup_project.sh [PYTHON_VERSION]
#   PYTHON_VERSION: Optional. Specify the Python version (e.g., 3.12, 3.13).
#                   If not provided, the script will use the default 'python' command on your system.

# Prerequisites:
# 1. Microsoft Visual C++ Build Tools installed (REQUIRED for Windows users to compile packages like numpy).
# 2. The specified Python version (e.g., Python 3.12.x or 3.13.x) must be installed
#    on your system and accessible via commands like 'python3.12' or 'python'.
# 3. Ensure this script is placed in the project's root directory.

echo "Starting project setup..."

# --- IMPORTANT: Navigate to the script's directory first ---
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd -P)
echo "Navigating to project directory: ${SCRIPT_DIR}"
cd "${SCRIPT_DIR}"
if [ $? -ne 0 ]; then
    echo "Error: Failed to change to script directory."
    exit 1
fi

# --- 0. Determine Python Command to Use ---
PYTHON_VERSION_ARG="${1}" # Get the argument passed to the script

if [ -z "${PYTHON_VERSION_ARG}" ]; then
    # No version specified, use default 'python' command
    PYTHON_CMD="python"
    echo "No specific Python version requested. Using default 'python' command on your system."
    echo "Checking default Python version..."
    if command -v "${PYTHON_CMD}" &> /dev/null; then
        DEFAULT_PYTHON_VERSION=$("${PYTHON_CMD}" --version 2>&1)
        echo "Default system Python version: ${DEFAULT_PYTHON_VERSION}"
        if [[ "${DEFAULT_PYTHON_VERSION}" != *Python\ 3.13* ]]; then
            echo "Warning: Your default Python is not 3.13. It's recommended to use Python 3.12 or 3.13 for this project."
            echo "You can specify a version like: ./setup_project.sh 3.12"
        fi
    else
        echo "Error: Default 'python' command not found. Please ensure Python is installed and in your PATH."
        exit 1
    fi
else
    # Version specified, construct command (e.g., python3.12, python3.13)
    PYTHON_CMD="python${PYTHON_VERSION_ARG}"
    echo "Attempting to use Python version: ${PYTHON_VERSION_ARG} (command: ${PYTHON_CMD})"
    if ! command -v "${PYTHON_CMD}" &> /dev/null; then
        echo "Error: Python command '${PYTHON_CMD}' not found."
        echo "Please ensure Python ${PYTHON_VERSION_ARG} is installed and its executable is in your system's PATH."
        exit 1
    fi
fi

# 1. Clean and Recreate Virtual Environment
echo "1. Cleaning up existing virtual environment (if any) and creating a new one..."
rm -rf venv # Removes the venv folder if it exists
"${PYTHON_CMD}" -m venv venv # Creates a new virtual environment using the determined python command
if [ $? -ne 0 ]; then
    echo "Error: Failed to create virtual environment with '${PYTHON_CMD}'. Check permissions or Python installation."
    exit 1
fi
echo "Virtual environment created successfully using ${PYTHON_CMD}."

# 2. Activate Virtual Environment
echo "2. Activating virtual environment..."
# Check if the Windows-style activate script exists, otherwise use the Linux-style
if [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
elif [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "Error: Virtual environment activate script not found in either venv/Scripts or venv/bin."
    exit 1
fi

if [ $? -ne 0 ]; then
    echo "Error: Failed to activate virtual environment. Please check your setup."
    exit 1
fi
echo "Virtual environment activated. Current Python version in venv:"
python --version # Display the active Python version within the venv

# 3. Install Core Python Tools and Project Dependencies
echo "3. Upgrading pip and installing core tools (setuptools, wheel) and project dependencies..."

# Upgrade pip first using the Python executable within the venv
python.exe -m pip install --upgrade pip # This specific command was key for your Windows setup
if [ $? -ne 0 ]; then
    echo "Warning: Failed to upgrade pip. Continuing with current pip version."
fi

# Install all dependencies including setuptools and wheel
pip install setuptools wheel streamlit pandas matplotlib requests pandas_ta numpy==1.26.4
if [ $? -ne 0 ]; then
    echo "Error: Failed to install project dependencies. Please check the error messages above."
    echo "Remember to install Microsoft Visual C++ Build Tools if on Windows and compiling issues persist."
    exit 1
fi
echo "All dependencies installed successfully."

echo "Setup complete. The virtual environment is ready."
