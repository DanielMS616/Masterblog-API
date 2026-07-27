// Function that runs once the window is fully loaded.
window.onload = function() {
    // Attempt to retrieve the API base URL from local storage.
    var savedBaseUrl = localStorage.getItem('apiBaseUrl');

    // If a base URL is found, insert it and load the posts.
    if (savedBaseUrl) {
        document.getElementById('api-base-url').value = savedBaseUrl;
        loadPosts();
    }
};


// Display a visible status message on the page.
function showMessage(message, type) {
    var statusMessage = document.getElementById('status-message');

    // Insert the message as text.
    statusMessage.textContent = message;

    // Reset the class before applying a new message type.
    statusMessage.className = 'status-message';

    // Add either the success or error class when provided.
    if (type) {
        statusMessage.classList.add(type);
    }
}


// Convert an API response into JavaScript data and handle errors.
function handleJsonResponse(response) {
    return response.json().then(data => {
        // response.ok is false for status codes such as
        // 400, 404, and 500.
        if (!response.ok) {
            // Use the error message returned by the backend.
            var errorMessage = data.error || 'The request failed.';

            // The POST endpoint may additionally return a list
            // containing all missing required fields.
            if (
                data.missing_fields
                && data.missing_fields.length > 0
            ) {
                errorMessage += (
                    ' Missing fields: '
                    + data.missing_fields.join(', ')
                    + '.'
                );
            }

            // Throwing an error moves execution to .catch().
            throw new Error(errorMessage);
        }

        return data;
    });
}


// Fetch all posts from the API and display them.
//
// The optional successMessage is useful after adding or deleting
// a post. Otherwise, a general loading message is shown.
function loadPosts(successMessage) {
    var baseUrl = document
        .getElementById('api-base-url')
        .value
        .trim();

    // Prevent a request without an API URL.
    if (baseUrl === '') {
        showMessage(
            'Please enter the API base URL.',
            'error'
        );
        return;
    }

    // Store the URL so that it is available after reloading.
    localStorage.setItem('apiBaseUrl', baseUrl);

    showMessage('Loading posts...');

    // Send a GET request to the /posts endpoint.
    fetch(baseUrl + '/posts')
        .then(handleJsonResponse)
        .then(data => {
            const postContainer = document.getElementById(
                'post-container'
            );

            // Remove posts from a previous request.
            postContainer.innerHTML = '';

            // Show a message when the API contains no posts.
            if (data.length === 0) {
                postContainer.innerHTML = '<p>No posts found.</p>';
            }

            // Create one HTML element for every returned post.
            data.forEach(post => {
                const postDiv = document.createElement('div');
                postDiv.className = 'post';

                postDiv.innerHTML = `
                    <h2>${post.title}</h2>
                    <p class="post-meta">
                        By ${post.author} · ${post.date}
                    </p>
                    <p>${post.content}</p>
                    <button onclick="deletePost(${post.id})">
                        Delete
                    </button>
                `;

                postContainer.appendChild(postDiv);
            });

            // Use a specific message after adding or deleting.
            if (successMessage) {
                showMessage(successMessage, 'success');
            } else {
                showMessage(
                    data.length + ' post(s) loaded successfully.',
                    'success'
                );
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showMessage(error.message, 'error');
        });
}


// Send a POST request and create a new post.
function addPost() {
    var baseUrl = document
        .getElementById('api-base-url')
        .value
        .trim();

    var postTitle = document
        .getElementById('post-title')
        .value
        .trim();

    var postContent = document
        .getElementById('post-content')
        .value
        .trim();

    var postAuthor = document
        .getElementById('post-author')
        .value
        .trim();

    var postDate = document
        .getElementById('post-date')
        .value;

    // Prevent sending an incomplete post to the backend.
    if (
        postTitle === ''
        || postContent === ''
        || postAuthor === ''
        || postDate === ''
    ) {
        showMessage(
            'Please fill in title, content, author, and date.',
            'error'
        );
        return;
    }

    showMessage('Adding post...');

    // Send all four required fields to the backend.
    fetch(baseUrl + '/posts', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            title: postTitle,
            content: postContent,
            author: postAuthor,
            date: postDate
        })
    })
        .then(handleJsonResponse)
        .then(post => {
            console.log('Post added:', post);

            // Clear the form after the post was created.
            document.getElementById('post-title').value = '';
            document.getElementById('post-content').value = '';
            document.getElementById('post-author').value = '';
            document.getElementById('post-date').value = '';

            // Reload the list and show a specific success message.
            loadPosts('Post added successfully.');
        })
        .catch(error => {
            console.error('Error:', error);
            showMessage(error.message, 'error');
        });
}


// Ask for confirmation and delete the selected post.
function deletePost(postId) {
    var baseUrl = document
        .getElementById('api-base-url')
        .value
        .trim();

    // Open a browser confirmation dialog.
    //
    // confirm() returns:
    // true  -> the user clicked "OK"
    // false -> the user clicked "Cancel"
    var deletionConfirmed = confirm(
        'Do you really want to delete this post?'
    );

    // Stop the function when the user cancels the deletion.
    if (!deletionConfirmed) {
        showMessage('Deletion cancelled.');
        return;
    }

    showMessage('Deleting post...');

    // Send a DELETE request to the endpoint containing the post ID.
    fetch(baseUrl + '/posts/' + postId, {
        method: 'DELETE'
    })
        .then(handleJsonResponse)
        .then(data => {
            console.log(data.message);

            // Reload the posts and display a success message.
            loadPosts('Post deleted successfully.');
        })
        .catch(error => {
            console.error('Error:', error);
            showMessage(error.message, 'error');
        });
}