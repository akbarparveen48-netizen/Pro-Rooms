# Pro-Rooms 🚀

Pro-Rooms is a premium platform for students and professionals to discover, create, and join exclusive WhatsApp group rooms. Each room is protected by a 6-digit access code to ensure community quality.

## Features ✨

- **Room Discovery**: Search through a curated list of professional and student groups.
- **Secure Access**: Join rooms only if you have the 6-digit access code.
- **Create Your Own**: Easily create and manage your own WhatsApp group rooms.
- **Premium Design**: Sleek, modern, and dark-themed UI built with Glassmorphism.
- **User Authentication**: Secure login via local accounts or Google OAuth.

## Tech Stack 🛠️

- **Backend**: Flask (Python)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Frontend**: HTML5, Vanilla JS, CSS3 (Glassmorphism)
- **Authentication**: Local Auth & Authlib (Google OAuth)

## Setup & Installation 🚀

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/Vasanth2005kk/Pro-Rooms.git
    cd Pro-Rooms
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment Variables**:
    Create a `.env` file with the following:
    ```env
    DB_HOST=your_host
    DB_PORT=5432
    DB_USER=your_user
    DB_PASSWORD=your_password
    DB_NAME=rooms_db
    SECRET_KEY=your_secret
    GOOGLE_CLIENT_ID=your_id
    GOOGLE_CLIENT_SECRET=your_secret
    ```

4.  **Run the application**:
    ```bash
    python app.py
    ```

## Usage 💡

1.  Register or log in to your account.
2.  Browse available rooms or use the search bar to find specific groups.
3.  Click **Join Room** and enter the 6-digit password to get the WhatsApp group link.
4.  Use **Create New Room** to share your own WhatsApp group link with others.

---
Built with ❤️ by [Vasanth](https://github.com/Vasanth2005kk)