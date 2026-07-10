# ToyCad Hackathon Portal

A lightweight, robust web application built for managing hackathons. This portal provides a streamlined experience for participants, judges, and administrators with role-based access control and dedicated dashboards.

## 🚀 Features

- **Participant Dashboard**: Register, form/join teams, submit project links (GitHub), and view published grades & feedback.
- **Judge Dashboard**: Review submitted projects, evaluate teams with a 1-10 score slider and detailed feedback, and publish grades once evaluations are complete.
- **Admin Dashboard**: Manage the overall hackathon flow and monitor team progress.
- **Real-time Navigation**: Smooth, single-page application feel powered by vanilla JavaScript and dynamic DOM updates.
- **Modern UI**: Styled beautifully with Tailwind CSS (via CDN) utilizing a cohesive, dark-mode focused design system and Material Symbols.

## 🛠️ Technology Stack

- **Backend**: [FastAPI](https://fastapi.tiangolo.com/) (Python)
- **Database**: SQLite (`hackathon.db`)
- **Frontend**: Vanilla HTML5, CSS3, JavaScript
- **Styling**: Tailwind CSS (CDN)

## 📦 Running Locally

Follow these steps to run the portal on your local machine:

### 1. Prerequisites
Ensure you have Python 3.8+ installed on your system.

### 2. Install Dependencies
Install the required Python packages (FastAPI and Uvicorn):
```bash
pip install -r requirements.txt
```
*(If `requirements.txt` is missing, you can simply run `pip install fastapi uvicorn pydantic`)*

### 3. Initialize the Database
The project uses SQLite. The schema and initial data setup are handled in `database.py`. If you need to reset or initialize the database, you can simply run the Python script:
```bash
python database.py
```

### 4. Start the Server
Start the FastAPI development server using Uvicorn:
```bash
python -m uvicorn main:app --reload
```
The application will now be running locally. 

### 5. Access the Portal
Open your web browser and navigate to:
- **Login**: [http://localhost:8000/static/login.html](http://localhost:8000/static/login.html)
- **Register**: [http://localhost:8000/static/register.html](http://localhost:8000/static/register.html)

*(Note: Depending on how the static files are mounted in `main.py`, you can access the frontend via the `/static/` route).*

## 👥 Default Roles

When testing the application, you can register new users with the default role of **participant**. To test the **judge** or **admin** dashboards, you may need to manually update the `role` column for a specific user directly in the `hackathon.db` SQLite database using a tool like [DB Browser for SQLite](https://sqlitebrowser.org/) or an IDE extension.

---
*Happy Hacking!*
