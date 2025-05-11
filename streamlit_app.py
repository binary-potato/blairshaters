import streamlit as st
import pandas as pd
import numpy as np
import datetime
import hashlib
import uuid
import re
import base64
from PIL import Image
import io
import os

# Set page config
st.set_page_config(
    page_title="blairs haters",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables if they don't exist
if 'users' not in st.session_state:
    st.session_state.users = {
        'admin': {
            'password': hashlib.sha256('admin123'.encode()).hexdigest(),
            'name': 'Admin',
            'bio': 'Forum administrator',
            'joined_date': datetime.datetime.now().strftime('%Y-%m-%d'),
            'avatar': None
        }
    }

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    
if 'current_user' not in st.session_state:
    st.session_state.current_user = None

if 'posts' not in st.session_state:
    st.session_state.posts = {}
    
if 'categories' not in st.session_state:
    st.session_state.categories = ['General', 'Tech', 'Sports', 'Entertainment', 'Science']

if 'comments' not in st.session_state:
    st.session_state.comments = {}
    
if 'likes' not in st.session_state:
    st.session_state.likes = {}
    
# Custom functions
def generate_id():
    return str(uuid.uuid4())

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(username, password):
    if username in st.session_state.users:
        if st.session_state.users[username]['password'] == hash_password(password):
            return True
    return False

def save_uploaded_file(uploaded_file):
    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        encoded = base64.b64encode(file_bytes).decode()
        return encoded
    return None

def display_image(encoded_image):
    if encoded_image:
        binary_data = base64.b64decode(encoded_image)
        img = Image.open(io.BytesIO(binary_data))
        return img
    return None

def format_post_content(content):
    # Convert URLs to clickable links
    url_pattern = r'https?://[^\s]+'
    content = re.sub(url_pattern, r'<a href="\g<0>" target="_blank">\g<0></a>', content)
    
    # Convert markdown-style bold
    bold_pattern = r'\*\*(.*?)\*\*'
    content = re.sub(bold_pattern, r'<b>\1</b>', content)
    
    # Convert markdown-style italic
    italic_pattern = r'\*(.*?)\*'
    content = re.sub(italic_pattern, r'<i>\1</i>', content)
    
    # Convert markdown-style headings
    heading_pattern = r'^#{1,6}\s+(.+)$'
    lines = content.split('\n')
    for i, line in enumerate(lines):
        match = re.match(heading_pattern, line)
        if match:
            level = len(re.match(r'^(#+)', line).group(1))
            lines[i] = f'<h{level}>{match.group(1)}</h{level}>'
    content = '\n'.join(lines)
    
    # Convert markdown-style code blocks
    code_block_pattern = r'```(.*?)```'
    content = re.sub(code_block_pattern, r'<pre><code>\1</code></pre>', content, flags=re.DOTALL)
    
    # Convert GIF URLs to embedded GIFs
    gif_pattern = r'(https?://.*?\.gif)'
    content = re.sub(gif_pattern, r'<img src="\1" style="max-width:100%;">', content)
    
    return content

# Authentication functions
def login_page():
    st.title("Login to blairs haters")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit_button = st.form_submit_button("Login")
            
            if submit_button:
                if check_password(username, password):
                    st.session_state.logged_in = True
                    st.session_state.current_user = username
                    st.success("Login successful!")
                    st.experimental_rerun()
                else:
                    st.error("Invalid username or password")

    with col2:
        st.markdown("### New User?")
        signup_col1, signup_col2 = st.columns(2)
        
        with signup_col1:
            if st.button("Register", use_container_width=True):
                st.session_state.page = "register"
                st.experimental_rerun()
        
        with signup_col2:
            # Add demo account option
            if st.button("Try Demo", use_container_width=True):
                st.session_state.logged_in = True
                st.session_state.current_user = "admin"
                st.session_state.page = "home"
                st.experimental_rerun()

def register_page():
    st.title("Register for blairs haters")
    
    with st.form("register_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        name = st.text_input("Display Name")
        bio = st.text_area("Bio (optional)")
        avatar = st.file_uploader("Upload Avatar (optional)", type=["jpg", "jpeg", "png"])
        
        submit_button = st.form_submit_button("Register")
        
        if submit_button:
            if not username or not password or not name:
                st.error("Username, password, and display name are required")
                return
                
            if password != confirm_password:
                st.error("Passwords do not match")
                return
                
            if username in st.session_state.users:
                st.error("Username already exists")
                return
                
            # Save avatar if uploaded
            avatar_data = save_uploaded_file(avatar)
                
            # Create new user
            st.session_state.users[username] = {
                'password': hash_password(password),
                'name': name,
                'bio': bio,
                'joined_date': datetime.datetime.now().strftime('%Y-%m-%d'),
                'avatar': avatar_data
            }
            
            st.success("Registration successful! You can now log in.")
            st.session_state.page = "login"
            st.experimental_rerun()
    
    if st.button("Back to Login"):
        st.session_state.page = "login"
        st.experimental_rerun()

# Forum functions
def create_post_page():
    st.title("Create New Post")
    
    with st.form("post_form"):
        title = st.text_input("Post Title")
        category = st.selectbox("Category", st.session_state.categories)
        content = st.text_area("Content", height=300, help="You can use markdown formatting and include GIF URLs")
        image = st.file_uploader("Upload Image (optional)", type=["jpg", "jpeg", "png", "gif"])
        
        submit_button = st.form_submit_button("Post")
        
        if submit_button:
            if not title or not content:
                st.error("Title and content are required")
                return
                
            # Save image if uploaded
            image_data = save_uploaded_file(image)
            
            # Create new post
            post_id = generate_id()
            st.session_state.posts[post_id] = {
                'title': title,
                'category': category,
                'content': content,
                'image': image_data,
                'author': st.session_state.current_user,
                'author_name': st.session_state.users[st.session_state.current_user]['name'],
                'date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'views': 0
            }
            
            # Initialize comments and likes for this post
            st.session_state.comments[post_id] = []
            st.session_state.likes[post_id] = []
            
            st.success("Post created successfully!")
            st.session_state.page = "home"
            st.experimental_rerun()
    
    if st.button("Cancel"):
        st.session_state.page = "home"
        st.experimental_rerun()

def view_post_page(post_id):
    if post_id not in st.session_state.posts:
        st.error("Post not found")
        return
    
    post = st.session_state.posts[post_id]
    
    # Increment view count
    post['views'] += 1
    
    # Display post
    st.title(post['title'])
    
    col1, col2, col3 = st.columns([1, 5, 1])
    
    with col1:
        if post['author'] in st.session_state.users and st.session_state.users[post['author']]['avatar']:
            avatar_img = display_image(st.session_state.users[post['author']]['avatar'])
            if avatar_img:
                st.image(avatar_img, width=100)
        else:
            st.markdown("👤")
        st.write(f"**{post['author_name']}**")
    
    with col2:
        st.markdown(f"**Category**: {post['category']}")
        st.markdown(f"**Posted on**: {post['date']}")
        st.markdown(f"**Views**: {post['views']}")
        
        st.markdown("---")
        
        # Display content with markdown formatting
        st.markdown(format_post_content(post['content']), unsafe_allow_html=True)
        
        if post['image']:
            st.image(display_image(post['image']), use_column_width=True)
        
        # Like button
        like_count = len(st.session_state.likes[post_id])
        if st.button(f"👍 Like ({like_count})"):
            if st.session_state.current_user not in st.session_state.likes[post_id]:
                st.session_state.likes[post_id].append(st.session_state.current_user)
                st.experimental_rerun()
            else:
                st.session_state.likes[post_id].remove(st.session_state.current_user)
                st.experimental_rerun()
    
    st.markdown("---")
    
    # Comments section
    st.subheader("Comments")
    
    # Display existing comments
    for i, comment in enumerate(st.session_state.comments[post_id]):
        comment_col1, comment_col2 = st.columns([1, 5])
        
        with comment_col1:
            if comment['author'] in st.session_state.users and st.session_state.users[comment['author']]['avatar']:
                avatar_img = display_image(st.session_state.users[comment['author']]['avatar'])
                if avatar_img:
                    st.image(avatar_img, width=50)
            else:
                st.markdown("👤")
            st.write(f"**{comment['author_name']}**")
        
        with comment_col2:
            st.markdown(f"*{comment['date']}*")
            st.markdown(format_post_content(comment['content']), unsafe_allow_html=True)
            
            if comment['image']:
                st.image(display_image(comment['image']), use_column_width=True)
        
        st.markdown("---")
    
    # Add new comment
    st.subheader("Add Comment")
    
    with st.form("comment_form"):
        comment_content = st.text_area("Comment", height=100, help="You can use markdown formatting and include GIF URLs")
        comment_image = st.file_uploader("Upload Image (optional)", type=["jpg", "jpeg", "png", "gif"])
        
        submit_comment = st.form_submit_button("Post Comment")
        
        if submit_comment:
            if not comment_content:
                st.error("Comment cannot be empty")
                return
                
            # Save image if uploaded
            comment_image_data = save_uploaded_file(comment_image)
            
            # Add new comment
            st.session_state.comments[post_id].append({
                'content': comment_content,
                'image': comment_image_data,
                'author': st.session_state.current_user,
                'author_name': st.session_state.users[st.session_state.current_user]['name'],
                'date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            
            st.success("Comment added successfully!")
            st.experimental_rerun()
    
    if st.button("Back to Forum"):
        st.session_state.page = "home"
        st.experimental_rerun()

def profile_page(username=None):
    if username is None:
        username = st.session_state.current_user
    
    if username not in st.session_state.users:
        st.error("User not found")
        return
    
    user = st.session_state.users[username]
    
    st.title(f"{user['name']}'s Profile")
    
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if user['avatar']:
            avatar_img = display_image(user['avatar'])
            if avatar_img:
                st.image(avatar_img, width=200)
        else:
            st.markdown("# 👤")
        st.write(f"**Username**: {username}")
        st.write(f"**Joined**: {user['joined_date']}")
        
        # Only allow editing if viewing own profile
        if username == st.session_state.current_user:
            if st.button("Edit Profile"):
                st.session_state.page = "edit_profile"
                st.experimental_rerun()
    
    with col2:
        st.subheader("Bio")
        st.write(user['bio'] if user['bio'] else "No bio provided")
        
        st.subheader("Posts")
        
        # Find posts by this user
        user_posts = {post_id: post for post_id, post in st.session_state.posts.items() if post['author'] == username}
        
        if user_posts:
            for post_id, post in user_posts.items():
                st.write(f"**{post['title']}** - {post['date']}")
                st.write(f"Category: {post['category']} | Views: {post['views']} | Likes: {len(st.session_state.likes[post_id])}")
                if st.button(f"View Post", key=f"view_post_{post_id}"):
                    st.session_state.current_post = post_id
                    st.session_state.page = "view_post"
                    st.experimental_rerun()
                st.markdown("---")
        else:
            st.write("No posts yet")
    
    if st.button("Back to Forum"):
        st.session_state.page = "home"
        st.experimental_rerun()

def edit_profile_page():
    st.title("Edit Profile")
    
    user = st.session_state.users[st.session_state.current_user]
    
    with st.form("edit_profile_form"):
        name = st.text_input("Display Name", value=user['name'])
        bio = st.text_area("Bio", value=user['bio'] if user['bio'] else "")
        
        # Show current avatar if exists
        if user['avatar']:
            st.write("Current Avatar:")
            avatar_img = display_image(user['avatar'])
            if avatar_img:
                st.image(avatar_img, width=200)
        
        new_avatar = st.file_uploader("Upload New Avatar (optional)", type=["jpg", "jpeg", "png"])
        
        # Password change (optional)
        st.subheader("Change Password (optional)")
        current_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        
        submit_button = st.form_submit_button("Save Changes")
        
        if submit_button:
            # Update basic info
            st.session_state.users[st.session_state.current_user]['name'] = name
            st.session_state.users[st.session_state.current_user]['bio'] = bio
            
            # Update avatar if new one uploaded
            if new_avatar:
                avatar_data = save_uploaded_file(new_avatar)
                st.session_state.users[st.session_state.current_user]['avatar'] = avatar_data
            
            # Change password if provided
            if current_password and new_password and confirm_password:
                if user['password'] != hash_password(current_password):
                    st.error("Current password is incorrect")
                    return
                    
                if new_password != confirm_password:
                    st.error("New passwords do not match")
                    return
                    
                st.session_state.users[st.session_state.current_user]['password'] = hash_password(new_password)
            
            st.success("Profile updated successfully!")
            st.session_state.page = "profile"
            st.experimental_rerun()
    
    if st.button("Cancel"):
        st.session_state.page = "profile"
        st.experimental_rerun()

def home_page():
    st.title("blairs #1 haters")
    
    # Sidebar with categories
    st.sidebar.title("Categories")
    selected_category = st.sidebar.radio("Select Category", ["All"] + st.session_state.categories)
    
    # Sort options
    sort_by = st.sidebar.selectbox("Sort by", ["Newest", "Oldest", "Most Viewed", "Most Liked"])
    
    # Create new post button
    if st.sidebar.button("Create New Post"):
        st.session_state.page = "create_post"
        st.experimental_rerun()
    
    # Filter posts by category
    if selected_category == "All":
        filtered_posts = st.session_state.posts
    else:
        filtered_posts = {post_id: post for post_id, post in st.session_state.posts.items() if post['category'] == selected_category}
    
    # Sort posts
    if sort_by == "Newest":
        sorted_posts = dict(sorted(filtered_posts.items(), key=lambda x: x[1]['date'], reverse=True))
    elif sort_by == "Oldest":
        sorted_posts = dict(sorted(filtered_posts.items(), key=lambda x: x[1]['date']))
    elif sort_by == "Most Viewed":
        sorted_posts = dict(sorted(filtered_posts.items(), key=lambda x: x[1]['views'], reverse=True))
    elif sort_by == "Most Liked":
        sorted_posts = dict(sorted(filtered_posts.items(), key=lambda x: len(st.session_state.likes[x[0]]), reverse=True))
    
    # Display posts
    if sorted_posts:
        for post_id, post in sorted_posts.items():
            col1, col2, col3 = st.columns([1, 5, 1])
            
            with col1:
                if post['author'] in st.session_state.users and st.session_state.users[post['author']]['avatar']:
                    avatar_img = display_image(st.session_state.users[post['author']]['avatar'])
                    if avatar_img:
                        st.image(avatar_img, width=50)
                else:
                    st.markdown("👤")
                st.write(f"**{post['author_name']}**")
            
            with col2:
                st.subheader(post['title'])
                st.write(f"**Category**: {post['category']}")
                st.write(f"**Posted on**: {post['date']}")
                
                # Show truncated content
                content_preview = post['content'][:200] + "..." if len(post['content']) > 200 else post['content']
                st.write(content_preview)
                
                if post['image']:
                    st.image(display_image(post['image']), width=200)
            
            with col3:
                st.write(f"**Views**: {post['views']}")
                st.write(f"**Likes**: {len(st.session_state.likes[post_id])}")
                st.write(f"**Comments**: {len(st.session_state.comments[post_id])}")
                
                if st.button("View Post", key=f"view_{post_id}"):
                    st.session_state.current_post = post_id
                    st.session_state.page = "view_post"
                    st.experimental_rerun()
            
            st.markdown("---")
    else:
        st.write("No posts in this category yet.")

# Help page
def help_page():
    st.title("Forum User Guide")
    
    st.markdown("""
    ## Welcome to blairs's #1 haters!
    
    This guide will help you navigate and make the most of our community platform.
    
    ### Getting Started
    
    1. **Sign Up**: Create your account with a username, password, and profile details.
    2. **Log In**: Access your account using your credentials.
    3. **Browse**: Explore posts from various categories on the home page.
    
    ### Navigation
    
    - **Home**: View all posts sorted by your preferred criteria
    - **Categories**: Filter posts by specific topics using the sidebar
    - **My Profile**: View and edit your profile information
    - **Help**: Access this user guide anytime
    
    ### Creating Content
    
    #### Making Posts
    1. Click the "Create New Post" button in the sidebar
    2. Fill in the title, select a category, and write your content
    3. Optionally add an image
    4. Click "Post" to publish
    
    #### Formatting Options
    
    Our forum supports Markdown formatting:
    - **Bold text**: Surround text with double asterisks `**like this**`
    - *Italic text*: Surround text with single asterisks `*like this*`
    - Headings: Use hashtags `# Heading 1`, `## Heading 2`, etc.
    - Code blocks: Surround code with triple backticks ``` ```
    - Links: URLs are automatically converted to clickable links
    - GIFs: Simply paste a GIF URL and it will be displayed
    
    #### Commenting
    1. Navigate to a post
    2. Scroll to the comment section
    3. Write your comment, optionally add an image
    4. Click "Post Comment"
    
    ### Profile Management
    
    - **View Profile**: See your posts and profile information
    - **Edit Profile**: Update your display name, bio, and avatar
    - **Change Password**: Update your security credentials
    
    ### Interaction
    
    - **Likes**: Show appreciation for posts with the like button
    - **Comments**: Engage in discussions through the comment section
    - **View Count**: See how many users have viewed a post
    
    ### Need Help?
    
    If you have any questions or issues, please contact the forum administrator.
    """)
    
    if st.button("Back to Forum"):
        st.session_state.page = "home"
        st.experimental_rerun()

# Main application
def main():
    # Initialize page if not set
    if 'page' not in st.session_state:
        st.session_state.page = "login" if not st.session_state.logged_in else "home"
    
    # Display user info in sidebar if logged in
    if st.session_state.logged_in:
        st.sidebar.title(f"Welcome, {st.session_state.users[st.session_state.current_user]['name']}!")
        
        # Show user avatar if exists
        if st.session_state.users[st.session_state.current_user]['avatar']:
            avatar_img = display_image(st.session_state.users[st.session_state.current_user]['avatar'])
            if avatar_img:
                st.sidebar.image(avatar_img, width=100)
        
        # Navigation
        st.sidebar.markdown("### Navigation")
        if st.sidebar.button("Home"):
            st.session_state.page = "home"
            st.experimental_rerun()
            
        if st.sidebar.button("My Profile"):
            st.session_state.page = "profile"
            st.experimental_rerun()
        
        if st.sidebar.button("Help & User Guide"):
            st.session_state.page = "help"
            st.experimental_rerun()
            
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.current_user = None
            st.session_state.page = "login"
            st.experimental_rerun()
    
    # Display current page
    if not st.session_state.logged_in:
        if st.session_state.page == "register":
            register_page()
        else:
            # Display welcome message and info on login page
            login_page()
            
            # Add welcome section below login form
            st.markdown("---")
            st.header("Welcome to the Forum!")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                ### Connect with Your Community
                
                this website is a place to HATE ON YOU KNOW WHO
                with others who share your interests. Our forum supports:
                
                - Rich text formatting with Markdown
                - Image and GIF sharing
                - Organized categories for easy navigation
                - User profiles and avatars
                
                Join our growing community today!
                """)
            
            with col2:
                st.markdown("""
                ### Getting Started
                
                1. Register for an account
                2. Create your profile with a custom avatar
                3. Browse posts by category
                4. Engage with other users through comments
                5. Share your own thoughts with new posts
                
                Need help? Our comprehensive user guide is available
                after login.
                """)
            
            # Display signup button prominently
            st.markdown("### Ready to join?")
            if st.button("Create an Account Now", key="welcome_signup", use_container_width=True):
                st.session_state.page = "register"
                st.experimental_rerun()
    else:
        if st.session_state.page == "home":
            home_page()
        elif st.session_state.page == "create_post":
            create_post_page()
        elif st.session_state.page == "view_post":
            view_post_page(st.session_state.current_post)
        elif st.session_state.page == "profile":
            profile_page()
        elif st.session_state.page == "edit_profile":
            edit_profile_page()
        elif st.session_state.page == "help":
            help_page()
        elif st.session_state.page == "user_profile" and 'view_user' in st.session_state:
            profile_page(st.session_state.view_user)

if __name__ == "__main__":
    main()
