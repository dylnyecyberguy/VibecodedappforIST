from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB_NAME = "fish.db"


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS catches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            species TEXT NOT NULL,
            weight REAL,
            length REAL,
            location TEXT,
            bait TEXT,
            date TEXT,
            notes TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            unlocked INTEGER DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            target INTEGER,
            progress INTEGER DEFAULT 0,
            completed INTEGER DEFAULT 0
        )
    """)

    conn.commit()

    achievements = [
        ("First Catch", "Log your first fish", 0),
        ("10 Fish Caught", "Log 10 total catches", 0),
        ("Species Collector", "Catch 3 different species", 0),
        ("Big Catch", "Catch a fish over 5 lb", 0)
    ]

    for a in achievements:
        cur.execute("""
            INSERT OR IGNORE INTO achievements (name, description, unlocked)
            VALUES (?, ?, ?)
        """, a)

    conn.commit()
    conn.close()


def update_achievements():
    conn = get_db_connection()
    cur = conn.cursor()

    total_catches = cur.execute("SELECT COUNT(*) FROM catches").fetchone()[0]
    species_count = cur.execute("SELECT COUNT(DISTINCT species) FROM catches").fetchone()[0]
    big_catch = cur.execute("SELECT COUNT(*) FROM catches WHERE weight >= 5").fetchone()[0]

    if total_catches >= 1:
        cur.execute("UPDATE achievements SET unlocked = 1 WHERE name = 'First Catch'")
    if total_catches >= 10:
        cur.execute("UPDATE achievements SET unlocked = 1 WHERE name = '10 Fish Caught'")
    if species_count >= 3:
        cur.execute("UPDATE achievements SET unlocked = 1 WHERE name = 'Species Collector'")
    if big_catch >= 1:
        cur.execute("UPDATE achievements SET unlocked = 1 WHERE name = 'Big Catch'")

    conn.commit()
    conn.close()


def update_goals():
    conn = get_db_connection()
    cur = conn.cursor()

    goals = cur.execute("SELECT * FROM goals").fetchall()
    total_catches = cur.execute("SELECT COUNT(*) FROM catches").fetchone()[0]

    for goal in goals:
        progress = min(total_catches, goal["target"])
        completed = 1 if progress >= goal["target"] else 0

        cur.execute("""
            UPDATE goals
            SET progress = ?, completed = ?
            WHERE id = ?
        """, (progress, completed, goal["id"]))

    conn.commit()
    conn.close()


@app.route("/")
def index():
    conn = get_db_connection()
    catches = conn.execute("SELECT * FROM catches ORDER BY date DESC LIMIT 5").fetchall()
    achievements = conn.execute("SELECT * FROM achievements WHERE unlocked = 1").fetchall()
    goals = conn.execute("SELECT * FROM goals").fetchall()

    total_catches = conn.execute("SELECT COUNT(*) FROM catches").fetchone()[0]
    biggest = conn.execute("SELECT MAX(weight) FROM catches").fetchone()[0]
    conn.close()

    return render_template(
        "index.html",
        catches=catches,
        achievements=achievements,
        goals=goals,
        total_catches=total_catches,
        biggest=biggest
    )


@app.route("/add", methods=["GET", "POST"])
def add_catch():
    if request.method == "POST":
        species = request.form["species"]
        weight = request.form["weight"]
        length = request.form["length"]
        location = request.form["location"]
        bait = request.form["bait"]
        date = request.form["date"]
        notes = request.form["notes"]

        conn = get_db_connection()
        conn.execute("""
            INSERT INTO catches (species, weight, length, location, bait, date, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (species, weight, length, location, bait, date, notes))
        conn.commit()
        conn.close()

        update_achievements()
        update_goals()

        return redirect(url_for("index"))

    return render_template("add_catch.html")


@app.route("/catches")
def catches():
    conn = get_db_connection()
    all_catches = conn.execute("SELECT * FROM catches ORDER BY date DESC").fetchall()
    conn.close()
    return render_template("catches.html", catches=all_catches)


@app.route("/goals", methods=["GET", "POST"])
def goals():
    conn = get_db_connection()

    if request.method == "POST":
        title = request.form["title"]
        target = int(request.form["target"])

        conn.execute("""
            INSERT INTO goals (title, target, progress, completed)
            VALUES (?, ?, 0, 0)
        """, (title, target))
        conn.commit()

        update_goals()
        conn.close()
        return redirect(url_for("goals"))

    all_goals = conn.execute("SELECT * FROM goals").fetchall()
    conn.close()
    return render_template("goals.html", goals=all_goals)


@app.route("/achievements")
def achievements():
    conn = get_db_connection()
    all_achievements = conn.execute("SELECT * FROM achievements").fetchall()
    conn.close()
    return render_template("achievements.html", achievements=all_achievements)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)