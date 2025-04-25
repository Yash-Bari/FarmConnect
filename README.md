# FarmDirectConnect

FarmDirectConnect is a modern, farm-to-customer web platform built with Flask. It connects farmers directly with customers, allowing for crop management, online ordering, and seamless farm-to-table experiences.

## Features
- **User Authentication** (Farmers & Customers)
- **Marketplace**: Browse, search, and filter crops
- **Farmer Dashboard**: Crop management, order fulfillment
- **Customer Dashboard**: Shopping cart, order management
- **Order & Payment Management**
- **Notifications**
- **Responsive UI**: Fresh black, white, and green farm-friendly theme

## Tech Stack
- **Backend**: Flask, SQLAlchemy, Flask-Login, Flask-WTF
- **Database**: MySQL (utf8mb4, port 3307)
- **Frontend**: Bootstrap 5, custom CSS

## Setup Instructions

### 1. Clone the Repository
```bash
git clone <repo-url>
cd FarmDirectConnect
```

### 2. Install Dependencies
Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create a `.env` file in the root directory and set the following:
```
SECRET_KEY=your_secret_key
DATABASE_URL=mysql+pymysql://root:yash#oo7@localhost:3307/farmconnect?charset=utf8mb4
```

### 4. Database Setup
Ensure MySQL is running on port 3307. Create the database if it doesn't exist:
```sql
CREATE DATABASE farmconnect CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```
Apply migrations (if using Flask-Migrate):
```bash
flask db upgrade
```

### 5. Run the Application
```bash
flask run
```
Visit [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

## Directory Structure
```
FarmDirectConnect/
├── main.py
├── extensions.py
├── routes.py
├── models.py
├── requirements.txt
├── templates/
│   ├── base.html
│   ├── auth/
│   ├── customer/
│   └── farmer/
├── static/
│   └── css/
│       └── style.css
└── ...
```

## Customization
- Update theme colors in `static/css/style.css` for your branding.
- Add more features or integrations as needed.

## Credits
- Built with Flask, Bootstrap, and love for fresh produce!

## License
MIT License
