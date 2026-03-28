from flask import Flask, jsonify, render_template, request
import pandas as pd
import random
from flask_cors import CORS
import ast

app = Flask(__name__)
CORS(app)

# Load and preprocess datasets
movies_df = pd.read_csv("tmdb_5000_movies.csv")
credits_df = pd.read_csv("tmdb_5000_credits.csv")

# Merge datasets
movies_df = movies_df.merge(credits_df, on="title")

# Convert genres column from string to list
movies_df["genres"] = movies_df["genres"].apply(lambda x: [i["name"] for i in ast.literal_eval(x)])

# Fallback image if not available
def get_placeholder_image():
    return "https://via.placeholder.com/500x750?text=No+Image"

# Generate movie card format
def movie_to_dict(movie_row):
    return {
        "title": movie_row["title"],
        "rating": round(movie_row["popularity"], 1),
        "image": get_placeholder_image(),
        "genres": movie_row["genres"],
        "overview": movie_row["overview"],
        "runtime": movie_row["runtime"]
    }

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/trending")
def trending():
    trending_sample = movies_df.sample(8)
    return jsonify([movie_to_dict(row) for _, row in trending_sample.iterrows()])

@app.route("/api/search")
def search_movies():
    query = request.args.get("q", "").lower()
    if not query:
        return jsonify({"results": [], "recommendations": []})

    search_results = movies_df[movies_df["title"].str.lower().str.contains(query)]

    if search_results.empty:
        return jsonify({"results": [], "recommendations": []})

    # First match genre-based recommendations
    top_movie = search_results.iloc[0]
    target_genres = top_movie["genres"]

    # Filter other movies with similar genres
    recommended = movies_df[
        movies_df["title"] != top_movie["title"]
    ].copy()
    recommended = recommended[recommended["genres"].apply(lambda g: any(genre in g for genre in target_genres))]
    recommended_sample = recommended.sample(min(8, len(recommended)))

    return jsonify({
        "results": [movie_to_dict(row) for _, row in search_results.head(8).iterrows()],
        "recommendations": [movie_to_dict(row) for _, row in recommended_sample.iterrows()]
    })

@app.route("/api/recommendations")
def default_recommendations():
    sample = movies_df.sample(8)
    return jsonify([movie_to_dict(row) for _, row in sample.iterrows()])

if __name__ == "__main__":
    app.run(debug=True)
