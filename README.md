# 🛒 Lades - E-commerce Backend System

A backend system for an e-commerce platform built with Django, designed to manage users, products, orders, cart, and chat functionalities.

> **Personal Project**  
> Backend-focused | Django + PostgreSQL

---

## 📌 Description

Lades is a backend system that simulates a real-world e-commerce platform, focusing on core business logic and scalable architecture.

The system is built using Django and follows a modular design approach, where each feature is separated into independent apps for better maintainability and extensibility.

It handles user authentication, product management, shopping cart operations, order processing, and messaging between users.

---

## 🚀 Core Functionalities

### 👤 Authentication & Account
- User registration & login
- Authentication system
- User profile management

### 🛍 Product Management
- Create / update / delete products
- Upload product images
- Manage product inventory

### 🛒 Cart System
- Add products to cart
- Remove products from cart
- Update quantity
- Calculate total amount

### 📦 Order System
- Create orders from cart
- Apply discount codes
- Handle payment status
- Ensure transaction safety using database locking

### 💬 Chat System
- User-to-user messaging
- Store conversation history
- Real-time ready architecture

### 📎 Attachment System
- Upload and manage files/images

---

## 🏗️ Project Structure
src/
├── account/ # Authentication & user management
├── attachment/ # File upload handling
├── cart/ # Shopping cart logic
├── chat/ # Messaging system
├── lades/ # Django core configuration
├── order/ # Order & payment logic
├── product/ # Product & inventory management
├── router/ # API routing
├── utils/ # Shared utilities
├── manage.py

---

## ⚙️ Technologies Used

### Backend
- Python
- Django
- Django Ninja
- PostgreSQL

### Tools
- Git, GitHub
- Postman (API testing)

---

## 🧠 System Design Highlights

- Modular architecture using Django apps
- Separation of concerns across features
- Transaction-safe order processing (`select_for_update`)
- Database-level validation using constraints
- Clean API structure for scalability

---

## 🗄️ Database Design

The system is built around relational database principles with PostgreSQL.

### Main Entities:
- **User**
- **Product**
- **Cart / CartItem**
- **Order / OrderItem**
- **Message (Chat)**

### Key Features:
- Foreign Key relationships between entities
- Data integrity enforced with constraints (CHECK, UNIQUE, NOT NULL)
- Optimized queries for performance

---

## 🔥 Highlights

- Real-world e-commerce logic
- Clean and maintainable codebase
- Optimized database operations
- API logging middleware for debugging
- Scalable architecture ready for expansion

---

## 📌 Future Improvements

- [ ] Payment gateway integration
- [ ] Redis caching for performance
- [ ] Docker deployment
- [ ] API documentation (Swagger / OpenAPI)
- [ ] Real-time chat with WebSocket

---

## 👨‍💻 Author

- LemonHV