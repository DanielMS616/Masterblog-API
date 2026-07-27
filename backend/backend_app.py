import json
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint


app = Flask(__name__)

# Enable Cross-Origin Resource Sharing for all routes.
# This allows the separately running frontend to access the API.
CORS(app)


# The Swagger user interface is available under this URL.
SWAGGER_URL = "/api/docs"

# Flask serves files from backend/static under the /static URL.
API_URL = "/static/masterblog.json"


# Create the Swagger UI blueprint.
swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        "app_name": "Masterblog API"
    }
)


# Register the Swagger routes in the Flask application.
app.register_blueprint(
    swagger_ui_blueprint,
    url_prefix=SWAGGER_URL
)


# __file__ represents the path of this Python file.
# .parent points to the backend directory.
#
# This guarantees that posts.json is found in the backend folder,
# even when the application is started from the project root.
POSTS_FILE = Path(__file__).parent / "posts.json"


def load_posts():
    """Load all blog posts from the JSON file."""

    try:
        # Open the JSON file for reading.
        with POSTS_FILE.open("r", encoding="utf-8") as file:
            posts = json.load(file)

        # The JSON file must contain a list of post dictionaries.
        if not isinstance(posts, list):
            return None, "The posts file must contain a JSON list."

        # No error occurred.
        return posts, None

    except FileNotFoundError:
        # If the file does not exist yet, the API starts with
        # an empty list of posts.
        return [], None

    except json.JSONDecodeError:
        # This error occurs when the file contains invalid JSON.
        return None, "The posts file contains invalid JSON."

    except OSError:
        # This covers other file-reading errors, for example
        # missing permissions.
        return None, "The posts file could not be read."


def save_posts(posts):
    """Save all blog posts to the JSON file."""

    try:
        # Open the file in write mode.
        #
        # Write mode replaces the previous file content with the
        # complete updated list.
        with POSTS_FILE.open("w", encoding="utf-8") as file:
            json.dump(
                posts,
                file,
                indent=4,
                ensure_ascii=False
            )

        # None means that no error occurred.
        return None

    except OSError:
        # Return an error message if writing the file failed.
        return "The posts file could not be saved."


def get_next_id(posts):
    """Return the next available integer ID."""

    # If there are no posts yet, start with ID 1.
    if not posts:
        return 1

    # Extract all existing IDs from the loaded post list.
    existing_ids = [post["id"] for post in posts]

    # The new ID is one number higher than the current highest ID.
    return max(existing_ids) + 1


def is_valid_date(date_string):
    """Check whether a value is a valid date in YYYY-MM-DD format."""

    try:
        # Convert the string into a Python datetime object.
        #
        # %Y = four-digit year
        # %m = two-digit month
        # %d = two-digit day
        datetime.strptime(date_string, "%Y-%m-%d")

        return True

    except (TypeError, ValueError):
        # TypeError occurs if the value is not a string.
        # ValueError occurs if the format or date is invalid.
        return False


@app.route("/api/posts", methods=["GET"])
def get_posts():
    """Return all posts, optionally sorted by title or content."""

    # Load the current posts from the JSON file.
    posts, load_error = load_posts()

    # Return a server error if the file could not be read correctly.
    if load_error:
        return jsonify({
            "error": load_error
        }), 500

    # Read the optional sorting parameters from the URL.
    sort_field = request.args.get("sort")
    sort_direction = request.args.get("direction")

    # Without sorting parameters, preserve the stored order.
    if sort_field is None and sort_direction is None:
        return jsonify(posts), 200

    # A direction cannot be used without a sorting field.
    if sort_field is None:
        return jsonify({
            "error": (
                "The 'sort' parameter is required when "
                "'direction' is provided."
            )
        }), 400

    # Only the fields required by the current assignment are allowed.
    if sort_field not in ["title", "content"]:
        return jsonify({
            "error": (
                "Invalid sort field. "
                "Allowed values are 'title' and 'content'."
            )
        }), 400

    # Use ascending order if no direction was provided.
    if sort_direction is None:
        sort_direction = "asc"

    # Validate the requested direction.
    if sort_direction not in ["asc", "desc"]:
        return jsonify({
            "error": (
                "Invalid sort direction. "
                "Allowed values are 'asc' and 'desc'."
            )
        }), 400

    # True means descending and False means ascending.
    sort_descending = sort_direction == "desc"

    # sorted() creates a new list and leaves the stored order unchanged.
    sorted_posts = sorted(
        posts,
        key=lambda post: post[sort_field].lower(),
        reverse=sort_descending
    )

    return jsonify(sorted_posts), 200


@app.route("/api/posts/search", methods=["GET"])
def search_posts():
    """Return posts that match the provided search terms."""

    # Load the current posts from the JSON file.
    posts, load_error = load_posts()

    if load_error:
        return jsonify({
            "error": load_error
        }), 500

    # Read the optional search terms from the URL.
    title_query = request.args.get("title", "")
    content_query = request.args.get("content", "")

    # Make the search case-insensitive and remove outer spaces.
    title_query = title_query.strip().lower()
    content_query = content_query.strip().lower()

    matching_posts = []

    # Check every post loaded from the JSON file.
    for post in posts:
        title_matches = (
            title_query != ""
            and title_query in post["title"].lower()
        )

        content_matches = (
            content_query != ""
            and content_query in post["content"].lower()
        )

        if title_matches or content_matches:
            matching_posts.append(post)

    return jsonify(matching_posts), 200


@app.route("/api/posts", methods=["POST"])
def add_post():
    """Create a new blog post and save it in the JSON file."""

    # Read the JSON data from the request body.
    new_post_data = request.get_json(silent=True)

    if new_post_data is None:
        return jsonify({
            "error": "Request body must contain JSON data."
        }), 400

    # All four fields are required for a new post.
    required_fields = [
        "title",
        "content",
        "author",
        "date"
    ]

    missing_fields = []

    # Collect the names of all missing fields.
    for field in required_fields:
        if field not in new_post_data:
            missing_fields.append(field)

    if missing_fields:
        return jsonify({
            "error": "Missing required fields.",
            "missing_fields": missing_fields
        }), 400

    # Validate the provided publication date.
    if not is_valid_date(new_post_data["date"]):
        return jsonify({
            "error": (
                "The 'date' field must contain a valid date "
                "in YYYY-MM-DD format."
            )
        }), 400

    # Load the existing posts before adding the new one.
    posts, load_error = load_posts()

    if load_error:
        return jsonify({
            "error": load_error
        }), 500

    # Create the complete new post.
    new_post = {
        "id": get_next_id(posts),
        "title": new_post_data["title"],
        "content": new_post_data["content"],
        "author": new_post_data["author"],
        "date": new_post_data["date"]
    }

    # Add the new post to the loaded list.
    posts.append(new_post)

    # Save the complete updated list.
    save_error = save_posts(posts)

    if save_error:
        return jsonify({
            "error": save_error
        }), 500

    return jsonify(new_post), 201


@app.route("/api/posts/<int:post_id>", methods=["DELETE"])
def delete_post(post_id):
    """Delete a post and save the changed list."""

    # Load the current posts from the JSON file.
    posts, load_error = load_posts()

    if load_error:
        return jsonify({
            "error": load_error
        }), 500

    # Search for the requested post.
    for post in posts:
        if post["id"] == post_id:
            # Remove the matching post from the loaded list.
            posts.remove(post)

            # Save the changed list to the JSON file.
            save_error = save_posts(posts)

            if save_error:
                return jsonify({
                    "error": save_error
                }), 500

            return jsonify({
                "message": (
                    f"Post with id {post_id} "
                    "has been deleted successfully."
                )
            }), 200

    return jsonify({
        "error": f"Post with id {post_id} was not found."
    }), 404


@app.route("/api/posts/<int:post_id>", methods=["PUT"])
def update_post(post_id):
    """Update a post and save the changed data."""

    # Load the latest posts from the JSON file.
    posts, load_error = load_posts()

    # Stop the request if the file could not be loaded.
    if load_error:
        return jsonify({
            "error": load_error
        }), 500

    # Search for the post with the requested ID.
    for post in posts:
        if post["id"] == post_id:
            # Read the optional values from the request body.
            #
            # An empty dictionary means that no fields will be changed.
            update_data = request.get_json(silent=True) or {}

            # Validate the date before changing the post.
            #
            # The date is optional for an update. It is checked only
            # when the client actually provides a new date.
            if (
                "date" in update_data
                and not is_valid_date(update_data["date"])
            ):
                return jsonify({
                    "error": (
                        "The 'date' field must contain a valid date "
                        "in YYYY-MM-DD format."
                    )
                }), 400

            # Keep the current value when a field was not provided.
            post["title"] = update_data.get(
                "title",
                post["title"]
            )

            post["content"] = update_data.get(
                "content",
                post["content"]
            )

            post["author"] = update_data.get(
                "author",
                post["author"]
            )

            post["date"] = update_data.get(
                "date",
                post["date"]
            )

            # Save the complete changed list in posts.json.
            save_error = save_posts(posts)

            # Return HTTP 500 if writing the file failed.
            if save_error:
                return jsonify({
                    "error": save_error
                }), 500

            # Return the complete updated post.
            return jsonify(post), 200

    # This point is reached only when the ID does not exist.
    return jsonify({
        "error": f"Post with id {post_id} was not found."
    }), 404


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5002,
        debug=True
    )