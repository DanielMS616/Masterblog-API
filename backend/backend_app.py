from datetime import datetime

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

# The Swagger user interface will be available under this URL.
SWAGGER_URL = "/api/docs"

# Flask serves files from the backend/static directory under /static.
# This URL points to our Swagger definition file.
API_URL = "/static/masterblog.json"


# Create the Swagger UI blueprint.
# A blueprint adds a group of routes to an existing Flask application.
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


# For now, the blog posts are stored in a Python list.
# Each post is represented by a dictionary.
#
# In addition to the ID, title, and content, every post now also
# contains an author and a publication date.
#
# The date is stored as a string in the format YYYY-MM-DD.
POSTS = [
    {
        "id": 1,
        "title": "First post",
        "content": "This is the first post.",
        "author": "Daniel",
        "date": "2026-07-20"
    },
    {
        "id": 2,
        "title": "Second post",
        "content": "This is the second post.",
        "author": "Josi",
        "date": "2026-07-25"
    }
]


def get_next_id():
    """Return the next available integer ID for a new blog post."""

    # If the list is empty, the first post receives the ID 1.
    if not POSTS:
        return 1

    # Extract all existing IDs from the list of posts.
    existing_ids = [post["id"] for post in POSTS]

    # The next ID is one number higher than the current highest ID.
    return max(existing_ids) + 1


def is_valid_date(date_string):
    """Check whether a value is a valid date in YYYY-MM-DD format."""

    try:
        # Convert the string into a Python date and verify its format.
        #
        # %Y = four-digit year
        # %m = two-digit month
        # %d = two-digit day
        datetime.strptime(date_string, "%Y-%m-%d")

        # If no error occurred, the date is valid.
        return True

    except (TypeError, ValueError):
        # TypeError occurs when the value is not a string.
        # ValueError occurs when the format or date is invalid.
        return False


@app.route("/api/posts", methods=["GET"])
def get_posts():
    """Return all blog posts, optionally sorted by title or content."""

    # Read the optional sorting parameters from the URL.
    sort_field = request.args.get("sort")
    sort_direction = request.args.get("direction")

    # If neither parameter was provided, return the posts in their
    # original order, just as the endpoint did before.
    if sort_field is None and sort_direction is None:
        return jsonify(POSTS), 200

    # A direction has no meaning without a field to sort by.
    if sort_field is None:
        return jsonify({
            "error": (
                "The 'sort' parameter is required when "
                "'direction' is provided."
            )
        }), 400

    # Only title and content are allowed as sorting fields.
    if sort_field not in ["title", "content"]:
        return jsonify({
            "error": (
                "Invalid sort field. "
                "Allowed values are 'title' and 'content'."
            )
        }), 400

    # If a sort field was provided without a direction,
    # use ascending order as a useful default.
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

    # reverse=False means ascending order.
    # reverse=True means descending order.
    sort_descending = sort_direction == "desc"

    # sorted() creates a new list and does not change the original POSTS
    # list. lower() makes the alphabetical sorting case-insensitive.
    sorted_posts = sorted(
        POSTS,
        key=lambda post: post[sort_field].lower(),
        reverse=sort_descending
    )

    return jsonify(sorted_posts), 200


@app.route("/api/posts/search", methods=["GET"])
def search_posts():
    """Return posts that match the provided search terms."""

    # Read the optional search terms from the URL.
    # An empty string is used when a parameter was not provided.
    title_query = request.args.get("title", "")
    content_query = request.args.get("content", "")

    # Remove unnecessary spaces and make the search case-insensitive.
    title_query = title_query.strip().lower()
    content_query = content_query.strip().lower()

    # Store all matching posts in this list.
    matching_posts = []

    # Check every existing blog post.
    for post in POSTS:
        # A title matches when a title search term was provided
        # and that term occurs inside the post title.
        title_matches = (
            title_query != ""
            and title_query in post["title"].lower()
        )

        # The same check is performed for the post content.
        content_matches = (
            content_query != ""
            and content_query in post["content"].lower()
        )

        # The assignment asks for matches in the title OR the content.
        if title_matches or content_matches:
            matching_posts.append(post)

    # An empty list is returned when no matching posts were found.
    return jsonify(matching_posts), 200


@app.route("/api/posts", methods=["POST"])
def add_post():
    """Create a new blog post and add it to the post list."""

    # Read the JSON data from the request body.
    #
    # silent=True prevents Flask from returning its own 415 error
    # when no JSON body or no JSON content type was provided.
    new_post_data = request.get_json(silent=True)

    # A valid JSON object is required.
    if new_post_data is None:
        return jsonify({
            "error": "Request body must contain JSON data."
        }), 400

    # All four fields are required when a new post is created.
    required_fields = [
        "title",
        "content",
        "author",
        "date"
    ]

    # Store the names of all fields that were not provided.
    missing_fields = []

    # Check every required field.
    for field in required_fields:
        if field not in new_post_data:
            missing_fields.append(field)

    # Return one helpful response containing all missing fields.
    if missing_fields:
        return jsonify({
            "error": "Missing required fields.",
            "missing_fields": missing_fields
        }), 400

    # The date must be a real date in the format YYYY-MM-DD.
    if not is_valid_date(new_post_data["date"]):
        return jsonify({
            "error": (
                "The 'date' field must contain a valid date "
                "in YYYY-MM-DD format."
            )
        }), 400

    # Create the complete blog post.
    #
    # The ID is generated by the backend. The client only sends
    # title, content, author, and date.
    new_post = {
        "id": get_next_id(),
        "title": new_post_data["title"],
        "content": new_post_data["content"],
        "author": new_post_data["author"],
        "date": new_post_data["date"]
    }

    # Add the new post to the in-memory list.
    POSTS.append(new_post)

    # HTTP 201 means that a new resource was created successfully.
    return jsonify(new_post), 201


@app.route("/api/posts/<int:post_id>", methods=["DELETE"])
def delete_post(post_id):
    """Delete the blog post with the given ID."""

    # Go through all posts to find the post with the requested ID.
    for post in POSTS:
        if post["id"] == post_id:
            # Remove the complete post dictionary from the list.
            POSTS.remove(post)

            # Return a success message with HTTP status code 200.
            return jsonify({
                "message": (
                    f"Post with id {post_id} "
                    "has been deleted successfully."
                )
            }), 200

    # This part is only reached when no matching post was found.
    return jsonify({
        "error": f"Post with id {post_id} was not found."
    }), 404


@app.route("/api/posts/<int:post_id>", methods=["PUT"])
def update_post(post_id):
    """Update the blog post with the given ID."""

    # Search through all posts for the requested ID.
    for post in POSTS:
        if post["id"] == post_id:
            # Read the JSON object from the request body.
            # If no valid JSON was sent, use an empty dictionary.
            update_data = request.get_json(silent=True) or {}

            # The dictionary method get() returns the new title if it
            # exists in the JSON data. Otherwise, it returns the old title.
            post["title"] = update_data.get(
                "title",
                post["title"]
            )

            # The same logic is used for the content.
            post["content"] = update_data.get(
                "content",
                post["content"]
            )

            # Return the complete updated post.
            return jsonify(post), 200

    # This part is reached only when no post has the requested ID.
    return jsonify({
        "error": f"Post with id {post_id} was not found."
    }), 404


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)
