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


// Function to fetch all posts from the API and display them.
function loadPosts() {
    // Retrieve the base URL from the input field.
    var baseUrl = document.getElementById('api-base-url').value;

    // Store the URL so that it is available after reloading the page.
    localStorage.setItem('apiBaseUrl', baseUrl);

    // Send a GET request to the /posts endpoint.
    fetch(baseUrl + '/posts')
        .then(response => {
            // response.ok is true for successful HTTP status codes.
            if (!response.ok) {
                throw new Error('The posts could not be loaded.');
            }

            // Convert the JSON response into JavaScript data.
            return response.json();
        })
        .then(data => {
            // Find the container in which the posts are displayed.
            const postContainer = document.getElementById(
                'post-container'
            );

            // Remove posts from a previous request.
            postContainer.innerHTML = '';

            // Create one HTML element for every returned post.
            data.forEach(post => {
                const postDiv = document.createElement('div');
                postDiv.className = 'post';

                // Display all fields returned by the backend.
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
        })
        .catch(error => {
            // Display technical errors in the browser console.
            console.error('Error:', error);
        });
}


// Function to send a POST request and create a new post.
function addPost() {
    // Retrieve the API base URL.
    var baseUrl = document.getElementById('api-base-url').value;

    // Retrieve all values from the post form.
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
        alert('Please fill in title, content, author, and date.');
        return;
    }

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
        .then(response => {
            // Stop the process if the backend returned an error.
            if (!response.ok) {
                throw new Error('The post could not be added.');
            }

            return response.json();
        })
        .then(post => {
            console.log('Post added:', post);

            // Clear the form after the post was created.
            document.getElementById('post-title').value = '';
            document.getElementById('post-content').value = '';
            document.getElementById('post-author').value = '';
            document.getElementById('post-date').value = '';

            // Reload the list so that the new post appears immediately.
            loadPosts();
        })
        .catch(error => {
            console.error('Error:', error);
        });
}


// Function to send a DELETE request and delete a post.
function deletePost(postId) {
    var baseUrl = document.getElementById('api-base-url').value;

    // Send a DELETE request to the endpoint containing the post ID.
    fetch(baseUrl + '/posts/' + postId, {
        method: 'DELETE'
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('The post could not be deleted.');
            }

            console.log('Post deleted:', postId);

            // Reload the posts after deleting one.
            loadPosts();
        })
        .catch(error => {
            console.error('Error:', error);
        });
}