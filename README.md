# HSBC Approval System (IPAS)

An automated internal approval system built with Python and Flask.

## Prerequisites

Before running the project on a new system, ensure you have the following installed:
- [Python 3.8+](https://www.python.org/downloads/) (Make sure "Add Python to PATH" is checked during installation)
- [Git](https://git-scm.com/)

## Installation & Setup

Follow these steps to run the application locally:

### 1. Clone the repository

```bash
git clone https://github.com/PralambikaSoni/HSBC-Approval-System.git
cd HSBC-Approval-System
```

### 2. Set up a Virtual Environment

It is highly recommended to use a virtual environment to isolate the project's dependencies from your global Python packages.

**On Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

With the virtual environment activated, install the necessary Python packages:
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

The project requires certain environment variables to function correctly (e.g., database URI, secret keys). 

Copy the example environment template into a new `.env` file:
- **On Windows:**
  ```powershell
  copy .env.example .env
  ```
- **On macOS/Linux:**
  ```bash
  cp .env.example .env
  ```

*Optional: Open the newly created `.env` file in a text editor and update any specific values if needed.*

### 5. Run the Application

Finally, start the Python server using the provided start script:
```bash
python run.py
```

Once running, you can access the application by navigating to this URL in your web browser:
**http://127.0.0.1:5000**

---

## Troubleshooting

- **`ModuleNotFoundError`**: Ensure you have activated your virtual environment before running `python run.py`. You should see `(venv)` in your terminal prompt.
- **`python` command not found**: Ensure Python is added to your system's PATH variables or try using `python3` instead.
