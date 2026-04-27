# WittySearch 🔍

WittySearch is a specialized file search engine designed to demonstrate efficient file system traversal logic and present results through a clean, accessible, and responsive user interface. This project serves as a comprehensive portfolio piece showcasing both frontend design and backend functionality.

## 🔗 Quick Links
* **Live Site Demo:** [wittywilla.xyz/projects/wittysearch/](https://wittywilla.xyz/projects/wittysearch/)
* **Official Documentation:** [wittywilla.xyz/projects/wittysearchdocumentation/](https://wittywilla.xyz/projects/wittysearchdocumentation/)

---

## 🚀 Site Demo (Proof of Concept)
The live site demo available at the link above is designed to serve as a **basic proof of concept** for those interested in exploring the project's frontend UI, layout, and design philosophy. 

**Please note:** The demo *does not* utilize the Python backend. It is a static representation meant to showcase the responsive design, accessibility features, and visual components (like the theme toggles and image previews) without the active Flask routing and file traversal logic running behind the scenes. 

---

## ✨ Key Features
* **Robust Backend Architecture:** Powered by a Python Flask backend designed to handle deep file system traversal and search queries efficiently.
* **Dynamic UI Rendering:** Utilizes Jinja2 templates for seamless server-side data integration into the frontend.
* **Flexible Configuration:** Search parameters and data structures are managed easily using JSON.
* **Responsive, Mobile-First Design:** Crafted with semantic HTML5 and modern CSS to ensure a smooth, readable experience on any device.
* **Accessibility Focused:** Built with proper ARIA attributes and a "skip to main content" link for improved screen reader navigation and keyboard usability.
* **Theater-Mode Image Previews:** Includes dynamic, theater-style popups for visual search results.
* **Dark/Light Theme Toggle:** Built-in theme switching capability for user comfort.
* **Branded Integration:** Custom WittyWilla favicon integration and persistent GitHub navigation links.

---

## 🛠️ Technology Stack
* **Frontend:** HTML5 (Semantic), CSS3 (Mobile-First), JavaScript (Theme toggling & theater-mode previews)
* **Backend:** Python, Flask, Jinja2
* **Data Management:** JSON 
* **File Parsing:** PyPDF2

---

## 📦 Installation & Setup

To run the WittySearch backend locally, you will need Python installed on your system along with the project dependencies. 

Choose your operating system below and copy-paste the commands into your terminal to automatically install Python and the required libraries (`Flask` and `PyPDF2`).

### 🪟 Windows
*Open PowerShell or Command Prompt:*
```powershell
# 1. Install Python (if not already installed) using the Windows Package Manager
winget install -e --id Python.Python.3.12

# 2. Install the required project dependencies
pip install Flask PyPDF2
```

### 🍎 macOS
*Open Terminal (Requires [Homebrew](https://brew.sh/)):*
```bash
# 1. Install Python via Homebrew
brew install python

# 2. Install the required project dependencies
pip3 install Flask PyPDF2
```

### 🐧 Linux
*Open your terminal and use the commands matching your distribution:*

**Ubuntu / Debian / Linux Mint (APT)**
```bash
# 1. Update package lists and install Python/pip
sudo apt update && sudo apt install python3 python3-pip -y

# 2. Install the required project dependencies
pip3 install Flask PyPDF2
```

**Fedora / RHEL (DNF)**
```bash
# 1. Install Python and pip
sudo dnf install python3 python3-pip -y

# 2. Install the required project dependencies
pip3 install Flask PyPDF2
```

**Arch Linux (Pacman)**
```bash
# 1. Install Python and pip
sudo pacman -Syu python python-pip --noconfirm

# 2. Install the required project dependencies
pip install Flask PyPDF2
```

---

## ▶️ Running the Application
Once your dependencies are installed, navigate to the project folder in your terminal and launch the backend:

```bash
python app.py
```
*(Note: Depending on your OS environment, you may need to run `python3 app.py` instead).*

Once the server starts, open your web browser and navigate to `http://127.0.0.1:5000` to use WittySearch!

Currently I'm still working on a way to just have this as a deployable docker container, but for now, it's just a standalone project while I work out how to accopmlish my goal. 

---

## 📚 Documentation
For an in-depth look at the project architecture, please refer to the [WittySearch Documentation Portal](https://wittywilla.xyz/projects/wittysearchdocumentation/). 

The documentation pages cover:
* Backend Python Flask architecture and routing logic.
* Jinja2 UI template rendering.
* CSS design frameworks and accessibility choices.
* Data configuration and JSON integration.

---

*A project by WittyWilla.*
