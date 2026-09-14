# 🌾 Mandi Procurement System

A FastAPI-based web application backend designed to streamline agricultural mandi operations for farmers and administrators. The system manages farmer registration, OTP-based login, crop slot booking, and admin management.

---

## 🚀 Features

- **Farmer Registration & Management:** Register new farmers with details like Aadhaar, mobile number, and mandi selection.
- **OTP Authentication:** Send and verify OTPs using Fast2SMS API integration.
- **Crop Slot Booking:** Enable farmers to book slots for selling crops with estimated quantities (in quintals).
- **Token & Crop Details Retrieval:** Fetch farmer tokens and active crop bookings by farmer_id.
- **Admin Dashboard Backend:** Secure admin authentication to update and monitor crop selling statuses.

---

## 🛠️ Tech Stack

- **Backend:** FastAPI (Python)
- **Database:** MySQL
- **Validation:** Pydantic
- **SMS Gateway:** Fast2SMS API
- **Server:** Uvicorn

---

## 📡 API Endpoints Summary

### 🔐 Authentication & OTP
- `POST /send-otp/` - Request OTP on mobile number.
- `POST /verify-otp/` - Verify received OTP for login.

### 🧑‍🌾 Farmer Operations
- `POST /register-farmer/` - Onboard a new farmer into the system.
- `POST /book-crop-slot/` - Book a selling slot for crops with estimated yield.
- `GET /farmer-crop/{farmer_id}` - Retrieve booked crop details for a specific farmer.
- `GET /farmer/token/{farmer_id}` - Fetch generated token details for a specific farmer.

### 👨‍💼 Admin Operations
- `POST /Admin-Registration/` - Verify admin credentials.
- `POST /admin/update-status/` - Update crop slot booking status.

---

## 📦 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/codeby-om/Project-Befarm.git](https://github.com/codeby-om/Project-Befarm.git)
   cd Project-Befarm
   ```
2. **Navigate to backend directory:**
   ```bash
   cd frontened
   ```
3. **Activate Virtual Environment:**
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
4. **Install Dependenceies:**
   ```bash
   pip install fastapi uvicorn mysql-connector-python pydantic requests
   ```
5. **Run the Server:**
   ```bash
   uvicorn project:app --reload
   ```
   

  
