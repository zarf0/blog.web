import os
import streamlit as st
import sqlite3
from datetime import datetime

# Create SQLite connection
conn = sqlite3.connect("blog.db")
c = conn.cursor()

# Create tables if not exists
c.execute(
    """CREATE TABLE IF NOT EXISTS posts 
             (id INTEGER PRIMARY KEY, user_id INTEGER, title TEXT, content TEXT, category TEXT, tags TEXT, likes INTEGER DEFAULT 0, created_at TEXT)"""
)

print("Posts table created successfully")

c.execute(
    """CREATE TABLE IF NOT EXISTS users 
             (id INTEGER PRIMARY KEY, username TEXT UNIQUE, email TEXT UNIQUE, password TEXT, role TEXT, verified INTEGER DEFAULT 0,
             profile_picture TEXT, bio TEXT)"""
)

print("Users table created successfully")

c.execute(
    """CREATE TABLE IF NOT EXISTS comments 
             (id INTEGER PRIMARY KEY, post_id INTEGER, user_id INTEGER, parent_id INTEGER, comment TEXT, created_at TEXT)"""
)

print("Comments table created successfully")

conn.commit()

# Function to create a new post
def create_post(title, content, user_id):
    if not st.session_state.authenticated:
        st.warning("Please log in to create a post.")
        return
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute(
        "INSERT INTO posts (user_id, title, content, created_at) VALUES (?, ?, ?, ?)",
        (user_id, title, content, created_at),
    )
    conn.commit()
    st.success("Post created successfully!")


# Function to retrieve all posts
def get_all_posts():
    c.execute("SELECT * FROM posts ORDER BY created_at DESC")
    return c.fetchall()


# Function to display paginated posts
def display_posts(posts, page_number, page_size=5):
    if not posts:
        st.info("No posts available.")
    else:
        start_index = page_number * page_size
        end_index = min((page_number + 1) * page_size, len(posts))
        paginated_posts = posts[start_index:end_index]
        for post in paginated_posts:
            st.write("---")
            with st.container():
                st.markdown(
                    f'<h2 style="font-family:sans-serif;color:#262626;">{post[2]}</h2>',
                    unsafe_allow_html=True,
                )
                st.write(post[3])  # Display post content
                st.markdown(
                    f"<p style='font-family:sans-serif;color:#666;'>Category: {post[4]}</p>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"<p style='font-family:sans-serif;color:#666;'>Tags: {post[5]}</p>",
                    unsafe_allow_html=True,
                )
                col1, col2 = st.columns([1, 3])
                with col1:
                    like_button_key = f"like_button_{post[0]}"
                    liked = st.session_state.get(like_button_key, False)
                    if st.button(
                        f"👍 Like ({post[6]})" if not liked else f"👍 Liked ({post[6]})",
                        key=like_button_key,
                        help="Like this post",
                    ):
                        if not liked:
                            increment_like(post[0])
                            st.session_state[like_button_key] = True
                            st.experimental_rerun()
                with col2:
                    with st.expander("Comments", expanded=False):
                        comments = get_comments_for_post(post[0])
                        for comment in comments:
                            st.write(f"- {comment[4]}")
                        comment_content = st.text_input(
                            f"Enter your comment for post {post[0]}:",
                            key=f"comment_input_{post[0]}",
                        )
                        if st.button(
                            "Post Comment", key=f"post_comment_button_{post[0]}"
                        ):
                            create_comment(
                                post[0],
                                st.session_state.user_id,
                                parent_id=None,
                                comment=comment_content,
                            )
        # Pagination
        st.write("---")
        total_pages = (len(posts) - 1) // page_size + 1
        if total_pages > 1:
            for page in range(total_pages):
                if page == page_number:
                    st.write(f"{page + 1}")
                else:
                    st.write(
                        st.markdown._get_widget_cache().set_key(
                            str(page), str(page + 1)
                        )
                    )
            st.write("---")


# Function to increment like count for a post
def increment_like(post_id):
    c.execute("UPDATE posts SET likes = likes + 1 WHERE id=?", (post_id,))
    conn.commit()

# Function to retrieve comments for a specific post
def get_comments_for_post(post_id):
    c.execute("SELECT * FROM comments WHERE post_id=?", (post_id,))
    return c.fetchall()


# Function to create a new comment
def create_comment(post_id, user_id, parent_id, comment):
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute(
        "INSERT INTO comments (post_id, user_id, parent_id, comment, created_at) VALUES (?, ?, ?, ?, ?)",
        (post_id, user_id, parent_id, comment, created_at),
    )
    conn.commit()
    st.success("Comment posted successfully!")


# Function to retrieve posts created by a specific user
def get_user_posts(user_id):
    c.execute("SELECT * FROM posts WHERE user_id=?", (user_id,))
    return c.fetchall()


# Function to delete a post
def delete_post(post_id):
    c.execute("DELETE FROM posts WHERE id=?", (post_id,))
    conn.commit()


# Function to register a new user
def register_user(username, email, password, profile_picture):
    c.execute(
        "INSERT INTO users (username, email, password, role, profile_picture) VALUES (?, ?, ?, ?, ?)",
        (username, email, password, "user", profile_picture),
    )
    conn.commit()
    st.success("Registration successful!")


# Function to authenticate user
def authenticate(username, password):
    c.execute(
        "SELECT * FROM users WHERE username=? AND password=?", (username, password)
    )
    return c.fetchone() is not None


# Main Streamlit app
def main():
    st.set_page_config(
        page_title="Advanced Blog Website", page_icon=":memo:", layout="wide"
    )

    st.title("📝 Advanced Blog Website")

    # Initialize session state variables
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    menu = ["Home", "Create Post", "View Posts", "Delete Posts", "Register", "Profile"]
    choice = st.sidebar.radio("Menu", menu)

    if choice == "Home":
        st.subheader("Welcome to the Advanced Blog Website")
        st.write("Feel free to create and view blog posts from the sidebar.")

    elif choice == "Create Post":
        st.subheader("Create New Post")
        if st.session_state.authenticated:
            title = st.text_input("Enter post title:", key="post_title")
            content = st.text_area(
                "Enter post content:", height=200, key="post_content"
            )
            if st.button("Create", key="create_post_button"):
                if (
                    title.strip() and content.strip()
                ):  # Check if title and content are not empty
                    create_post(title, content, st.session_state.user_id)
                else:
                    st.warning("Please enter title and content.")
        else:
            st.warning("Please log in to create a post.")

    # Other menu options remain unchanged...

    elif choice == "View Posts":
        st.subheader("All Posts")
        posts = get_all_posts()
        if posts:
            if "page_number" not in st.session_state:
                st.session_state.page_number = 0
            display_posts(posts, st.session_state.page_number)

    elif choice == "Delete Posts":
        st.subheader("Delete Posts")
        if st.session_state.authenticated:
            # Retrieve user's posts
            user_posts = get_user_posts(st.session_state.user_id)
            if not user_posts:
                st.info("You haven't created any posts yet.")
            else:
                post_ids = [post[0] for post in user_posts]
                post_to_delete = st.selectbox(
                    "Select post to delete:",
                    options=user_posts,
                    format_func=lambda x: x[2],
                )
                if st.button("Delete Post", key="delete_post_button"):
                    delete_post(post_to_delete[0])
                    st.success("Post deleted successfully.")
        else:
            st.warning("Please log in to delete posts.")

    elif choice == "Register":
        st.subheader("Register")
        username = st.text_input("Username:", key="register_username")
        email = st.text_input("Email:", key="register_email")
        password = st.text_input("Password:", type="password", key="register_password")
        confirm_password = st.text_input(
            "Confirm Password:", type="password", key="confirm_password"
        )
        if st.button("Register", key="register_button"):
            if password == confirm_password:
                register_user(username, email, password, profile_picture_path=None)
            else:
                st.warning("Passwords do not match.")

    elif choice == "Profile":
        st.subheader("User Profile Dashboard")
        if st.session_state.authenticated:
            # Retrieve user profile information
            user_info = get_user_info(st.session_state.user_id)
            st.write(f"Username: {user_info[1]}")
            st.write(f"Email: {user_info[2]}")
            st.write(f"Role: {user_info[4]}")
            st.write(f"Bio: {user_info[7]}")
            profile_picture = user_info[6]
            if profile_picture:
                st.image(
                    profile_picture,
                    caption="Profile Picture",
                    use_column_width=True,
                    output_format="JPEG",
                    output_width=150,
                )
        else:
            st.warning("Please log in to view your profile.")


# Function to retrieve user profile information
def get_user_info(user_id):
    c.execute("SELECT * FROM users WHERE id=?", (user_id,))
    return c.fetchone()


# Login Page
def login():
    st.set_page_config(page_title="Login", page_icon=":unlock:")
    st.title("Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    st.markdown("[Register](#)")
    st.markdown("[Forgot Password?](#)")

    if st.button("Login"):
        if authenticate(username, password):
            st.success("Logged in successfully!")
            st.session_state.authenticated = True
            st.session_state.user_id = 1  # Assuming user_id=1 for demo purposes
            st.markdown("Redirecting to the home page...")
            st.experimental_rerun()
        else:
            st.error("Incorrect username or password.")


# Run the app
if __name__ == "__main__":
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        login()
    else:
        main()
