# Gym Management System (Flask + MySQL)

A lightweight web application for managing a gym’s core operations: members, trainers, classes, payments and attendance.  
Authentication is restricted to **admin** and **receptionist** accounts.

---

## ⚙️ Features
- Member CRUD (add, view, update*¹, delete*¹)  
- Trainer CRUD  
- Class scheduling linked to trainers  
- Attendance tracking per class  
- Payment recording per member  
- Role-based access: `admin`, `receptionist`  
- Environment-based configuration (no secrets in code)

> *¹ update/delete routes not implemented yet; can be added easily.*

---

## 🚀 Quick Start

### 1. Clone & install
```bash
git clone https://github.com/<you>/gym-management.git
cd gym-management
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
2. Database setup
Create a MySQL (or MariaDB) database locally or on a free provider (FreeDB, PlanetScale, etc.).
Import the schema:
bash
Copy
mysql -h <host> -u <user> -p <db_name> < schema.sql
3. Environment file
Copy and edit:
bash
Copy
cp .env.example .env
Table
Copy
Variable	Example (FreeDB)
DB_HOST	freedb.tech
DB_USER	freedb_user
DB_PASS	your_password
DB_NAME	freedb_gym
DB_PORT	3306
4. Seed default staff accounts
Run once:
sql
Copy
INSERT INTO Users (username, password_hash, role) VALUES
('admin', '$2b$12$...', 'admin'),
('reception1', '$2b$12$...', 'receptionist');
Password hashes are bcrypt of admin123 and reception123.
5. Launch
bash
Copy
python main.py
# Visit http://127.0.0.1:5000
🔐 Default Credentials
Table
Copy
Username	Password	Role
admin	admin123	admin
reception1	reception123	receptionist
🐳 Docker (optional)
bash
Copy
docker build -t gym-app .
docker run -p 5000:5000 --env-file .env gym-app
🚀 Deploy to Render (free)
Push to GitHub
Render → New Web Service → connect repo
Build: pip install -r requirements.txt
Start: gunicorn main:app
Paste env-vars from .env into Render → Environment
📁 Tech Stack
Backend: Flask 2.x, Flask-Login, bcrypt
Database: MySQL / MariaDB
Hosting: Render, FreeDB, PlanetScale, Docker
📄 License
MIT – open for contributions and forks.
