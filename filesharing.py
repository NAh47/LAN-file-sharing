from flask import Flask, render_template_string, send_from_directory, url_for, request, jsonify, redirect
from werkzeug.utils import safe_join
import os
import json

app = Flask(__name__)

# Configuration
SHARE_DIR = "C:/Users/nahom"
INDEX_FILE = "file_index.json"

def create_index(path):
    file_index = []
    total_files = sum([len(files) for _, _, files in os.walk(path)])
    processed_files = 0
    
    for root, dirs, files in os.walk(path):
        for name in dirs + files:
            relative_path = os.path.relpath(os.path.join(root, name), path)
            file_index.append(relative_path)
            processed_files += 1
            progress = (processed_files / total_files) * 100
            print(f"Indexing... {progress:.2f}% complete", end="\r")
    print("Indexing complete.")
    return file_index

def save_index(index, index_file):
    with open(index_file, 'w') as f:
        json.dump(index, f)

def load_index(index_file):
    with open(index_file, 'r') as f:
        return json.load(f)

if os.path.exists(INDEX_FILE):
    print("Index found. Loading index...")
    file_index = load_index(INDEX_FILE)
else:
    print("Index not found. Creating index...")
    file_index = create_index(SHARE_DIR)
    save_index(file_index, INDEX_FILE)

# Template for the main page with sidebar and content area
main_template = '''
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>File Share</title>
    <link href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" rel="stylesheet">
    <style>
      body {
        font-size: .875rem;
      }
      .sidebar {
        position: fixed;
        top: 0;
        bottom: 0;
        left: 0;
        z-index: 100;
        padding: 48px 0 0;
        overflow-y: auto;
      }
      .main {
        margin-left: 200px;
        padding: 20px;
      }
      .nav-link img {
        margin-right: 10px;
      }
      .nav-link.active {
        font-weight: bold;
        color: darkblue;
      }
      .nav-item ul {
        padding-left: 20px;
      }
      .search-results {
        position: absolute;
        background-color: white;
        border: 1px solid #ddd;
        max-height: 200px;
        overflow-y: auto;
        width: 100%;
      }
      .search-results li {
        padding: 5px 10px;
        cursor: pointer;
      }
      .search-results li:hover {
        background-color: #f1f1f1;
      }
    </style>
    <script>
      document.addEventListener('DOMContentLoaded', function() {
        var scrollPos = sessionStorage.getItem('scrollPos');
        if (scrollPos) {
          document.querySelector('.sidebar').scrollTop = scrollPos;
        }
        var links = document.querySelectorAll('.nav-link');
        links.forEach(function(link) {
          link.addEventListener('click', function() {
            sessionStorage.setItem('scrollPos', document.querySelector('.sidebar').scrollTop);
          });
        });

        // Live search functionality
        var searchInput = document.querySelector('input[name="q"]');
        var searchResults = document.createElement('ul');
        searchResults.classList.add('search-results');
        searchInput.parentNode.appendChild(searchResults);

        searchInput.addEventListener('input', function() {
          var query = searchInput.value;
          if (query.length > 0) {
            fetch('/live_search?q=' + query)
              .then(response => response.json())
              .then(data => {
                searchResults.innerHTML = '';
                data.forEach(item => {
                  var li = document.createElement('li');
                  li.textContent = item;
                  li.addEventListener('click', function() {
                    window.location.href = '/folder/' + item;
                  });
                  searchResults.appendChild(li);
                });
              });
          } else {
            searchResults.innerHTML = '';
          }
        });

        document.addEventListener('click', function(event) {
          if (!searchInput.contains(event.target) && !searchResults.contains(event.target)) {
            searchResults.innerHTML = '';
          }
        });
      });
    </script>
  </head>
  <body>
    <nav class="navbar navbar-expand-md navbar-dark bg-dark fixed-top">
      <a class="navbar-brand" href="#">File Share</a>
      <form class="form-inline my-2 my-lg-0 ml-auto" action="/search" method="get">
        <input class="form-control mr-sm-2" type="search" name="q" placeholder="Search" aria-label="Search">
        <button class="btn btn-outline-light my-2 my-sm-0" type="submit">Search</button>
      </form>
    </nav>
    <div class="container-fluid">
      <div class="row">
        <nav class="col-md-2 d-none d-md-block bg-light sidebar">
          <div class="sidebar-sticky">
            <ul class="nav flex-column">
              {% for folder in folders %}
              <li class="nav-item">
                <a class="nav-link {% if folder in opened_folders %}active{% endif %}" href="/folder/{{ folder }}">
                  <img src="{{ url_for('static', filename='folder.svg') }}" width="20" height="20" alt="Folder">
                  {{ folder }}
                </a>
                {% if folder in opened_folders %}
                <ul class="nav flex-column">
                  {% for subfolder in opened_folders[folder] %}
                  <li class="nav-item">
                    <a class="nav-link {% if current_folder == subfolder %}active{% endif %}" href="/folder/{{ folder }}/{{ subfolder }}">
                      <img src="{{ url_for('static', filename='folder.svg') }}" width="20" height="20" alt="Folder">
                      {{ subfolder }}
                    </a>
                  </li>
                  {% endfor %}
                </ul>
                {% endif %}
              </li>
              {% endfor %}
            </ul>
          </div>
        </nav>
        <main role="main" class="col-md-9 ml-sm-auto col-lg-10 px-4 main">
          <h2>Welcome to the File Share</h2>
          <p>Select a folder from the sidebar to view its contents.</p>
        </main>
      </div>
    </div>
  </body>
</html>
'''

# Template for displaying folder contents
folder_template = '''
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>{{ folder }}</title>
    <link href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" rel="stylesheet">
    <style>
      body {
        font-size: .875rem;
      }
      .sidebar {
        position: fixed;
        top: 0;
        bottom: 0;
        left: 0;
        z-index: 100;
        padding: 48px 0 0;
        overflow-y: auto;
      }
      .main {
        margin-left: 200px;
        padding: 20px;
      }
      .nav-link img, .list-group-item img {
        margin-right: 10px;
      }
      .nav-link.active {
        font-weight: bold;
        color: darkblue;
      }
      .nav-item ul {
        padding-left: 20px;
      }
    </style>
    <script>
      document.addEventListener('DOMContentLoaded', function() {
        var scrollPos = sessionStorage.getItem('scrollPos');
        if (scrollPos) {
          document.querySelector('.sidebar').scrollTop = scrollPos;
        }
        var links = document.querySelectorAll('.nav-link');
        links.forEach(function(link) {
          link.addEventListener('click', function() {
            sessionStorage.setItem('scrollPos', document.querySelector('.sidebar').scrollTop);
          });
        });
      });
    </script>
  </head>
  <body>
    <nav class="navbar navbar-expand-md navbar-dark bg-dark fixed-top">
      <a class="navbar-brand" href="/">File Share</a>
      <form class="form-inline my-2 my-lg-0 ml-auto" action="/search" method="get">
        <input class="form-control mr-sm-2" type="search" name="q" placeholder="Search" aria-label="Search">
        <button class="btn btn-outline-light my-2 my-sm-0" type="submit">Search</button>
      </form>
    </nav>
    <div class="container-fluid">
      <div class="row">
        <nav class="col-md-2 d-none d-md-block bg-light sidebar">
          <div class="sidebar-sticky">
            <ul class="nav flex-column">
              {% for folder in folders %}
              <li class="nav-item">
                <a class="nav-link {% if folder in opened_folders %}active{% endif %}" href="/folder/{{ folder }}">
                  <img src="{{ url_for('static', filename='folder.svg') }}" width="20" height="20" alt="Folder">
                  {{ folder }}
                </a>
                {% if folder in opened_folders %}
                <ul class="nav flex-column">
                  {% for subfolder in opened_folders[folder] %}
                  <li class="nav-item">
                    <a class="nav-link {% if current_folder == subfolder %}active{% endif %}" href="/folder/{{ folder }}/{{ subfolder }}">
                      <img src="{{ url_for('static', filename='folder.svg') }}" width="20" height="20" alt="Folder">
                      {{ subfolder }}
                    </a>
                  </li>
                  {% endfor %}
                </ul>
                {% endif %}
              </li>
              {% endfor %}
            </ul>
          </div>
        </nav>
        <main role="main" class="col-md-9 ml-sm-auto col-lg-10 px-4 main">
          <h2>Contents of {{ folder }}</h2>
          <ul class="list-group">
            {% for item in contents %}
            <li class="list-group-item">
              {% if '.' in item %}
              <img src="{{ url_for('static', filename='file.svg') }}" width="20" height="20" alt="File">
              <a href="/download/{{ folder }}/{{ item }}">{{ item }}</a>
              {% else %}
              <img src="{{ url_for('static', filename='folder.svg') }}" width="20" height="20" alt="Folder">
              <a href="/folder/{{ folder }}/{{ item }}">{{ item }}</a>
              {% endif %}
            </li>
            {% endfor %}
          </ul>
        </main>
      </div>
    </div>
  </body>
</html>
'''

# Template for displaying search results
search_template = '''
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>Search Results</title>
    <link href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" rel="stylesheet">
    <style>
      body {
        font-size: .875rem;
      }
      .sidebar {
        position: fixed;
        top: 0;
        bottom: 0;
        left: 0;
        z-index: 100;
        padding: 48px 0 0;
        overflow-y: auto;
      }
      .main {
        margin-left: 200px;
        padding: 20px;
      }
      .nav-link img {
        margin-right: 10px;
      }
      .nav-link.active {
        font-weight: bold;
        color: darkblue;
      }
      .nav-item ul {
        padding-left: 20px;
      }
    </style>
    <script>
      document.addEventListener('DOMContentLoaded', function() {
        var scrollPos = sessionStorage.getItem('scrollPos');
        if (scrollPos) {
          document.querySelector('.sidebar').scrollTop = scrollPos;
        }
        var links = document.querySelectorAll('.nav-link');
        links.forEach(function(link) {
          link.addEventListener('click', function() {
            sessionStorage.setItem('scrollPos', document.querySelector('.sidebar').scrollTop);
          });
        });
      });
    </script>
  </head>
  <body>
    <nav class="navbar navbar-expand-md navbar-dark bg-dark fixed-top">
      <a class="navbar-brand" href="/">File Share</a>
      <form class="form-inline my-2 my-lg-0 ml-auto" action="/search" method="get">
        <input class="form-control mr-sm-2" type="search" name="q" placeholder="Search" aria-label="Search">
        <button class="btn btn-outline-light my-2 my-sm-0" type="submit">Search</button>
      </form>
    </nav>
    <div class="container-fluid">
      <div class="row">
        <nav class="col-md-2 d-none d-md-block bg-light sidebar">
          <div class="sidebar-sticky">
            <ul class="nav flex-column">
              {% for folder in folders %}
              <li class="nav-item">
                <a class="nav-link {% if folder in opened_folders %}active{% endif %}" href="/folder/{{ folder }}">
                  <img src="{{ url_for('static', filename='folder.svg') }}" width="20" height="20" alt="Folder">
                  {{ folder }}
                </a>
                {% if folder in opened_folders %}
                <ul class="nav flex-column">
                  {% for subfolder in opened_folders[folder] %}
                  <li class="nav-item">
                    <a class="nav-link {% if current_folder == subfolder %}active{% endif %}" href="/folder/{{ folder }}/{{ subfolder }}">
                      <img src="{{ url_for('static', filename='folder.svg') }}" width="20" height="20" alt="Folder">
                      {{ subfolder }}
                    </a>
                  </li>
                  {% endfor %}
                </ul>
                {% endif %}
              </li>
              {% endfor %}
            </ul>
          </div>
        </nav>
        <main role="main" class="col-md-9 ml-sm-auto col-lg-10 px-4 main">
          <h2>Search Results</h2>
          <ul class="list-group">
            {% for item in results %}
            <li class="list-group-item">
              {% if '.' in item %}
              <img src="{{ url_for('static', filename='file.svg') }}" width="20" height="20" alt="File">
              <a href="/download/{{ item }}">{{ item }}</a>
              {% else %}
              <img src="{{ url_for('static', filename='folder.svg') }}" width="20" height="20" alt="Folder">
              <a href="/folder/{{ item }}">{{ item }}</a>
              {% endif %}
            </li>
            {% endfor %}
          </ul>
        </main>
      </div>
    </div>
  </body>
</html>
'''

def search_files(query):
    results = [item for item in file_index if query.lower() in item.lower()]
    return results

@app.route('/')
def index():
    folders = [f.name for f in os.scandir(SHARE_DIR) if f.is_dir()]
    return render_template_string(main_template, folders=folders, opened_folders={}, current_folder="")

@app.route('/folder/<path:folder_path>')
def folder_contents(folder_path):
    folder_abs_path = safe_join(SHARE_DIR, folder_path)
    if not os.path.exists(folder_abs_path):
        return "Folder not found", 404
    contents = os.listdir(folder_abs_path)
    contents.sort()

    # Prepare the opened folders structure for the sidebar
    opened_folders = {}
    parts = folder_path.split('/')
    for i in range(len(parts)):
        sub_path = '/'.join(parts[:i+1])
        sub_abs_path = safe_join(SHARE_DIR, sub_path)
        if os.path.exists(sub_abs_path):
            opened_folders[parts[i]] = [f.name for f in os.scandir(sub_abs_path) if f.is_dir()]

    folders = [f.name for f in os.scandir(SHARE_DIR) if f.is_dir()]
    return render_template_string(folder_template, folder=folder_path, contents=contents, folders=folders, opened_folders=opened_folders, current_folder=parts[-1])

@app.route('/download/<path:file_path>')
def download(file_path):
    return send_from_directory(SHARE_DIR, file_path, as_attachment=True)

@app.route('/search')
def search():
    query = request.args.get('q')
    if not query:
        return redirect(url_for('index'))
    results = search_files(query)
    folders = [f.name for f in os.scandir(SHARE_DIR) if f.is_dir()]
    return render_template_string(search_template, results=results, folders=folders, opened_folders={}, current_folder="")

@app.route('/live_search')
def live_search():
    query = request.args.get('q')
    if not query:
        return jsonify([])
    results = search_files(query)
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
