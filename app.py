import os
import re
import datetime
import platform
import subprocess
import json
import math

import PyPDF2
from flask import Flask, request, render_template, send_file, abort

app = Flask(__name__)

# --- GLOBAL CONSTANTS ---

ALLOWED_IMAGE_EXTS = ['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp', 'bmp', 'tiff', 'ico']
ALLOWED_VIDEO_EXTS = ['mp4', 'mkv', 'mov', 'avi', 'wmv', 'flv', 'webm', 'm4v', '3gp']

MIME_TYPES = {
    'html': 'text/html', 'htm': 'text/html', 'css': 'text/css',
    'js': 'application/javascript', 'json': 'application/json',
    'txt': 'text/plain', 'md': 'text/markdown', 'pdf': 'application/pdf',
    'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png',
    'gif': 'image/gif', 'svg': 'image/svg+xml', 'webp': 'image/webp',
    'bmp': 'image/bmp', 'ico': 'image/x-icon',
    'mp4': 'video/mp4', 'mkv': 'video/x-matroska', 'mov': 'video/quicktime',
    'avi': 'video/x-msvideo', 'wmv': 'video/x-ms-wmv', 'flv': 'video/x-flv',
    'webm': 'video/webm', 'm4v': 'video/x-m4v', '3gp': 'video/3gpp',
}


def load_file_types():
    """Loads the file types mapping from a local JSON file."""
    try:
        with open('filetypes.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load filetypes.json: {e}")
        return {}


FILE_TYPES_MAP = load_file_types()


def get_app_settings():
    """Loads application settings from settings.json."""
    try:
        with open('settings.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def is_feature_enabled(setting_path, default=True):
    """Checks if a specific feature is enabled in settings.json using dot notation."""
    settings = get_app_settings()
    keys = setting_path.split('.')
    val = settings
    for key in keys:
        if isinstance(val, dict) and key in val:
            val = val[key]
        else:
            return default
    return val if isinstance(val, bool) else default


def parse_query(query):
    """Extracts explicit filetype parameters from the search query."""
    filetype_match = re.search(r'filetype:(\w+)', query, re.IGNORECASE)
    filetype = filetype_match.group(1).lower() if filetype_match else None
    base_query = re.sub(r'filetype:\w+', '', query, flags=re.IGNORECASE).strip().lower()
    return base_query, filetype


def search_local_files(base_query, filetype):
    """Scans defined directories to match query terms against file names and contents."""
    results = []
    
    # Read target directories from settings, fallback to a local 'files' folder
    search_dirs = is_feature_enabled('files.directories', ['files'])
    if not isinstance(search_dirs, list):
        search_dirs = ['files']

    for dir_idx, search_dir in enumerate(search_dirs):
        base_search_dir = os.path.abspath(search_dir)
        
        # Maintain original behavior of creating a default local 'files' folder if it is missing
        if search_dir == 'files' and not os.path.exists(base_search_dir):
            try:
                os.makedirs(base_search_dir)
            except Exception:
                pass

        if not os.path.exists(base_search_dir) or not os.path.isdir(base_search_dir):
            continue

        for root, dirs, files in os.walk(base_search_dir):
            for file in files:
                filepath = os.path.join(root, file)
                ext = file.split('.')[-1].lower() if '.' in file else 'unknown'
                
                # Filter by filetype if requested
                if filetype:
                    alias_groups = [
                        ['html', 'htm'], 
                        ['jpg', 'jpeg'], 
                        ['doc', 'docx'], 
                        ['xls', 'xlsx']
                    ]
                    valid_exts = [filetype]
                    for group in alias_groups:
                        if filetype in group:
                            valid_exts = group
                            break
                    
                    if ext not in valid_exts:
                        continue
                
                # Gather file metadata
                stat = os.stat(filepath)
                size_kb = stat.st_size / 1024
                date_mod = datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d')
                
                file_meta = FILE_TYPES_MAP.get(ext, ['Unknown Type', 'Unknown'])
                full_name = file_meta[0]
                category = file_meta[1]

                is_image = ext in ALLOWED_IMAGE_EXTS
                is_video = ext in ALLOWED_VIDEO_EXTS
                is_html = ext in ['html', 'htm']
                
                match_found = False
                snippet = ""
                favicon_path = None
                
                # Basic filename matching
                if base_query and base_query in file.lower():
                    match_found = True
                
                text_exts = ['txt', 'md', 'csv', 'html', 'htm', 'css', 'py', 'json', 'log', 'xml', 'js', 'ts', 'jsx', 'tsx', 'php', 'c', 'cpp', 'h', 'cs', 'java', 'sql', 'yaml', 'yml', 'ini', 'sh', 'bat']
                
                # --- PDF Parsing Logic ---
                if ext == 'pdf':
                    try:
                        with open(filepath, 'rb') as f:
                            reader = PyPDF2.PdfReader(f)
                            content = ""
                            # Limit reading to the first 5 pages to maintain search speed
                            for i in range(min(5, len(reader.pages))):
                                page = reader.pages[i]
                                extracted = page.extract_text()
                                if extracted:
                                    content += extracted + "\n"

                            if base_query and base_query in content.lower():
                                match_found = True
                                idx = content.lower().find(base_query)
                                start = max(0, idx - 80)
                                end = min(len(content), idx + 250)
                                raw_snippet = content[start:end]
                                clean_snippet = re.sub(r'\n{3,}', '\n\n', raw_snippet).strip()
                                snippet = f"...{clean_snippet}..."
                            elif not snippet:
                                snippet = f"{content[:250].strip()}..." 
                    except Exception:
                        pass # Silently skip encrypted or unreadable PDFs

                # --- Plain Text Parsing Logic ---
                elif ext in text_exts:
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                            # Favicon Extraction Logic for HTML
                            if is_html:
                                link_tags = re.findall(r'<link[^>]+>', content, re.IGNORECASE)
                                for tag in link_tags:
                                    tag_lower = tag.lower()
                                    if 'rel="icon"' in tag_lower or "rel='icon'" in tag_lower or 'rel="shortcut icon"' in tag_lower or "rel='shortcut icon'" in tag_lower:
                                        href_match = re.search(r'href=["\']([^"\']+)["\']', tag, re.IGNORECASE)
                                        if href_match:
                                            raw_href = href_match.group(1)
                                            if raw_href.startswith('http://') or raw_href.startswith('https://'):
                                                favicon_path = raw_href
                                                break
                                            else:
                                                fav_full_path = os.path.normpath(os.path.join(root, raw_href))
                                                if os.path.exists(fav_full_path) and os.path.isfile(fav_full_path):
                                                    # Link favicon path to its target directory index
                                                    fav_rel = os.path.relpath(fav_full_path, base_search_dir).replace('\\', '/')
                                                    favicon_path = f"{dir_idx}/{fav_rel}"
                                                    break

                            # Snippet Search
                            if base_query and base_query in content.lower():
                                match_found = True
                                idx = content.lower().find(base_query)
                                start = max(0, idx - 80)
                                end = min(len(content), idx + 250)
                                raw_snippet = content[start:end]
                                clean_snippet = re.sub(r'\n{3,}', '\n\n', raw_snippet).strip()
                                snippet = f"...{clean_snippet}..."
                            elif not snippet:
                                snippet = f"{content[:250].strip()}..." 
                    except Exception:
                        pass 
                
                # Catch-all for filetype queries without a base text query
                if not base_query and filetype:
                    match_found = True

                if match_found:
                    rel_to_base = os.path.relpath(filepath, base_search_dir).replace('\\', '/')
                    dir_to_base = os.path.relpath(root, base_search_dir).replace('\\', '/')
                    
                    # Prefix routing map using dir_idx
                    rel_path = f"{dir_idx}/{rel_to_base}"
                    rel_dir = f"{dir_idx}/{dir_to_base}" if dir_to_base != "." else str(dir_idx)
                    
                    results.append({
                        'title': file,
                        'directory': root,  # Returns the absolute path for clear UI display
                        'rel_path': rel_path,
                        'rel_dir': rel_dir,
                        'type': ext,
                        'full_name': full_name,
                        'category': category,
                        'size': f"{size_kb:.1f} KB",
                        'date': date_mod,
                        'is_image': is_image,
                        'is_video': is_video,
                        'is_html': is_html,
                        'favicon_path': favicon_path,
                        'snippet': snippet,
                    })
                    
    return results


# --- FLASK ROUTES ---

@app.route('/')
def home():
    show_server = is_feature_enabled("interface.buttons.optional.wittywillaprojectserver", True)
    show_github = is_feature_enabled("interface.buttons.optional.wittysearchgithub", True)
    return render_template('index.html', show_server=show_server, show_github=show_github)


@app.route('/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return render_template('index.html')
        
    try:
        limit = int(request.args.get('limit', 10))
        page = int(request.args.get('page', 1))
    except ValueError:
        limit = 10
        page = 1

    if limit not in [10, 25, 50, 100]:
        limit = 10
        
    base_query, filetype = parse_query(query)
    all_results = search_local_files(base_query, filetype)
    
    total_results = len(all_results)
    total_pages = math.ceil(total_results / limit) if total_results > 0 else 1
    
    # Ensure page stays within bounds
    page = max(1, min(page, total_pages))
    
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated_results = all_results[start_idx:end_idx]
    
    show_server = is_feature_enabled("interface.buttons.optional.wittywillaprojectserver", True)
    show_github = is_feature_enabled("interface.buttons.optional.wittysearchgithub", True)
    
    return render_template(
        'results.html', 
        query=query, 
        results=paginated_results,
        total_results=total_results,
        page=page,
        limit=limit,
        total_pages=total_pages,
        show_server=show_server,
        show_github=show_github
    )


@app.route('/file/<path:filepath>')
def serve_file(filepath):
    # Split the routed index from the target relative path
    parts = filepath.split('/', 1)
    if len(parts) < 2:
        abort(404)
        
    try:
        dir_idx = int(parts[0])
        rel_path = parts[1]
    except ValueError:
        abort(400)
        
    search_dirs = is_feature_enabled('files.directories', ['files'])
    if not isinstance(search_dirs, list) or dir_idx < 0 or dir_idx >= len(search_dirs):
        abort(404)
        
    base_dir = os.path.abspath(search_dirs[dir_idx])
    full_path = os.path.abspath(os.path.join(base_dir, rel_path))
    
    # Path Traversal Protection
    if not full_path.startswith(base_dir):
        abort(403)
        
    ext = filepath.split('.')[-1].lower() if '.' in filepath else ''
    
    if ext in MIME_TYPES:
        return send_file(full_path, mimetype=MIME_TYPES[ext])
    else:
        return send_file(full_path, as_attachment=True)


@app.route('/open_dir')
def open_dir():
    dir_path = request.args.get('path', '')
    parts = dir_path.split('/', 1)
    
    if len(parts) == 0 or not parts[0]:
        return "Invalid directory", 400
        
    try:
        dir_idx = int(parts[0])
    except ValueError:
        return "Invalid directory", 400
        
    rel_dir = parts[1] if len(parts) > 1 else ""
    
    search_dirs = is_feature_enabled('files.directories', ['files'])
    if not isinstance(search_dirs, list) or dir_idx < 0 or dir_idx >= len(search_dirs):
        return "Invalid directory", 404

    base_dir = os.path.abspath(search_dirs[dir_idx])
    full_path = os.path.abspath(os.path.join(base_dir, rel_dir))
    
    # Path Traversal Protection
    if not full_path.startswith(base_dir) or not os.path.isdir(full_path):
        return "Invalid directory", 403

    try:
        if platform.system() == "Windows":
            os.startfile(full_path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", full_path])
        else:
            subprocess.Popen(["xdg-open", full_path])
        return "", 204
    except Exception as e:
        return str(e), 500


# --- STARTUP AND LICENSE LOGIC ---

def print_legal_header():
    """Prints the non-blocking legal notice for logs/terminal."""
    print("\n" + "="*70)
    print("  WittySearch - app.py  Copyright (C) 2026")
    print("  Wilhelmina \"Willow\" Poortenga (WittyWilla)")
    print("-" * 70)
    print("  This program is free software under the GPLv3 License.")
    print("  It comes with ABSOLUTELY NO WARRANTY.")
    print("="*70 + "\n")


def check_license():
    """Enforces GPLv3 license acceptance on startup."""
    # 1. THE MANDATORY FILE CHECK (Must exist even if previously accepted)
    if not os.path.exists('LICENSE.txt'):
        print("\n" + "!"*70)
        print("FATAL ERROR: Unable to launch program due to missing LICENSE.txt.")
        print("-" * 70)
        print("This is a GPLv3 licensed project, and it is required to have this")
        print("license in the root directory in order to run. Removing or altering")
        print("the LICENSE.txt file before or after launching the file will break")
        print("GPLv3 if redistributing. Even in a non-redistributing environment,")
        print("this program will always check for the file's existence.")
        print("!"*70 + "\n")
        os._exit(1) # Immediate hard exit

    # 2. Skip interaction if this is the Flask reloader process
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        return

    # 3. Check for previous acceptance
    terms_file = "LICENSE_TERMS.txt"
    if os.path.exists(terms_file):
        with open(terms_file, 'r') as f:
            if f.read().strip().lower() == "true":
                print_legal_header()
                print("License already accepted. Initializing WittySearch...")
                return

    # 4. Interactive prompt
    print_legal_header()
    print("NOTICE: Agreeing to these terms will create a 'LICENSE_TERMS.txt' file.")
    print("This automates future launches by skipping this prompt.")
    print("The legal header above will remain in your terminal logs.")
    print("-" * 70)

    while True:
        choice = input("Accept license? [y]es / [n]o / [c]view full license: ").lower().strip()
        
        if choice == 'y':
            with open(terms_file, 'w') as f:
                f.write("true")
            print("\nLicense accepted. Launching...\n")
            break
        elif choice == 'n':
            with open(terms_file, 'w') as f:
                f.write("false")
            print("\nLicense declined. Application exiting.")
            os._exit(1)
        elif choice == 'c':
            print("\n" + "~"*70)
            with open('LICENSE.txt', 'r', encoding='utf-8') as f:
                print(f.read())
            print("~"*70 + "\n")
        else:
            print("Invalid input. Please enter 'y', 'n', or 'c'.")


if __name__ == '__main__':
    # Verify or prompt for license acceptance
    check_license()
    
    # Start the Flask app
    app.run(debug=True, port=5000)
