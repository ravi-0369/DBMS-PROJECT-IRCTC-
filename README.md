# 🚆 IRCTC Railway Reservation System

A web-based **Railway Reservation System** developed as a DBMS project.  
The project simulates important functionalities of an online railway ticket booking system, including user registration, login, train search, seat availability, ticket booking, cancellation, and OTP-based password reset.

---

## 📌 About the Project

The **IRCTC Railway Reservation System** is designed to provide a simple interface for users to search for trains and manage railway reservations.

The project combines:

- 🗄️ Database Management System
- 🌐 Web Development
- 🐍 Python Backend
- 🔐 User Authentication
- 🎫 Railway Ticket Reservation

This project was developed as an academic **DBMS project** to demonstrate database design, SQL queries, relationships, and integration of a database with a web application.

---

## ✨ Features

### 👤 User Management

- User registration
- User login
- Secure password handling
- Logout functionality
- Password reset using OTP
- User session management

### 🚆 Train Search

- Search trains between source and destination
- Select travel date
- View available trains
- Check seat availability
- Per-date seat availability

### 🎫 Ticket Reservation

- Select train
- Enter passenger details
- Select available seats
- Book tickets
- Generate booking information
- View reservation details

### ❌ Ticket Cancellation

- Cancel existing bookings
- Update seat availability after cancellation

### 🔐 OTP Password Reset

- Request password reset
- Generate OTP
- Verify OTP
- Reset password securely

---

## 🛠️ Technologies Used

| Technology | Purpose |
|------------|---------|
| Python | Backend development |
| Flask | Web application framework |
| HTML | Frontend structure |
| CSS | Styling |
| SQL | Database management |
| SQLite/MySQL | Database |
| Git & GitHub | Version control |

---

## 📂 Project Structure

```text
DBMS-PROJECT-IRCTC/
│
├── app.py
├── schema.sql
├── requirements.txt
├── .gitignore
│
├── templates/
│   ├── ...
│   └── ...
│
└── README.md
