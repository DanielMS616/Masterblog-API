import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

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

# A post is represented by a dictionary containing its fields.
Post = dict[str, Any]


def is_valid_date(date_string: Any) -> bool:
    """Check whether a value is a valid date in YYYY-MM-DD format."""

    if not isinstance(date_string, str):
        return False

    try:
        # Convert the string into a Python datetime object.
        #
        # %Y = four-digit year
        # %m = two-digit month
        # %d = two-digit day
        parsed_date = datetime.strptime(date_string, "%Y-%m-%d")

        # strptime() may accept values without leading zeroes on some
        # systems. Comparing the formatted date enforces the exact format.
        return parsed_date.strftime("%Y-%m-%d") == date_string

    except ValueError:
        # ValueError occurs if the format or date is invalid.
        return False


def is_valid_stored_post(post: Any) -> bool:
    """Check whether a value has the expected stored post structure."""

    if not isinstance(post, dict):
        return False

    post_id = post.get("id")

    # bool is a subclass of int in Python, so reject it explicitly.
    if not isinstance(post_id, int) or isinstance(post_id, bool):
        return False

    for field in ["title", "content", "author"]:
        value = post.get(field)

        if not isinstance(value, str) or value.strip() == "":
            return False

    return is_valid_date(post.get("date"))


def load_posts() -> tuple[list[Post], Optional[str]]:
    """Load all blog posts from the JSON file."""

    try:
        # Open the JSON file for reading.
        with POSTS_FILE.open("r", encoding="utf-8") as file:
            loaded_data = json.load(file)

        # The JSON file must contain a list.
        if not isinstance(loaded_data, list):
            return [], "The posts file must contain a JSON list."

        # Every list item must have the expected post structure.
        if not all(is_valid_stored_post(post) for post in loaded_data):
            return [], "The posts file contains invalid post data."

        # The structure was checked above, so the list can now be used
        # as a list of post dictionaries.
        posts: list[Post] = loaded_data

        return posts, None

    except FileNotFoundError:
        # If the file does not exist yet, the API starts with
        # an empty list of posts.
        return [], None

    except json.JSONDecodeError:
        # This error occurs when the file contains invalid JSON.
        return [], "The posts file contains invalid JSON."

    except OSError:
        # This covers other file-reading errors, for example
        # missing permissions.
        return [], "The posts file could not be read."


def save_posts(posts: list[Post]) -> Optional[str]:
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


def get_next_id(posts: list[Post]) -> int:
    """Return the next available integer ID."""

    # If there are no posts yet, start with ID 1.
    if not posts:
        return 1

    # Extract all existing IDs from the loaded post list.
    existing_ids = [post["id"] for post in posts]

    # The new ID is one number higher than the current highest ID.
    return max(existing_ids) + 1


def get_invalid_text_fields(
    data: Post,
    fields: list[str]
) -> list[str]:
    """Return supplied fields that do not contain non-empty text."""

    invalid_fields = []

    for field in fields:
        if field not in data:
            continue

        value = data[field]

        if not isinstance(value, str) or value.strip() == "":
            invalid_fields.append(field)

    return invalid_fields


@app.route("/api/posts", methods=["GET"])
def get_posts():
    """Return all posts, optionally sorted by a supported field."""

    # Load the latest blog posts from the JSON file.
    posts, load_error = load_posts()

    # Stop the request if the file could not be loaded.
    if load_error:
        return jsonify({
            "error": load_error
        }), 500

    # Read the optional sorting parameters from the URL.
    #
    # Example:
    # /api/posts?sort=author&direction=asc
    sort_field = request.args.get("sort")
    sort_direction = request.args.get("direction")

    # If no sorting parameters were provided, return the posts
    # in the same order in which they are stored in posts.json.
    if sort_field is None and sort_direction is None:
        return jsonify(posts), 200

    # A sorting direction cannot be used without a sorting field.
    if sort_field is None:
        return jsonify({
            "error": (
                "The 'sort' parameter is required when "
                "'direction' is provided."
            )
        }), 400

    # These are the fields that may be used for sorting.
    allowed_sort_fields = [
        "title",
        "content",
        "author",
        "date"
    ]

    # Return an error when the requested field is not supported.
    if sort_field not in allowed_sort_fields:
        return jsonify({
            "error": (
                "Invalid sort field. Allowed values are "
                "'title', 'content', 'author', and 'date'."
            )
        }), 400

    # If the client provides a sort field but no direction,
    # ascending order is used as the default.
    if sort_direction is None:
        sort_direction = "asc"

    # Only ascending and descending order are supported.
    if sort_direction not in ["asc", "desc"]:
        return jsonify({
            "error": (
                "Invalid sort direction. "
                "Allowed values are 'asc' and 'desc'."
            )
        }), 400

    # sorted() expects reverse=True for descending order
    # and reverse=False for ascending order.
    sort_descending = sort_direction == "desc"

    # Dates must be converted into real datetime objects.
    # Text fields are sorted case-insensitively.
    if sort_field == "date":
        sorted_posts = sorted(
            posts,
            key=lambda post: datetime.strptime(
                post["date"],
                "%Y-%m-%d"
            ),
            reverse=sort_descending
        )
    else:
        sorted_posts = sorted(
            posts,
            key=lambda post: post[sort_field].lower(),
            reverse=sort_descending
        )

    # Return the sorted copy. The stored order remains unchanged.
    return jsonify(sorted_posts), 200


@app.route("/api/posts/search", methods=["GET"])
def search_posts():
    """Return posts that contain the provided search term."""

    # Load the latest blog posts from the JSON file.
    posts, load_error = load_posts()

    # Stop the request if the file could not be loaded.
    if load_error:
        return jsonify({
            "error": load_error
        }), 500

    # Read the general search term from the URL.
    #
    # Example:
    # /api/posts/search?search=daniel
    search_query = request.args.get("search", "").strip().lower()

    # Without a search term, return an empty result list.
    if search_query == "":
        return jsonify([]), 200

    matching_posts = []

    # Search title, content, author, and date.
    for post in posts:
        searchable_values = [
            post["title"],
            post["content"],
            post["author"],
            post["date"]
        ]

        if any(
            search_query in value.lower()
            for value in searchable_values
        ):
            matching_posts.append(post)

    return jsonify(matching_posts), 200


@app.route("/api/posts", methods=["POST"])
def add_post():
    """Create a new blog post and save it in the JSON file."""

    request_data = request.get_json(silent=True)

    # The request body must contain a JSON object.
    if not isinstance(request_data, dict):
        return jsonify({
            "error": "Request body must contain a JSON object."
        }), 400

    new_post_data: Post = request_data

    # All four fields are required for a new post.
    required_fields = [
        "title",
        "content",
        "author",
        "date"
    ]

    missing_fields = [
        field
        for field in required_fields
        if field not in new_post_data
    ]

    if missing_fields:
        return jsonify({
            "error": "Missing required fields.",
            "missing_fields": missing_fields
        }), 400

    invalid_text_fields = get_invalid_text_fields(
        new_post_data,
        ["title", "content", "author"]
    )

    if invalid_text_fields:
        return jsonify({
            "error": (
                "The following fields must contain non-empty text: "
                + ", ".join(invalid_text_fields)
                + "."
            )
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

    # Create the complete new post. Outer spaces are removed
    # from the text fields before they are stored.
    new_post = {
        "id": get_next_id(posts),
        "title": new_post_data["title"].strip(),
        "content": new_post_data["content"].strip(),
        "author": new_post_data["author"].strip(),
        "date": new_post_data["date"]
    }

    posts.append(new_post)

    save_error = save_posts(posts)

    if save_error:
        return jsonify({
            "error": save_error
        }), 500

    return jsonify(new_post), 201


@app.route("/api/posts/<int:post_id>", methods=["DELETE"])
def delete_post(post_id):
    """Delete a post and save the changed list."""

    posts, load_error = load_posts()

    if load_error:
        return jsonify({
            "error": load_error
        }), 500

    for post in posts:
        if post["id"] == post_id:
            posts.remove(post)

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

    posts, load_error = load_posts()

    if load_error:
        return jsonify({
            "error": load_error
        }), 500

    for post in posts:
        if post["id"] != post_id:
            continue

        request_data = request.get_json(silent=True)

        # No JSON body means that no fields are changed.
        if request_data is None:
            update_data: Post = {}

        # Other JSON structures, such as lists and strings,
        # cannot be used as an update object.
        elif not isinstance(request_data, dict):
            return jsonify({
                "error": "Request body must contain a JSON object."
            }), 400

        else:
            update_data = request_data

        invalid_text_fields = get_invalid_text_fields(
            update_data,
            ["title", "content", "author"]
        )

        if invalid_text_fields:
            return jsonify({
                "error": (
                    "The following fields must contain non-empty text: "
                    + ", ".join(invalid_text_fields)
                    + "."
                )
            }), 400

        # The date is optional for an update and is checked only
        # when the client provides a new value.
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
        for field in ["title", "content", "author"]:
            if field in update_data:
                post[field] = update_data[field].strip()

        if "date" in update_data:
            post["date"] = update_data["date"]

        save_error = save_posts(posts)

        if save_error:
            return jsonify({
                "error": save_error
            }), 500

        return jsonify(post), 200

    return jsonify({
        "error": f"Post with id {post_id} was not found."
    }), 404


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5002,
        debug=True
    )
