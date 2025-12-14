from flask import Flask, request, redirect
import sqlite3
import os

app = Flask(__name__)

DB = "botdata.db"
ADMIN_PASSWORD = "Mohammed@7756"

# ===============================
# AUTO-CREATE DATABASE AND TABLES
# ===============================
def init_db():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance REAL DEFAULT 0
        )
    """)
    # Topup requests table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS topup_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            amount REAL,
            status TEXT DEFAULT 'pending'
        )
    """)
    # Products table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price REAL
        )
    """)
    conn.commit()
    conn.close()

init_db()  # call once on start

# ===============================
# DATABASE HELPER
# ===============================
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

# ===============================
# LOGIN PAGE
# ===============================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            return redirect("/topups")
        return "<h3>❌ Wrong password</h3>"

    return """
    <h2>Admin Login</h2>
    <form method="post">
        <input type="password" name="password" placeholder="Password" required>
        <br><br>
        <button type="submit">Login</button>
    </form>
    """

# ===============================
# TOP-UP REQUESTS
# ===============================
@app.route("/topups")
def topups():
    db = get_db()
    rows = db.execute("SELECT * FROM topup_requests").fetchall()
    db.close()

    html = """
    <h2>Top-up Requests</h2>
    <table border="1" cellpadding="5">
    <tr>
        <th>ID</th>
        <th>Username</th>
        <th>Amount</th>
        <th>Status</th>
        <th>Action</th>
    </tr>
    """

    for r in rows:
        html += f"""
        <tr>
            <td>{r['id']}</td>
            <td>{r['username']}</td>
            <td>{r['amount']}</td>
            <td>{r['status']}</td>
            <td>
        """
        if r["status"] == "pending":
            html += f"""
                <a href="/approve/{r['id']}">Approve</a> |
                <a href="/reject/{r['id']}">Reject</a>
            """
        html += "</td></tr>"

    html += """
    </table>
    <br>
    <a href="/products">Manage Services</a>
    """
    return html

# ===============================
# APPROVE / REJECT
# ===============================
@app.route("/approve/<int:rid>")
def approve(rid):
    db = get_db()
    row = db.execute(
        "SELECT user_id, amount FROM topup_requests WHERE id=?",
        (rid,)
    ).fetchone()

    if row:
        db.execute(
            "UPDATE users SET balance = balance + ? WHERE user_id=?",
            (row["amount"], row["user_id"])
        )
        db.execute(
            "UPDATE topup_requests SET status='approved' WHERE id=?",
            (rid,)
        )
        db.commit()

    db.close()
    return redirect("/topups")


@app.route("/reject/<int:rid>")
def reject(rid):
    db = get_db()
    db.execute(
        "UPDATE topup_requests SET status='rejected' WHERE id=?",
        (rid,)
    )
    db.commit()
    db.close()
    return redirect("/topups")

# ===============================
# PRODUCTS / SERVICES
# ===============================
@app.route("/products", methods=["GET", "POST"])
def products():
    db = get_db()

    if request.method == "POST":
        name = request.form.get("name")
        price = request.form.get("price")
        db.execute(
            "INSERT INTO products (name, price) VALUES (?, ?)",
            (name, price)
        )
        db.commit()

    rows = db.execute("SELECT * FROM products").fetchall()
    db.close()

    html = """
    <h2>Services</h2>
    <table border="1" cellpadding="5">
    <tr>
        <th>ID</th>
        <th>Name</th>
        <th>Price</th>
        <th>Action</th>
    </tr>
    """

    for r in rows:
        html += f"""
        <tr>
            <td>{r['id']}</td>
            <td>{r['name']}</td>
            <td>{r['price']}</td>
            <td><a href="/delete/{r['id']}">Delete</a></td>
        </tr>
        """

    html += """
    </table>
    <br>
    <h3>Add Service</h3>
    <form method="post">
        <input name="name" placeholder="Service name" required>
        <br><br>
        <input name="price" type="number" step="0.01" placeholder="Price" required>
        <br><br>
        <button type="submit">Add</button>
    </form>
    <br>
    <a href="/topups">Back to Top-ups</a>
    """
    return html

@app.route("/delete/<int:pid>")
def delete(pid):
    db = get_db()
    db.execute("DELETE FROM products WHERE id=?", (pid,))
    db.commit()
    db.close()
    return redirect("/products")

# ===============================
# RUN SERVER
# ===============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
