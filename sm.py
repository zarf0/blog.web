import os
import streamlit as st
import sqlite3
from datetime import datetime


conn = sqlite3.connect("blog.db")
c = conn.cursor()

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



def get_all_posts():
    c.execute("SELECT * FROM posts ORDER BY created_at DESC")
    return c.fetchall()



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
                st.write(post[3])  
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



def increment_like(post_id):
    c.execute("UPDATE posts SET likes = likes + 1 WHERE id=?", (post_id,))
    conn.commit()


def get_comments_for_post(post_id):
    c.execute("SELECT * FROM comments WHERE post_id=?", (post_id,))
    return c.fetchall()



def create_comment(post_id, user_id, parent_id, comment):
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute(
        "INSERT INTO comments (post_id, user_id, parent_id, comment, created_at) VALUES (?, ?, ?, ?, ?)",
        (post_id, user_id, parent_id, comment, created_at),
    )
    conn.commit()
    st.success("Comment posted successfully!")



def get_user_posts(user_id):
    c.execute("SELECT * FROM posts WHERE user_id=?", (user_id,))
    return c.fetchall()



def delete_post(post_id):
    c.execute("DELETE FROM posts WHERE id=?", (post_id,))
    conn.commit()



def register_user(username, email, password, profile_picture):
    c.execute(
        "INSERT INTO users (username, email, password, role, profile_picture) VALUES (?, ?, ?, ?, ?)",
        (username, email, password, "user", profile_picture),
    )
    conn.commit()
    st.success("Registration successful!")



def authenticate(username, password):
    c.execute(
        "SELECT * FROM users WHERE username=? AND password=?", (username, password)
    )
    return c.fetchone() is not None

def register_user_with_profile_picture(username, email, password, profile_picture):
    profile_picture_path = save_uploaded_image(profile_picture)
    register_user(username, email, password, profile_picture_path)


def logout():
    st.session_state.authenticated = False
    st.session_state.user_id = None
    st.success("Logged out successfully!")



def main():
    st.set_page_config(
        page_title="Advanced Blog Website", page_icon=":memo:", layout="wide"
    )

    st.title("📝 Advanced Blog Website")


    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    menu = ["Home", "Create Post", "View Posts", "Delete Posts", "Profile", "Logout"]
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
                ):  
                    create_post(title, content, st.session_state.user_id)
                else:
                    st.warning("Please enter title and content.")
        else:
            st.warning("Please log in to create a post.")

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

    elif choice == "Profile":
        st.subheader("User Profile Dashboard")
        if st.session_state.authenticated:
       
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

       
        new_bio = st.text_area("Update Bio:", value="", key="new_bio")
        new_profile_picture = st.file_uploader(
            "Upload Profile Picture", type=["jpg", "jpeg", "png"], key="profile_pic"
        )
        if st.button("Update Profile"):
            update_user_profile(st.session_state.user_id, new_bio, new_profile_picture)

    elif choice == "Logout":
        logout()


def save_uploaded_image(uploaded_image):
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
    image_path = os.path.join("uploads", uploaded_image.name)
    with open(image_path, "wb") as f:
        f.write(uploaded_image.getbuffer())
    return image_path


def get_user_info(user_id):
    c.execute("SELECT * FROM users WHERE id=?", (user_id,))
    return c.fetchone()


def update_user_profile(user_id, new_bio, new_profile_picture):
    if new_bio:
        c.execute("UPDATE users SET bio=? WHERE id=?", (new_bio, user_id))
        conn.commit()
    if new_profile_picture:
        profile_picture_path = save_uploaded_image(new_profile_picture)
        c.execute(
            "UPDATE users SET profile_picture=? WHERE id=?",
            (profile_picture_path, user_id),
        )
        conn.commit()
    st.success("Profile updated successfully!")



def login_and_register():
    st.set_page_config(page_title="Login/Register", page_icon=":unlock:")
    st.title("Login/Register")

    choice = st.radio("Choose an action:", ("Login", "Register"))

    if choice == "Login":
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if authenticate(username, password):
                st.success("Logged in successfully!")
                st.session_state.authenticated = True
                st.session_state.user_id = 1  
                st.markdown("Redirecting to the home page...")
                st.experimental_rerun()
            else:
                st.error("Incorrect username or password.")

    elif choice == "Register":
        st.subheader("Register")
        username = st.text_input("Username:")
        email = st.text_input("Email:")
        password = st.text_input("Password:", type="password")
        confirm_password = st.text_input("Confirm Password:", type="password")
        profile_picture = st.file_uploader(
            "Upload Profile Picture", type=["jpg", "jpeg", "png"]
        )
        if st.button("Register"):
            if password == confirm_password:
                if profile_picture is not None:
                    register_user_with_profile_picture(
                        username, email, password, profile_picture
                    )
                else:
                    register_user(username, email, password, profile_picture=None)
            else:
                st.warning("Passwords do not match.")



if __name__ == "__main__":
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        login_and_register()
    else:
        main()
