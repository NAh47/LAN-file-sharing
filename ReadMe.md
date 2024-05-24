# File Sharing Application

## Description

This is a Flask-based file sharing application that allows you to share files and folders over a local network. The application features a sidebar for navigation, live search functionality, and file download capabilities.

## Features

- Browse folders and files in a Windows Explorer-like interface.
- Live search with instant results displayed as you type.
- Download files directly from the web interface.
- Indexing of the shared directory for optimized search performance.

## Installation

1. Clone the repository or download the script.

2. Ensure you have Python installed on your machine. This application is tested with Python 3.6+.

3. Install the required packages:
    ```sh
    pip install flask
    ```

4. Place your images (`file.svg`, `open-file-folder.svg`, `folder.svg`) in a `static` directory inside your project folder.

5. Set the `SHARE_DIR` variable in the script to the path of the directory you want to share.

## Running the Application

1. Open a terminal or command prompt.

2. Navigate to the directory containing the script.

3. Run the script using Python:
    ```sh
    python script_name.py
    ```

4. On any device connected to the same Wi-Fi network, open a web browser and go to `http://localhost:8000/` to access the file-sharing UI.

## Usage

- **Sidebar Navigation**: Browse through the folders using the sidebar.
- **Live Search**: Use the search bar to find files and folders. Results will appear as you type.
- **File Download**: Click on a file to download it directly to your device.

## License

This project is licensed under the MIT License.
