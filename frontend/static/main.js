// Function that runs once the window is fully loaded.
window.onload = function() {
    // Attempt to retrieve the API base URL from local storage.
    var savedBaseUrl = localStorage.getItem('apiBaseUrl');

    // If a base URL is found, insert it and load the posts.
    if (savedBaseUrl) {
        document.getElementById('api-base-url').value = savedBaseUrl;
        loadPosts();
    }

    // Allow the user to start a search by pressing Enter
    // inside the search field.
    var searchInput = document.getElementById('search-query');

    searchInput.addEventListener('keydown', function(event) {
        if (event.key === 'Enter') {
            searchPosts();
        }
    });
};


// Display a visible status message on the page.
function showMessage(message, type) {
    var statusMessage = document.getElementById('status-message');

    // Insert the message as normal text.
    statusMessage.textContent = message;

    // Reset previous success or error classes.
    statusMessage.className = 'status-message';

    // Add a new message type when one was provided.
    if (type) {
        statusMessage.classList.add(type);
    }
}


// Convert an API response into JavaScript data
// and handle unsuccessful HTTP status codes.
function handleJsonResponse(response) {
    return response.json().then(data => {
        // response.ok is false for status codes such as
        // 400, 404, and 500.
        if (!response.ok) {
            // Prefer the error message returned by the backend.
            var errorMessage = data.error || 'The request failed.';

            // The POST endpoint may additionally return a list
            // containing missing required fields.
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

            // Move execution to the following .catch() block.
            throw new Error(errorMessage);
        }

        return data;
    });
}


// Display a provided list of blog posts on the page.
function displayPosts(posts) {
    var postContainer = document.getElementById(
        'post-container'
    );

    // Remove results from the previous request.
    postContainer.innerHTML = '';

    // Show a short notice when the list is empty.
    if (posts.length === 0) {
        postContainer.innerHTML = '<p>No posts found.</p>';
        return;
    }

    // Create one HTML element for every post.
    posts.forEach(post => {
        var postDiv = document.createElement('div');
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
}


// Fetch all posts from the API and display them.
//
// The optional successMessage is used after creating
// or deleting a post.
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

    // Store the URL so that it remains available
    // after reloading the browser page.
    localStorage.setItem('apiBaseUrl', baseUrl);

    showMessage('Loading posts...');

    // Send a GET request to the normal posts endpoint.
    fetch(baseUrl + '/posts')
        .then(handleJsonResponse)
        .then(posts => {
            displayPosts(posts);

            // Show a specific message after adding or deleting.
            if (successMessage) {
                showMessage(successMessage, 'success');
            } else {
                showMessage(
                    posts.length
                    + ' post(s) loaded successfully.',
                    'success'
                );
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showMessage(error.message, 'error');
        });
}


// Search all supported fields using one general search term.
function searchPosts() {
    var baseUrl = document
        .getElementById('api-base-url')
        .value
        .trim();

    var searchQuery = document
        .getElementById('search-query')
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

    // Require a search term before sending the request.
    if (searchQuery === '') {
        showMessage(
            'Please enter a search term.',
            'error'
        );
        return;
    }

    // Store the current API URL in local storage.
    localStorage.setItem('apiBaseUrl', baseUrl);

    showMessage('Searching posts...');

    // encodeURIComponent() safely prepares the entered text
    // for use inside a URL.
    var encodedSearchQuery = encodeURIComponent(searchQuery);

    // Example resulting URL:
    // /api/posts/search?search=daniel
    fetch(
        baseUrl
        + '/posts/search?search='
        + encodedSearchQuery
    )
        .then(handleJsonResponse)
        .then(posts => {
            displayPosts(posts);

            if (posts.length === 0) {
                showMessage(
                    'No posts matched "'
                    + searchQuery
                    + '".'
                );
            } else {
                showMessage(
                    posts.length
                    + ' matching post(s) found.',
                    'success'
                );
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showMessage(error.message, 'error');
        });
}


// Clear the search field and display all posts again.
function clearSearch() {
    document.getElementById('search-query').value = '';

    loadPosts('Search cleared. All posts are displayed.');
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

    // Prevent sending an incomplete post.
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

            // Clear the form after successful creation.
            document.getElementById('post-title').value = '';
            document.getElementById('post-content').value = '';
            document.getElementById('post-author').value = '';
            document.getElementById('post-date').value = '';

            // Reload the list so that the post appears.
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

    // Open the browser's confirmation dialog.
    var deletionConfirmed = confirm(
        'Do you really want to delete this post?'
    );

    // Stop the function when the user cancels.
    if (!deletionConfirmed) {
        showMessage('Deletion cancelled.');
        return;
    }

    showMessage('Deleting post...');

    // Send the DELETE request to the selected post.
    fetch(baseUrl + '/posts/' + postId, {
        method: 'DELETE'
    })
        .then(handleJsonResponse)
        .then(data => {
            console.log(data.message);

            loadPosts('Post deleted successfully.');
        })
        .catch(error => {
            console.error('Error:', error);
            showMessage(error.message, 'error');
        });
}