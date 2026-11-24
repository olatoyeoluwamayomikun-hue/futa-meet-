import os
import sqlite3
import uuid

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify
)

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename


app = Flask(__name__)

app.secret_key = "change-this-development-secret"


# -----------------------------
# DATABASE AND UPLOAD SETTINGS
# -----------------------------

DATABASE = "futa_meet.db"

UPLOAD_FOLDER = os.path.join(
    "static",
    "uploads"
)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "gif",
    "webp"
}

ALLOWED_VIDEO_EXTENSIONS = {
    "mp4",
    "mov",
    "webm"
}

BUSINESS_CATEGORIES = {
    "accommodation": "Accommodation & Housing",
    "food": "Food & Restaurants",
    "campus_market": "Campus Market",
    "fashion": "Fashion & Clothing",
    "beauty": "Beauty & Cosmetics",
    "hair": "Barbing & Hair Styling",
    "laundry": "Laundry & Dry Cleaning",
    "printing": "Printing & Photocopying",
    "graphics": "Graphic Design",
    "photography": "Photography & Videography",
    "phones": "Phones & Gadgets",
    "repairs": "Repairs & Maintenance",
    "electronics": "Electronics",
    "books": "Books & Stationery",
    "academic": "Tutoring & Academic Services",
    "transport": "Transportation",
    "dispatch": "Dispatch & Delivery",
    "events": "Events & Planning",
    "catering": "Catering",
    "entertainment": "Entertainment",
    "fitness": "Fitness & Sports",
    "gaming": "Gaming",
    "freelance": "Freelancing",
    "software": "Web & Software Services",
    "marketing": "Digital Marketing",
    "tailoring": "Tailoring",
    "jewellery": "Jewellery & Watches",
    "perfumes": "Perfumes & Fragrances",
    "health": "Health & Wellness",
    "pharmacy": "Pharmacy & Medical Services",
    "groceries": "Groceries",
    "drinks": "Drinks & Beverages",
    "pastries": "Pastries & Snacks",
    "agriculture": "Agriculture & Farm Products",
    "cleaning": "Cleaning Services",
    "gifts": "Gifts & Souvenirs",
    "student_services": "Student Services",
    "other": "Other"
}

DEFAULT_COMMISSION_RATE = 10.0

ADMIN_EMAIL = os.environ.get(
    "FUTA_MEET_ADMIN_EMAIL",
    "admin@futameet.com"
)

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


# -----------------------------
# DATABASE CONNECTION
# -----------------------------

def get_db():

    connection = sqlite3.connect(DATABASE)

    connection.row_factory = sqlite3.Row

    return connection


# -----------------------------
# INITIALIZE DATABASE
# -----------------------------

def init_db():

    connection = get_db()

    # USERS TABLE
    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            full_name TEXT NOT NULL,

            email TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL,

            department TEXT NOT NULL,

            level TEXT NOT NULL,

            bio TEXT DEFAULT '',

            profile_picture TEXT DEFAULT '',

            profile_visible INTEGER DEFAULT 1,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
    """)


    # POSTS TABLE
    connection.execute("""
        CREATE TABLE IF NOT EXISTS posts (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            content TEXT NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id)
            REFERENCES users(id)

        )
    """)


    # ADD MEDIA COLUMNS TO EXISTING POSTS TABLE

    try:

        connection.execute("""
            ALTER TABLE posts
            ADD COLUMN media_filename TEXT DEFAULT ''
        """)

    except sqlite3.OperationalError:

        pass


    try:

        connection.execute("""
            ALTER TABLE posts
            ADD COLUMN media_type TEXT DEFAULT ''
        """)

    except sqlite3.OperationalError:

        pass


    # LIKES TABLE
    connection.execute("""
        CREATE TABLE IF NOT EXISTS likes (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            post_id INTEGER NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(user_id, post_id),

            FOREIGN KEY (user_id)
            REFERENCES users(id),

            FOREIGN KEY (post_id)
            REFERENCES posts(id)

        )
    """)


    # COMMENTS TABLE
    connection.execute("""
        CREATE TABLE IF NOT EXISTS comments (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            post_id INTEGER NOT NULL,

            content TEXT NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id)
            REFERENCES users(id),

            FOREIGN KEY (post_id)
            REFERENCES posts(id)

        )
    """)


    # SHARES TABLE
    connection.execute("""
        CREATE TABLE IF NOT EXISTS shares (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            post_id INTEGER NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(user_id, post_id),

            FOREIGN KEY (user_id)
            REFERENCES users(id),

            FOREIGN KEY (post_id)
            REFERENCES posts(id)

        )
    """)


    # PINS TABLE
    connection.execute("""
        CREATE TABLE IF NOT EXISTS pins (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            post_id INTEGER NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(user_id, post_id),

            FOREIGN KEY (user_id)
            REFERENCES users(id),

            FOREIGN KEY (post_id)
            REFERENCES posts(id)

        )
    """)
    # FOLLOWS TABLE
    connection.execute("""
        CREATE TABLE IF NOT EXISTS follows (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            follower_id INTEGER NOT NULL,

            following_id INTEGER NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(follower_id, following_id),

            FOREIGN KEY (follower_id)
            REFERENCES users(id),

            FOREIGN KEY (following_id)
            REFERENCES users(id)

        )
    """)
        # NOTIFICATIONS TABLE
    connection.execute("""
        CREATE TABLE IF NOT EXISTS notifications (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            recipient_id INTEGER NOT NULL,

            sender_id INTEGER NOT NULL,

            type TEXT NOT NULL,

            message TEXT NOT NULL,

            post_id INTEGER,

            is_read INTEGER DEFAULT 0,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (recipient_id)
            REFERENCES users(id),

            FOREIGN KEY (sender_id)
            REFERENCES users(id),

            FOREIGN KEY (post_id)
            REFERENCES posts(id)

        )
    """)

    # MESSAGES TABLE
    connection.execute("""
        CREATE TABLE IF NOT EXISTS messages (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            sender_id INTEGER NOT NULL,

            receiver_id INTEGER NOT NULL,

            content TEXT NOT NULL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (sender_id)
            REFERENCES users(id),

            FOREIGN KEY (receiver_id)
            REFERENCES users(id)

        )
    """)


    # BUSINESSES TABLE
    connection.execute("""
        CREATE TABLE IF NOT EXISTS businesses (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            owner_id INTEGER NOT NULL,

            business_name TEXT NOT NULL,

            category TEXT NOT NULL,

            description TEXT DEFAULT '',

            phone TEXT DEFAULT '',

            location TEXT DEFAULT '',

            logo_filename TEXT DEFAULT '',

            verification_status TEXT DEFAULT 'pending',

            rejection_reason TEXT DEFAULT '',

            commission_rate REAL DEFAULT 10.0,

            is_active INTEGER DEFAULT 0,

            verified_at TIMESTAMP,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (owner_id)
            REFERENCES users(id)

        )
    """)

    # Add newer business columns to an existing businesses table.
    for column_sql in [
        "ALTER TABLE businesses ADD COLUMN commission_rate REAL DEFAULT 10.0",
        "ALTER TABLE businesses ADD COLUMN is_active INTEGER DEFAULT 0",
        "ALTER TABLE businesses ADD COLUMN verified_at TIMESTAMP"
    ]:
        try:
            connection.execute(column_sql)
        except sqlite3.OperationalError:
            pass

    connection.commit()

    connection.close()


# -----------------------------
# HELPER FUNCTIONS
# -----------------------------

def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


def allowed_video(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_VIDEO_EXTENSIONS
    )


def get_current_user():

    user_id = session.get("user_id")

    if not user_id:

        return None


    connection = get_db()

    user = connection.execute(
        """
        SELECT *
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    ).fetchone()

    connection.close()

    return user


def post_exists(post_id):

    connection = get_db()

    post = connection.execute(
        """
        SELECT id
        FROM posts
        WHERE id = ?
        """,
        (post_id,)
    ).fetchone()

    connection.close()

    return post is not None


# -----------------------------
# HOMEPAGE
# -----------------------------

@app.route("/")
def home():

    user = get_current_user()

    return render_template(
        "index.html",
        user=user
    )


# -----------------------------
# REGISTER
# -----------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        full_name = request.form.get(
            "full_name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        department = request.form.get(
            "department",
            ""
        ).strip()

        level = request.form.get(
            "level",
            ""
        ).strip()


        if not all([
            full_name,
            email,
            password,
            department,
            level
        ]):

            flash(
                "Please fill in all required fields.",
                "error"
            )

            return redirect(
                url_for("register")
            )


        if len(password) < 8:

            flash(
                "Password must contain at least 8 characters.",
                "error"
            )

            return redirect(
                url_for("register")
            )


        connection = get_db()


        existing_user = connection.execute(
            """
            SELECT id
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()


        if existing_user:

            connection.close()

            flash(
                "An account with this email already exists.",
                "error"
            )

            return redirect(
                url_for("register")
            )


        hashed_password = generate_password_hash(
            password
        )


        connection.execute(
            """
            INSERT INTO users (
                full_name,
                email,
                password,
                department,
                level
            )

            VALUES (?, ?, ?, ?, ?)
            """,
            (
                full_name,
                email,
                hashed_password,
                department,
                level
            )
        )


        connection.commit()

        connection.close()


        flash(
            "Account created successfully. You can now log in.",
            "success"
        )

        return redirect(
            url_for("login")
        )


    return render_template(
        "register.html"
    )


# -----------------------------
# LOGIN
# -----------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )


        connection = get_db()


        user = connection.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()


        connection.close()


        if user and check_password_hash(
            user["password"],
            password
        ):

            session["user_id"] = user["id"]

            return redirect(
                url_for("dashboard")
            )


        flash(
            "Incorrect email or password.",
            "error"
        )


    return render_template(
        "login.html"
    )
# -----------------------------
# PROFILE
# -----------------------------

@app.route("/profile", methods=["GET", "POST"])
def profile():

    user = get_current_user()

    if not user:

        return redirect(
            url_for("login")
        )

    if request.method == "POST":

        department = request.form.get(
            "department",
            ""
        ).strip()

        level = request.form.get(
            "level",
            ""
        ).strip()

        bio = request.form.get(
            "bio",
            ""
        ).strip()

        profile_visible = (
            1
            if request.form.get("profile_visible")
            else 0
        )

        profile_picture = user["profile_picture"]

        uploaded_file = request.files.get(
            "profile_picture"
        )

        if uploaded_file and uploaded_file.filename:

            if not allowed_file(
                uploaded_file.filename
            ):

                flash(
                    "Unsupported image format.",
                    "error"
                )

                return redirect(
                    url_for("profile")
                )

            filename = secure_filename(
                uploaded_file.filename
            )

            unique_filename = (
                f"user_{user['id']}_{uuid.uuid4().hex}_{filename}"
            )

            file_path = os.path.join(
                app.config["UPLOAD_FOLDER"],
                unique_filename
            )

            uploaded_file.save(
                file_path
            )

            profile_picture = unique_filename

        connection = get_db()

        connection.execute(
            """
            UPDATE users

            SET department = ?,
                level = ?,
                bio = ?,
                profile_picture = ?,
                profile_visible = ?

            WHERE id = ?
            """,
            (
                department,
                level,
                bio,
                profile_picture,
                profile_visible,
                user["id"]
            )
        )

        connection.commit()

        connection.close()

        flash(
            "Your profile has been updated.",
            "success"
        )

        return redirect(
            url_for("profile")
        )

    user = get_current_user()

    connection = get_db()

    posts = connection.execute(
        """
        SELECT

            posts.id,

            posts.content,

            posts.created_at,

            posts.media_filename,

            posts.media_type,

            users.id AS user_id,

            users.full_name,

            users.profile_picture,

            (
                SELECT COUNT(*)

                FROM likes

                WHERE likes.post_id = posts.id

            ) AS like_count,

            EXISTS (

                SELECT 1

                FROM likes

                WHERE likes.post_id = posts.id

                AND likes.user_id = ?

            ) AS user_liked,

            (
                SELECT COUNT(*)

                FROM comments

                WHERE comments.post_id = posts.id

            ) AS comment_count,

            (
                SELECT COUNT(*)

                FROM shares

                WHERE shares.post_id = posts.id

            ) AS share_count,

            EXISTS (

                SELECT 1

                FROM pins

                WHERE pins.post_id = posts.id

                AND pins.user_id = ?

            ) AS user_pinned

        FROM posts

        JOIN users
        ON posts.user_id = users.id

        WHERE posts.user_id = ?

        ORDER BY posts.id DESC

        """,
        (
            user["id"],
            user["id"],
            user["id"]
        )
    ).fetchall()

    connection.close()

    return render_template(
        "profile.html",
        user=user,
        posts=posts
    )


# -----------------------------
# PUBLIC USER PROFILE
# -----------------------------

@app.route("/user/<int:user_id>")
def public_profile(user_id):

    connection = get_db()

    user = connection.execute(
        """
        SELECT *
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    ).fetchone()

    if not user:
        connection.close()
        flash("User not found.", "error")
        return redirect(url_for("discover"))

    # Count followers
    follower_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM follows
        WHERE following_id = ?
        """,
        (user_id,)
    ).fetchone()[0]

    # Count people this user follows
    following_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM follows
        WHERE follower_id = ?
        """,
        (user_id,)
    ).fetchone()[0]

    # Check whether current logged-in user follows this person
    current_user = get_current_user()

    is_following = False

    if current_user:
        existing_follow = connection.execute(
            """
            SELECT id
            FROM follows
            WHERE follower_id = ?
            AND following_id = ?
            """,
            (
                current_user["id"],
                user_id
            )
        ).fetchone()

        if existing_follow:
            is_following = True

    connection.close()

    return render_template(
        "user_profile.html",
        user=user,
        follower_count=follower_count,
        following_count=following_count,
        is_following=is_following,
        current_user=current_user
    )

# -----------------------------
# DASHBOARD
# -----------------------------

@app.route("/dashboard")
def dashboard():

    user = get_current_user()

    if not user:

        return redirect(
            url_for("login")
        )

    connection = get_db()

    posts = connection.execute(
        """
        SELECT

            posts.id,

            posts.content,

            posts.created_at,

            posts.media_filename,

            posts.media_type,

            users.id AS user_id,

            users.full_name,

            users.profile_picture,

            (
                SELECT COUNT(*)

                FROM likes

                WHERE likes.post_id = posts.id

            ) AS like_count,

            EXISTS (

                SELECT 1

                FROM likes

                WHERE likes.post_id = posts.id

                AND likes.user_id = ?

            ) AS user_liked,

            (
                SELECT COUNT(*)

                FROM comments

                WHERE comments.post_id = posts.id

            ) AS comment_count,

            (
                SELECT COUNT(*)

                FROM shares

                WHERE shares.post_id = posts.id

            ) AS share_count,

            EXISTS (

                SELECT 1

                FROM pins

                WHERE pins.post_id = posts.id

                AND pins.user_id = ?

            ) AS user_pinned

        FROM posts

        JOIN users
        ON posts.user_id = users.id

        ORDER BY posts.id DESC

        """,
        (
            user["id"],
            user["id"]
        )
    ).fetchall()

    connection.close()

    return render_template(
        "dashboard.html",
        user=user,
        posts=posts
    )


# -----------------------------
# DISCOVER STUDENTS
# -----------------------------

@app.route("/discover")
def discover():

    user = get_current_user()

    if not user:

        return redirect(
            url_for("login")
        )

    search = request.args.get(
        "search",
        ""
    ).strip()

    department = request.args.get(
        "department",
        ""
    ).strip()

    level = request.args.get(
        "level",
        ""
    ).strip()

    connection = get_db()

    query = """
        SELECT

            id,

            full_name,

            department,

            level,

            bio,

            profile_picture

        FROM users

        WHERE profile_visible = 1

        AND id != ?

    """

    parameters = [
        user["id"]
    ]

    if search:

        query += """
            AND (

                full_name LIKE ?

                OR department LIKE ?

                OR bio LIKE ?

            )

        """

        search_value = f"%{search}%"

        parameters.extend([
            search_value,
            search_value,
            search_value
        ])

    if department:

        query += """
            AND department = ?

        """

        parameters.append(
            department
        )

    if level:

        query += """
            AND level = ?

        """

        parameters.append(
            level
        )

    query += """
        ORDER BY full_name ASC

    """

    students = connection.execute(
        query,
        parameters
    ).fetchall()

    departments = connection.execute(
        """
        SELECT DISTINCT department

        FROM users

        WHERE profile_visible = 1

        ORDER BY department ASC

        """
    ).fetchall()

    levels = connection.execute(
        """
        SELECT DISTINCT level

        FROM users

        WHERE profile_visible = 1

        ORDER BY level ASC

        """
    ).fetchall()

    connection.close()

    return render_template(
        "discover.html",

        user=user,

        students=students,

        departments=departments,

        levels=levels,

        search=search,

        selected_department=department,

        selected_level=level

    )


# -----------------------------
# CREATE POST
# -----------------------------

@app.route("/create-post", methods=["GET", "POST"])
def create_post():

    user = get_current_user()

    if not user:

        return redirect(
            url_for("login")
        )

    if request.method == "POST":

        content = request.form.get(
            "content",
            ""
        ).strip()

        media = request.files.get(
            "media"
        )

        media_filename = ""

        media_type = ""

        if media and media.filename:

            original_filename = secure_filename(
                media.filename
            )

            file_extension = os.path.splitext(
                original_filename
            )[1].lower()

            allowed_images = {
                ".png",
                ".jpg",
                ".jpeg",
                ".gif",
                ".webp"
            }

            allowed_videos = {
                ".mp4",
                ".mov",
                ".webm"
            }

            if file_extension not in (
                allowed_images | allowed_videos
            ):

                flash(
                    "Only supported image and video files are allowed.",
                    "error"
                )

                return redirect(
                    url_for("create_post")
                )

            media_filename = (
                f"{uuid.uuid4().hex}{file_extension}"
            )

            if file_extension in allowed_images:

                media_type = "image"

            else:

                media_type = "video"

            os.makedirs(
                UPLOAD_FOLDER,
                exist_ok=True
            )

            media.save(
                os.path.join(
                    UPLOAD_FOLDER,
                    media_filename
                )
            )

        if not content and not media_filename:

            flash(
                "Write something or upload a picture/video.",
                "error"
            )

            return redirect(
                url_for("create_post")
            )

        if len(content) > 2000:

            flash(
                "Your post is too long. Keep it under 2000 characters.",
                "error"
            )

            return redirect(
                url_for("create_post")
            )

        connection = get_db()

        connection.execute(
            """
            INSERT INTO posts (

                user_id,

                content,

                media_filename,

                media_type

            )

            VALUES (?, ?, ?, ?)

            """,
            (
                user["id"],

                content,

                media_filename,

                media_type

            )
        )

        connection.commit()

        connection.close()

        flash(
            "Your post was published successfully!",
            "success"
        )

        return redirect(
            url_for("dashboard")
        )

    return render_template(
        "create_post.html",
        user=user
    )
# -----------------------------
# LIKE / UNLIKE POST
# -----------------------------

@app.route("/like/<int:post_id>", methods=["POST"])
def like_post(post_id):

    user = get_current_user()

    if not user:

        if request.headers.get(
            "X-Requested-With"
        ) == "XMLHttpRequest":

            return jsonify({
                "success": False,
                "message": "Please log in first."
            }), 401

        return redirect(
            url_for("login")
        )

    if not post_exists(post_id):

        return jsonify({
            "success": False,
            "message": "Post not found."
        }), 404

    connection = get_db()

    existing_like = connection.execute(
        """
        SELECT id

        FROM likes

        WHERE user_id = ?

        AND post_id = ?

        """,
        (
            user["id"],
            post_id
        )
    ).fetchone()

    if existing_like:

        connection.execute(
            """
            DELETE FROM likes

            WHERE user_id = ?

            AND post_id = ?

            """,
            (
                user["id"],
                post_id
            )
        )

        liked = False

    else:

        connection.execute(
            """
            INSERT INTO likes (
                user_id,
                post_id
            )

            VALUES (?, ?)

            """,
            (
                user["id"],
                post_id
            )
        )

        liked = True

    connection.commit()

    like_count = connection.execute(
        """
        SELECT COUNT(*)

        FROM likes

        WHERE post_id = ?

        """,
        (post_id,)
    ).fetchone()[0]

    connection.close()

    if request.headers.get(
        "X-Requested-With"
    ) == "XMLHttpRequest":

        return jsonify({
            "success": True,
            "liked": liked,
            "like_count": like_count
        })

    return redirect(
        request.referrer
        or url_for("dashboard")
    )


# -----------------------------
# ADD COMMENT
# -----------------------------

@app.route("/comment/<int:post_id>", methods=["POST"])
def add_comment(post_id):

    user = get_current_user()

    if not user:

        if request.headers.get(
            "X-Requested-With"
        ) == "XMLHttpRequest":

            return jsonify({
                "success": False,
                "message": "Please log in first."
            }), 401

        return redirect(
            url_for("login")
        )

    content = request.form.get(
        "content",
        ""
    ).strip()

    is_ajax = (
        request.headers.get(
            "X-Requested-With"
        ) == "XMLHttpRequest"
        or request.is_json
    )

    def comment_error(
        message,
        status_code=400
    ):

        if is_ajax:

            return jsonify({
                "success": False,
                "message": message
            }), status_code

        flash(
            message,
            "error"
        )

        return redirect(
            request.referrer
            or url_for("dashboard")
        )

    if not content:

        return comment_error(
            "Comment cannot be empty."
        )

    if len(content) > 500:

        return comment_error(
            "Comment must be under 500 characters."
        )

    if not post_exists(post_id):

        return comment_error(
            "Post not found.",
            404
        )

    connection = get_db()

    cursor = connection.execute(
        """
        INSERT INTO comments (
            user_id,
            post_id,
            content
        )

        VALUES (?, ?, ?)

        """,
        (
            user["id"],
            post_id,
            content
        )
    )

    comment_id = cursor.lastrowid

    connection.commit()

    comment = connection.execute(
        """
        SELECT

            comments.id,

            comments.content,

            comments.created_at,

            users.id AS user_id,

            users.full_name,

            users.profile_picture

        FROM comments

        JOIN users
        ON comments.user_id = users.id

        WHERE comments.id = ?

        """,
        (comment_id,)
    ).fetchone()

    connection.close()

    response_data = {

        "success": True,

        "message": "Comment added successfully.",

        "comment": {

            "id": comment["id"],

            "content": comment["content"],

            "created_at": comment["created_at"],

            "user_id": comment["user_id"],

            "full_name": comment["full_name"],

            "profile_picture": comment["profile_picture"]

        }

    }

    if is_ajax:

        return jsonify(
            response_data
        )

    flash(
        "Comment added successfully.",
        "success"
    )

    return redirect(
        request.referrer
        or url_for("dashboard")
    )


# -----------------------------
# GET COMMENTS FOR A POST
# -----------------------------

@app.route("/comments/<int:post_id>", methods=["GET"])
def get_comments(post_id):

    user = get_current_user()

    if not user:

        return jsonify({
            "success": False,
            "message": "Please log in first."
        }), 401

    if not post_exists(post_id):

        return jsonify({
            "success": False,
            "message": "Post not found."
        }), 404

    connection = get_db()

    comments = connection.execute(
        """
        SELECT

            comments.id,

            comments.content,

            comments.created_at,

            users.id AS user_id,

            users.full_name,

            users.profile_picture

        FROM comments

        JOIN users
        ON comments.user_id = users.id

        WHERE comments.post_id = ?

        ORDER BY comments.id ASC

        """,
        (post_id,)
    ).fetchall()

    connection.close()

    comments_data = []

    for comment in comments:

        comments_data.append({

            "id": comment["id"],

            "content": comment["content"],

            "created_at": comment["created_at"],

            "user_id": comment["user_id"],

            "full_name": comment["full_name"],

            "profile_picture": comment["profile_picture"]

        })

    return jsonify({

        "success": True,

        "comments": comments_data

    })


# -----------------------------
# SHARE / UNSHARE POST
# -----------------------------

@app.route("/share/<int:post_id>", methods=["POST"])
def share_post(post_id):

    user = get_current_user()

    if not user:

        return jsonify({
            "success": False,
            "message": "Please log in first."
        }), 401

    if not post_exists(post_id):

        return jsonify({
            "success": False,
            "message": "Post not found."
        }), 404

    connection = get_db()

    existing_share = connection.execute(
        """
        SELECT id

        FROM shares

        WHERE user_id = ?

        AND post_id = ?

        """,
        (
            user["id"],
            post_id
        )
    ).fetchone()

    if existing_share:

        connection.execute(
            """
            DELETE FROM shares

            WHERE user_id = ?

            AND post_id = ?

            """,
            (
                user["id"],
                post_id
            )
        )

        shared = False

    else:

        connection.execute(
            """
            INSERT INTO shares (
                user_id,
                post_id
            )

            VALUES (?, ?)

            """,
            (
                user["id"],
                post_id
            )
        )

        shared = True

    connection.commit()

    share_count = connection.execute(
        """
        SELECT COUNT(*)

        FROM shares

        WHERE post_id = ?

        """,
        (post_id,)
    ).fetchone()[0]

    connection.close()

    return jsonify({

        "success": True,

        "shared": shared,

        "share_count": share_count

    })


# -----------------------------
# PIN / UNPIN POST
# -----------------------------

@app.route("/pin/<int:post_id>", methods=["POST"])
def pin_post(post_id):

    user = get_current_user()

    if not user:

        return jsonify({
            "success": False,
            "message": "Please log in first."
        }), 401

    if not post_exists(post_id):

        return jsonify({
            "success": False,
            "message": "Post not found."
        }), 404

    connection = get_db()

    existing_pin = connection.execute(
        """
        SELECT id

        FROM pins

        WHERE user_id = ?

        AND post_id = ?

        """,
        (
            user["id"],
            post_id
        )
    ).fetchone()

    if existing_pin:

        connection.execute(
            """
            DELETE FROM pins

            WHERE user_id = ?

            AND post_id = ?

            """,
            (
                user["id"],
                post_id
            )
        )

        pinned = False

    else:

        connection.execute(
            """
            INSERT INTO pins (
                user_id,
                post_id
            )

            VALUES (?, ?)

            """,
            (
                user["id"],
                post_id
            )
        )

        pinned = True

    connection.commit()

    connection.close()

    return jsonify({

        "success": True,

        "pinned": pinned

    })
# -----------------------------
# FOLLOW / UNFOLLOW USER
# -----------------------------

@app.route("/follow/<int:user_id>", methods=["POST"])
def follow_user(user_id):

    current_user = get_current_user()

    if not current_user:
        return jsonify({
            "success": False,
            "message": "Please log in first."
        }), 401

    if current_user["id"] == user_id:
        return jsonify({
            "success": False,
            "message": "You cannot follow yourself."
        }), 400

    connection = get_db()

    target_user = connection.execute(
        """
        SELECT id
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    ).fetchone()

    if not target_user:
        connection.close()

        return jsonify({
            "success": False,
            "message": "User not found."
        }), 404

    existing_follow = connection.execute(
        """
        SELECT id
        FROM follows
        WHERE follower_id = ?
        AND following_id = ?
        """,
        (
            current_user["id"],
            user_id
        )
    ).fetchone()

    if existing_follow:

        # UNFOLLOW
        connection.execute(
            """
            DELETE FROM follows
            WHERE follower_id = ?
            AND following_id = ?
            """,
            (
                current_user["id"],
                user_id
            )
        )

        following = False

    else:

        # FOLLOW
        connection.execute(
            """
            INSERT INTO follows (
                follower_id,
                following_id
            )
            VALUES (?, ?)
            """,
            (
                current_user["id"],
                user_id
            )
        )

        following = True

        # CREATE NOTIFICATION
        connection.execute(
            """
            INSERT INTO notifications (
                recipient_id,
                sender_id,
                type,
                message,
                post_id,
                is_read
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                current_user["id"],
                "follow",
                f'{current_user["full_name"]} started following you.',
                None,
                0
            )
        )



    connection.commit()

    follower_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM follows
        WHERE following_id = ?
        """,
        (user_id,)
    ).fetchone()[0]

    connection.close()

    return jsonify({
        "success": True,
        "following": following,
        "follower_count": follower_count
    })
# -----------------------------
# CHAT
# -----------------------------

@app.route("/chat")
def chat():

    current_user = get_current_user()

    if not current_user:
        return redirect(
            url_for("login")
        )

    connection = get_db()

    users = connection.execute(
        """
        SELECT
            id,
            full_name,
            department,
            level,
            profile_picture
        FROM users
        WHERE id != ?
        AND profile_visible = 1
        ORDER BY full_name ASC
        """,
        (current_user["id"],)
    ).fetchall()

    conversations = connection.execute(
        """
        SELECT
            u.id,
            u.full_name,
            u.department,
            u.level,
            u.profile_picture,
            (
                SELECT m.content
                FROM messages m
                WHERE
                    (m.sender_id = u.id AND m.receiver_id = ?)
                    OR
                    (m.sender_id = ? AND m.receiver_id = u.id)
                ORDER BY m.id DESC
                LIMIT 1
            ) AS last_message,
            (
                SELECT m.created_at
                FROM messages m
                WHERE
                    (m.sender_id = u.id AND m.receiver_id = ?)
                    OR
                    (m.sender_id = ? AND m.receiver_id = u.id)
                ORDER BY m.id DESC
                LIMIT 1
            ) AS created_at
        FROM users u
        WHERE u.id != ?
        AND EXISTS (
            SELECT 1
            FROM messages m
            WHERE
                (m.sender_id = u.id AND m.receiver_id = ?)
                OR
                (m.sender_id = ? AND m.receiver_id = u.id)
        )
        ORDER BY created_at DESC
        """,
        (
            current_user["id"],
            current_user["id"],
            current_user["id"],
            current_user["id"],
            current_user["id"],
            current_user["id"],
            current_user["id"]
        )
    ).fetchall()

    connection.close()

    return render_template(
        "chat.html",
        current_user=current_user,
        users=users,
        conversations=conversations,
        selected_user=None,
        messages=[]
    )


# -----------------------------
# OPEN CHAT
# -----------------------------

@app.route("/chat/<int:user_id>")
def open_chat(user_id):

    current_user = get_current_user()

    if not current_user:
        return redirect(
            url_for("login")
        )

    if current_user["id"] == user_id:
        return redirect(
            url_for("chat")
        )

    connection = get_db()

    selected_user = connection.execute(
        """
        SELECT
            id,
            full_name,
            department,
            level,
            profile_picture
        FROM users
        WHERE id = ?
        AND profile_visible = 1
        """,
        (user_id,)
    ).fetchone()

    if not selected_user:
        connection.close()
        flash(
            "Student not found.",
            "error"
        )
        return redirect(
            url_for("chat")
        )

    users = connection.execute(
        """
        SELECT
            id,
            full_name,
            department,
            level,
            profile_picture
        FROM users
        WHERE id != ?
        AND profile_visible = 1
        ORDER BY full_name ASC
        """,
        (current_user["id"],)
    ).fetchall()

    conversations = connection.execute(
        """
        SELECT
            u.id,
            u.full_name,
            u.department,
            u.level,
            u.profile_picture,
            (
                SELECT m.content
                FROM messages m
                WHERE
                    (m.sender_id = u.id AND m.receiver_id = ?)
                    OR
                    (m.sender_id = ? AND m.receiver_id = u.id)
                ORDER BY m.id DESC
                LIMIT 1
            ) AS last_message,
            (
                SELECT m.created_at
                FROM messages m
                WHERE
                    (m.sender_id = u.id AND m.receiver_id = ?)
                    OR
                    (m.sender_id = ? AND m.receiver_id = u.id)
                ORDER BY m.id DESC
                LIMIT 1
            ) AS created_at
        FROM users u
        WHERE u.id != ?
        AND EXISTS (
            SELECT 1
            FROM messages m
            WHERE
                (m.sender_id = u.id AND m.receiver_id = ?)
                OR
                (m.sender_id = ? AND m.receiver_id = u.id)
        )
        ORDER BY created_at DESC
        """,
        (
            current_user["id"],
            current_user["id"],
            current_user["id"],
            current_user["id"],
            current_user["id"],
            current_user["id"],
            current_user["id"]
        )
    ).fetchall()

    messages = connection.execute(
        """
        SELECT
            id,
            sender_id,
            receiver_id,
            content,
            created_at
        FROM messages
        WHERE
            (sender_id = ? AND receiver_id = ?)
            OR
            (sender_id = ? AND receiver_id = ?)
        ORDER BY id ASC
        """,
        (
            current_user["id"],
            user_id,
            user_id,
            current_user["id"]
        )
    ).fetchall()

    connection.close()

    return render_template(
        "chat.html",
        current_user=current_user,
        users=users,
        conversations=conversations,
        selected_user=selected_user,
        messages=messages
    )


# -----------------------------
# SEND MESSAGE
# -----------------------------

@app.route("/send-message", methods=["POST"])
def send_message():

    current_user = get_current_user()

    if not current_user:
        return jsonify({
            "success": False,
            "message": "Please log in first."
        }), 401

    receiver_id = request.form.get(
        "receiver_id",
        ""
    ).strip()

    content = request.form.get(
        "content",
        ""
    ).strip()

    if not receiver_id or not content:
        return jsonify({
            "success": False,
            "message": "Message cannot be empty."
        }), 400

    try:
        receiver_id = int(receiver_id)
    except ValueError:
        return jsonify({
            "success": False,
            "message": "Invalid receiver."
        }), 400

    if receiver_id == current_user["id"]:
        return jsonify({
            "success": False,
            "message": "You cannot message yourself."
        }), 400

    if len(content) > 2000:
        return jsonify({
            "success": False,
            "message": "Message is too long."
        }), 400

    connection = get_db()

    receiver = connection.execute(
        "SELECT id FROM users WHERE id = ?",
        (receiver_id,)
    ).fetchone()

    if not receiver:
        connection.close()
        return jsonify({
            "success": False,
            "message": "Student not found."
        }), 404

    cursor = connection.execute(
        """
        INSERT INTO messages (
            sender_id,
            receiver_id,
            content
        )
        VALUES (?, ?, ?)
        """,
        (
            current_user["id"],
            receiver_id,
            content
        )
    )

    message_id = cursor.lastrowid
    connection.commit()

    message = connection.execute(
        """
        SELECT
            id,
            sender_id,
            receiver_id,
            content,
            created_at
        FROM messages
        WHERE id = ?
        """,
        (message_id,)
    ).fetchone()

    connection.close()

    return jsonify({
        "success": True,
        "message": {
            "id": message["id"],
            "sender_id": message["sender_id"],
            "receiver_id": message["receiver_id"],
            "content": message["content"],
            "created_at": message["created_at"]
        }
    })


# -----------------------------
# BUSINESS REGISTRATION
# -----------------------------

@app.route("/business/register", methods=["GET", "POST"])
def business_register():

    current_user = get_current_user()

    if not current_user:
        return redirect(
            url_for("login")
        )

    if request.method == "POST":

        business_name = request.form.get(
            "business_name",
            ""
        ).strip()

        category = request.form.get(
            "category",
            ""
        ).strip().lower()

        description = request.form.get(
            "description",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        location = request.form.get(
            "location",
            ""
        ).strip()

        logo = request.files.get(
            "logo"
        )

        if not business_name or not category:
            flash(
                "Business name and category are required.",
                "error"
            )
            return redirect(
                url_for("business_register")
            )

        if category not in BUSINESS_CATEGORIES:
            flash(
                "Please choose a valid business category.",
                "error"
            )
            return redirect(
                url_for("business_register")
            )

        logo_filename = ""

        if logo and logo.filename:

            if not allowed_file(logo.filename):
                flash(
                    "Unsupported logo image format.",
                    "error"
                )
                return redirect(
                    url_for("business_register")
                )

            safe_name = secure_filename(
                logo.filename
            )

            logo_filename = (
                f"business_{current_user['id']}_{uuid.uuid4().hex}_{safe_name}"
            )

            logo.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    logo_filename
                )
            )

        connection = get_db()

        # Keep one active/pending business of the same category per owner.
        existing_business = connection.execute(
            """
            SELECT id
            FROM businesses
            WHERE owner_id = ?
            AND category = ?
            AND verification_status IN ('pending', 'approved')
            """,
            (
                current_user["id"],
                category
            )
        ).fetchone()

        if existing_business:
            connection.close()
            flash(
                "You already have a pending or approved business in this category.",
                "error"
            )
            return redirect(
                url_for("business_register")
            )

        connection.execute(
            """
            INSERT INTO businesses (
                owner_id,
                business_name,
                category,
                description,
                phone,
                location,
                logo_filename,
                verification_status,
                commission_rate,
                is_active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?, 0)
            """,
            (
                current_user["id"],
                business_name,
                category,
                description,
                phone,
                location,
                logo_filename,
                DEFAULT_COMMISSION_RATE
            )
        )

        # Create notification for the business owner
        connection.execute(
            """
            INSERT INTO notifications (
                recipient_id,
                sender_id,
                type,
                message,
                post_id,
                is_read
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                current_user["id"],
                current_user["id"],
                "business_review",
                f'Your business "{business_name}" has been submitted and is now under review.',
                None,
                0
            )
        )

        connection.commit()
        connection.close()

        flash(
            "Business submitted successfully. Your business is now under review.",
            "success"
        )

        return redirect(
            url_for("business_my")
        )

    return render_template(
        "business_register.html",
        categories=BUSINESS_CATEGORIES
    )


# -----------------------------
# MY BUSINESSES
# -----------------------------

@app.route("/business/my")
def business_my():

    current_user = get_current_user()

    if not current_user:
        return redirect(
            url_for("login")
        )

    connection = get_db()

    businesses = connection.execute(
        """
        SELECT *
        FROM businesses
        WHERE owner_id = ?
        ORDER BY id DESC
        """,
        (current_user["id"],)
    ).fetchall()

    connection.close()

    return render_template(
        "business_my.html",
        businesses=businesses
    )


# -----------------------------
# BUSINESS DIRECTORY
# -----------------------------

@app.route("/business/<category>")
def business_directory(category):

    if category not in BUSINESS_CATEGORIES:
        return redirect(
            url_for("dashboard")
        )

    current_user = get_current_user()

    if not current_user:
        return redirect(
            url_for("login")
        )

    connection = get_db()

    businesses = connection.execute(
        """
        SELECT
            businesses.*,
            users.full_name AS owner_name
        FROM businesses
        JOIN users
        ON businesses.owner_id = users.id
        WHERE businesses.category = ?
        AND businesses.verification_status = 'approved'
        AND businesses.is_active = 1
        ORDER BY businesses.id DESC
        """,
        (category,)
    ).fetchall()

    connection.close()

    return render_template(
        "business_directory.html",
        businesses=businesses,
        category=category,
        category_name=BUSINESS_CATEGORIES[category]
    )


# -----------------------------
# BUSINESS PROFILE
# -----------------------------

@app.route("/business/profile/<int:business_id>")
def business_profile(business_id):

    current_user = get_current_user()

    if not current_user:
        return redirect(
            url_for("login")
        )

    connection = get_db()

    business = connection.execute(
        """
        SELECT
            businesses.*,
            users.full_name AS owner_name
        FROM businesses
        JOIN users
        ON businesses.owner_id = users.id
        WHERE businesses.id = ?
        AND businesses.verification_status = 'approved'
        AND businesses.is_active = 1
        """,
        (business_id,)
    ).fetchone()

    connection.close()

    if not business:
        flash(
            "Business not found or not yet verified.",
            "error"
        )
        return redirect(
            url_for("dashboard")
        )

    return render_template(
        "business_profile.html",
        business=business
    )


# -----------------------------
# ADMIN BUSINESS VERIFICATION
# -----------------------------

def is_admin():

    current_user = get_current_user()

    return bool(
        current_user
        and current_user["email"].lower() == ADMIN_EMAIL.lower()
    )


@app.route("/admin/businesses")
def admin_businesses():

    if not is_admin():
        flash(
            "Admin access required.",
            "error"
        )
        return redirect(
            url_for("dashboard")
        )

    connection = get_db()

    businesses = connection.execute(
        """
        SELECT
            businesses.*,
            users.full_name AS owner_name,
            users.email AS owner_email
        FROM businesses
        JOIN users
        ON businesses.owner_id = users.id
        ORDER BY
            CASE
                WHEN businesses.verification_status = 'pending' THEN 0
                ELSE 1
            END,
            businesses.id DESC
        """
    ).fetchall()

    connection.close()

    return render_template(
        "admin_businesses.html",
        businesses=businesses
    )


@app.route("/admin/business/<int:business_id>/verify", methods=["POST"])
def verify_business(business_id):

    if not is_admin():
        return jsonify({
            "success": False,
            "message": "Admin access required."
        }), 403

    connection = get_db()

    business = connection.execute(
        """
        SELECT id, owner_id, business_name
        FROM businesses
        WHERE id = ?
        """,
        (business_id,)
    ).fetchone()

    if not business:
        connection.close()
        return jsonify({
            "success": False,
            "message": "Business not found."
        }), 404

    connection.execute(
        """
        UPDATE businesses
        SET verification_status = 'approved',
            rejection_reason = '',
            is_active = 1,
            verified_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (business_id,)
    )

    # Notify the business owner that the business has been approved.
    admin_user = get_current_user()
    connection.execute(
        """
        INSERT INTO notifications (
            recipient_id,
            sender_id,
            type,
            message,
            post_id,
            is_read
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            business["owner_id"],
            admin_user["id"],
            "business_approved",
            f'Your business "{business["business_name"]}" has been approved and is now live on FUTA Meet.',
            None,
            0
        )
    )

    connection.commit()
    connection.close()

    return redirect(
        url_for("admin_businesses")
    )


@app.route("/admin/business/<int:business_id>/reject", methods=["POST"])
def reject_business(business_id):

    if not is_admin():
        return jsonify({
            "success": False,
            "message": "Admin access required."
        }), 403

    rejection_reason = request.form.get(
        "rejection_reason",
        ""
    ).strip()

    connection = get_db()

    business = connection.execute(
        """
        SELECT id, owner_id, business_name
        FROM businesses
        WHERE id = ?
        """,
        (business_id,)
    ).fetchone()

    if not business:
        connection.close()
        return jsonify({
            "success": False,
            "message": "Business not found."
        }), 404

    connection.execute(
        """
        UPDATE businesses
        SET verification_status = 'rejected',
            rejection_reason = ?,
            is_active = 0
        WHERE id = ?
        """,
        (
            rejection_reason,
            business_id
        )
    )

    # Notify the business owner that the application was rejected.
    admin_user = get_current_user()
    reason_text = rejection_reason or "No reason was provided."
    connection.execute(
        """
        INSERT INTO notifications (
            recipient_id,
            sender_id,
            type,
            message,
            post_id,
            is_read
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            business["owner_id"],
            admin_user["id"],
            "business_rejected",
            f'Your business "{business["business_name"]}" was not approved. Reason: {reason_text}',
            None,
            0
        )
    )

    connection.commit()
    connection.close()

    return redirect(
        url_for("admin_businesses")
    )


# -----------------------------
# NOTIFICATIONS
# -----------------------------

@app.route("/notifications")
def notifications():

    current_user = get_current_user()

    if not current_user:
        return redirect(
            url_for("login")
        )

    connection = get_db()

    notifications = connection.execute(
        """
        SELECT
            notifications.id,
            notifications.type,
            notifications.message,
            notifications.post_id,
            notifications.is_read,
            notifications.created_at,

            users.id AS sender_id,
            CASE
                WHEN notifications.type IN ('business_review', 'business_approved', 'business_rejected')
                THEN 'FUTA Meet'
                ELSE users.full_name
            END AS sender_name,
            CASE
                WHEN notifications.type IN ('business_review', 'business_approved', 'business_rejected')
                THEN NULL
                ELSE users.profile_picture
            END AS sender_picture

        FROM notifications

        JOIN users
        ON notifications.sender_id = users.id

        WHERE notifications.recipient_id = ?

        ORDER BY notifications.id DESC
        """,
        (current_user["id"],)
    ).fetchall()

    connection.close()

    return render_template(
        "notifications.html",
        notifications=notifications
    )
    
# -----------------------------
# LOGOUT
# -----------------------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("home")
    )


# -----------------------------
# START APPLICATION
# -----------------------------

if __name__ == "__main__":

    init_db()

    app.run(
        debug=True
    )