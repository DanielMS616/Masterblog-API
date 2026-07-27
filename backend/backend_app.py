from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

POSTS = [
    {"id": 1, "title": "First post", "content": "This is the first post."},
    {"id": 2, "title": "Second post", "content": "This is the second post."},
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


@app.route('/api/posts', methods=['GET'])
def get_posts():
    return jsonify(POSTS)


@app.route("/api/posts", methods=["POST"])
def add_post():
    """Create a new blog post and add it to the post list."""

    # Read the JSON object from the body of the request.
    new_post_data = request.get_json(silent=True)

    # Check whether a JSON object was sent at all.
    if new_post_data is None:
        return jsonify({
            "error": "Request body must contain JSON data."
        }), 400

    # Create a list in which missing field names are collected.
    missing_fields = []

    # Check whether the required title field exists.
    if "title" not in new_post_data:
        missing_fields.append("title")

    # Check whether the required content field exists.
    if "content" not in new_post_data:
        missing_fields.append("content")

    # If one or more fields are missing, return a helpful error message.
    if missing_fields:
        return jsonify({
            "error": "Missing required fields.",
            "missing_fields": missing_fields
        }), 400

    # Create the complete blog post with an automatically generated ID.
    new_post = {
        "id": get_next_id(),
        "title": new_post_data["title"],
        "content": new_post_data["content"]
    }

    # Add the new post to the in-memory list.
    POSTS.append(new_post)

    # Return the newly created post and the HTTP status code 201 Created.
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
