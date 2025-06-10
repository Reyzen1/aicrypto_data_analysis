# aicrypto_data_analysis

This repository is dedicated to exploring AI/Machine Learning applications in cryptocurrency data analysis. The project focuses on collecting, processing, and analyzing historical crypto price data using Python and relevant libraries, featuring an interactive dashboard built with Streamlit.

---

## 🚀 Getting Started

To set up and run this project on your local machine, please follow these steps. Our goal is to create an isolated and stable Python environment for executing the code, preventing common setup issues.

### 1. **Prerequisites**

* **Python (Python 3.12.x):** This project specifically requires **Python version 3.12** for correct functionality.
    * **Recommendation:** To easily manage different Python versions on your system, we highly recommend using tools like **`pyenv`** (for Linux/macOS) or **`Miniconda`/`Anaconda`** (for Windows and other systems). These tools help you install Python 3.12 effortlessly and manage virtual environments effectively.
    * If you don't have Python 3.12 installed, you can download it from the [official Python website](https://www.python.org/downloads/release/python-31210/). **Make sure to check the "Add Python to PATH" option during installation.**

### 2. **Create and Activate Virtual Environment**

It's always best practice to use a virtual environment for managing your project's dependencies to avoid conflicts with other projects.

1.  **Navigate to the Project Directory:**
    Open your terminal (Command Prompt/PowerShell) and change your directory to the main project folder `aicrypto_data_analysis`:
    ```bash
    cd E:\MyProjects\aicrypto_data_analysis\
    ```
    *(Replace the path with your actual project directory.)*

2.  **Create the Virtual Environment with Python 3.12:**
    Using the `py` launcher (which is typically installed with Python on Windows), create a new virtual environment named `venv`:
    ```bash
    py -3.12 -m venv venv
    ```

3.  **Activate the Virtual Environment:**
    ```bash
    .\venv\Scripts\activate
    ```
    After running this command, you should see `(venv)` at the beginning of your terminal's command line, indicating the virtual environment is active.

    * **Note for PowerShell Users:** If you encounter an error like `cannot be loaded because running scripts is disabled on this system`:
        1.  Open PowerShell **as an Administrator** (right-click the PowerShell icon and select "Run as administrator").
        2.  Enter the following command and press `Enter`:
            ```powershell
            Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
            ```
        3.  When prompted for confirmation, type `Y` and press `Enter`.
        4.  Close the Administrator PowerShell window, open a regular **PowerShell window**, and try activating the virtual environment again.

### 3. **Install Dependencies**

Once your virtual environment is active, you can install all the necessary libraries for the project. This project includes a `requirements.txt` file that specifies the exact versions of the tested libraries.

1.  **Install packages from `requirements.txt`:**
    ```bash
    pip install -r requirements.txt
    ```
    * **If the `requirements.txt` file is not present in your project** (or if you want to ensure `setuptools` is installed), please run these commands in your active virtual environment:
        ```bash
        pip install setuptools
        pip install streamlit pandas matplotlib requests pandas_ta numpy==1.26.4
        ```

### 4. **Run the Dashboard**

Now that all dependencies are installed, you can launch the Streamlit dashboard:

1.  **Run Streamlit:**
    Make sure you're still in the active virtual environment and within the main project directory. Then, execute the following command:
    ```bash
    streamlit run app.py
    ```

2.  **Open in Browser:**
    Streamlit will automatically open the dashboard in your default web browser.

3.  **Clear Streamlit Cache (If Needed):**
    If the dashboard doesn't display correctly or if you encounter any issues (even without explicit errors), click the menu (☰) in the top-right corner of the Streamlit dashboard and select **"Clear cache and rerun"**. This can help resolve caching-related problems.

---

## 🛠️ Troubleshooting Common Issues

Should you encounter any problems during setup or execution, refer to these common solutions:

* **`Access is denied` (Permission Error):**
    This error typically occurs because files are locked by another program (e.g., an open terminal or IDE) or due to permission issues.
    * **Solution:** Close all terminals and Python-related applications. Ensure no `python.exe` or `streamlit.exe` processes are active in Task Manager. Then, try opening your terminal **as an Administrator** (especially for installation steps) and repeat the process.
* **`ModuleNotFoundError: No module named 'pkg_resources'`:**
    This error indicates that `setuptools` (of which `pkg_resources` is a part) might not be installed correctly.
    * **Solution:** In your active virtual environment, run `pip install setuptools`. Then, retry `pip install -r requirements.txt` or your package installation command.
* **`ImportError: cannot import name 'NaN' from 'numpy'`:**
    This usually signals a compatibility issue with your `numpy` version, often related to your Python version or other libraries.
    * **Solution:** Ensure you've created your virtual environment with **Python 3.12** and correctly executed the package installation command including `numpy==1.26.4`.

---