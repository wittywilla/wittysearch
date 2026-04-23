import os
import re
import datetime
import platform
import subprocess
import json
import math
from flask import Flask, request, render_template, send_file, abort

app = Flask(__name__)

SEARCH_DIR = 'files'

ALLOWED_IMAGE_EXTS = ['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp', 'bmp', 'tiff', 'ico']
ALLOWED_VIDEO_EXTS = ['mp4', 'mkv', 'mov', 'avi', 'wmv', 'flv', 'webm', 'm4v', '3gp']

def load_file_types():
    try:
        with open('filetypes.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load filetypes.json: {e}")
        return {}

FILE_TYPES_MAP = load_file_types()

def parse_query(query):
    filetype_match = re.search(r'filetype:(\w+)', query, re.IGNORECASE)
    filetype = filetype_match.group(1).lower() if filetype_match else None
    base_query = re.sub(r'filetype:\w+', '', query, flags=re.IGNORECASE).strip().lower()
    return base_query, filetype

def search_local_files(base_query, filetype):
    results = []
    if not os.path.exists(SEARCH_DIR):
        os.makedirs(SEARCH_DIR)

    for root, dirs, files in os.walk(SEARCH_DIR):
        for file in files:
            filepath = os.path.join(root, file)
            ext = file.split('.')[-1].lower() if '.' in file else 'unknown'
            
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
            
            if base_query and base_query in file.lower():
                match_found = True
            
            text_exts = ['txt', 'md', 'csv', 'html', 'htm', 'css', 'py', 'json', 'log', 'xml', 'js', 'ts', 'jsx', 'tsx', 'php', 'c', 'cpp', 'h', 'cs', 'java', 'sql', 'yaml', 'yml', 'ini', 'sh', 'bat']
            if ext in text_exts:
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                        # --- NEW: Favicon Extraction Logic for HTML ---
                        if is_html:
                            # Find all link tags
                            link_tags = re.findall(r'<link[^>]+>', content, re.IGNORECASE)
                            for tag in link_tags:
                                tag_lower = tag.lower()
                                if 'rel="icon"' in tag_lower or "rel='icon'" in tag_lower or 'rel="shortcut icon"' in tag_lower or "rel='shortcut icon'" in tag_lower:
                                    href_match = re.search(r'href=["\']([^"\']+)["\']', tag, re.IGNORECASE)
                                    if href_match:
                                        raw_href = href_match.group(1)
                                        # Check if it's a remote URL or local file
                                        if raw_href.startswith('http://') or raw_href.startswith('https://'):
                                            favicon_path = raw_href
                                            break
                                        else:
                                            # Resolve local relative path
                                            fav_full_path = os.path.normpath(os.path.join(root, raw_href))
                                            if os.path.exists(fav_full_path) and os.path.isfile(fav_full_path):
                                                favicon_path = os.path.relpath(fav_full_path, SEARCH_DIR).replace('\\', '/')
                                                break

                        # Snippet Search
                        if base_query and base_query in content.lower():
                            match_found = True
                            idx = content.lower().find(base_query)
                            start = max(0, idx - 80)
                            end = min(len(content), idx + 250)
                            raw_snippet = content[start:end]
                            clean_snippet = re.sub(r'\n{3,}', '\n\n', raw_snippet).strip()
                            snippet = "..." + clean_snippet + "..."
                        elif not snippet:
                            snippet = content[:250].strip() + "..." 
                except Exception:
                    pass 
            
            if not base_query and filetype:
                match_found = True

            if match_found:
                rel_path = os.path.relpath(filepath, SEARCH_DIR).replace('\\', '/')
                rel_dir = os.path.relpath(root, SEARCH_DIR).replace('\\', '/')
                
                results.append({
                    'title': file,
                    'directory': root,
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

@app.route('/')
def home():
    return render_template('index.html')

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
    
    if page < 1: page = 1
    if page > total_pages: page = total_pages
    
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated_results = all_results[start_idx:end_idx]
    
    return render_template(
        'results.html', 
        query=query, 
        results=paginated_results,
        total_results=total_results,
        page=page,
        limit=limit,
        total_pages=total_pages
    )

@app.route('/file/<path:filepath>')
def serve_file(filepath):
    base_dir = os.path.abspath(SEARCH_DIR)
    full_path = os.path.abspath(os.path.join(base_dir, filepath))
    
    if not full_path.startswith(base_dir):
        abort(403)
        
    ext = filepath.split('.')[-1].lower() if '.' in filepath else ''
    
    mime_types = {
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
    
    if ext in mime_types:
        return send_file(full_path, mimetype=mime_types[ext])
    else:
        return send_file(full_path, as_attachment=True)

@app.route('/open_dir')
def open_dir():
    dir_path = request.args.get('path', '')
    base_dir = os.path.abspath(SEARCH_DIR)
    full_path = os.path.abspath(os.path.join(base_dir, dir_path))
    
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)