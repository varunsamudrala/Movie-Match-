import streamlit as st
import pandas as pd
import numpy as np
import os
import hashlib
import plotly.express as px
import re
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import LabelEncoder

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate_user(username, password):
    if not os.path.exists("users.csv"):
        return False
    users_df = pd.read_csv("users.csv")
    hashed_password = hash_password(password)
    return ((users_df['username'] == username) & (users_df['password'] == hashed_password)).any()

def add_user(username, password):
    hashed_password = hash_password(password)
    if os.path.exists("users.csv"):
        users_df = pd.read_csv("users.csv")
        if username in users_df['username'].values:
            return False
    else:
        users_df = pd.DataFrame(columns=["username", "password"])
    
    new_user_df = pd.DataFrame([{ "username": username, "password": hashed_password }])
    users_df = pd.concat([users_df, new_user_df], ignore_index=True)
    users_df.to_csv("users.csv", index=False)
    return True

def is_valid_input(text):
    return bool(re.match("^[a-zA-Z0-9_ ]+$", text))

def log_user_activity(username, genre):
    if not is_valid_input(username) or not is_valid_input(genre):
        print("Invalid character in username or genre.")
        return
    
    with open("user_activity.txt", "a") as file:
        file.write(f"{username},{genre}\n")

def get_user_activity():
    try:
        df_activity = pd.read_csv("user_activity.txt", names=["User", "Genre"], delimiter=",", engine="python")
        return df_activity
    except (FileNotFoundError, pd.errors.ParserError):
        return pd.DataFrame(columns=["User", "Genre"])

def recommend_movies(selected_genre, df):
    return df[df["genre"].str.contains(selected_genre, case=False, na=False)]

def get_collaborative_recommendations(username, df):
    user_activity_df = get_user_activity()
    if user_activity_df.empty:
        return pd.DataFrame()
    
    label_encoder = LabelEncoder()
    user_activity_df['User_Encoded'] = label_encoder.fit_transform(user_activity_df['User'])
    user_activity_df['Genre_Encoded'] = label_encoder.fit_transform(user_activity_df['Genre'])
    
    knn = NearestNeighbors(n_neighbors=3, metric='euclidean')
    knn.fit(user_activity_df[['User_Encoded', 'Genre_Encoded']])
    
    user_index = user_activity_df[user_activity_df['User'] == username].index
    if len(user_index) == 0:
        return pd.DataFrame()
    
    distances, indices = knn.kneighbors(user_activity_df.iloc[user_index][['User_Encoded', 'Genre_Encoded']], n_neighbors=3)
    similar_users = user_activity_df.iloc[indices.flatten()]['User'].unique()
    
    recommended_genres = user_activity_df[user_activity_df['User'].isin(similar_users)]['Genre'].unique()
    recommended_movies = df[df['genre'].isin(recommended_genres)]
    return recommended_movies

df = pd.read_csv("TeluguMovies_dataset_updated.csv")

def main():
    st.title("Movie Match")
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = ""
    
    menu = ["Login", "Sign Up"] if not st.session_state.logged_in else ["Home", "Logout"]
    choice = st.sidebar.selectbox("Menu", menu)
    
    if choice == "Login":
        st.subheader("Login Here")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if authenticate_user(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid username or password")
    
    elif choice == "Sign Up":
        st.subheader("Create New Account")
        new_user = st.text_input("Username")
        new_password = st.text_input("Password", type="password")
        if st.button("Sign Up"):
            if add_user(new_user, new_password):
                st.success("Account created successfully! You can now log in.")
            else:
                st.error("Username already exists!")
    
    elif choice == "Home":
        st.subheader(f"Welcome, {st.session_state.username}")
        genre_list = df["genre"].dropna().unique().tolist()
        selected_genre = st.selectbox("Enter or Select Genre", [""] + genre_list, index=0, key="genre_select")
        
        if st.button("Recommend Movies"):
            log_user_activity(st.session_state.username, selected_genre)
            recommendations = recommend_movies(selected_genre, df)
            st.write(recommendations[["movie", "year", "rating", "overview"]])
        
            collaborative_recommendations = get_collaborative_recommendations(st.session_state.username, df)
            if not collaborative_recommendations.empty:
                st.subheader("Collaborative Filtering Recommendations")
                st.write(collaborative_recommendations[["movie", "year", "rating", "overview"]])
        
        user_activity_df = get_user_activity()
        if user_activity_df.empty:
            random_data = pd.DataFrame({
                "Genre": ["Action", "Comedy", "Drama", "Thriller"],
                "Count": np.random.randint(5, 20, 4)
            })
            fig = px.bar(random_data, x="Genre", y="Count", title="Random User Activity Data")
        else:
            fig = px.histogram(user_activity_df, x="Genre", title="User Activity: Genre Preferences")
        st.plotly_chart(fig, use_container_width=True)
    
    elif choice == "Logout":
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

if __name__ == "__main__":
    main()
