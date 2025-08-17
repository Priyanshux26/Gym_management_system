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
