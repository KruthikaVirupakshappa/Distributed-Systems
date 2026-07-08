// Base API URL
const API_URL = '/api/users';

// Load users when page loads
document.addEventListener('DOMContentLoaded', () => {
    loadUsers();
});

// Fetch and display all users
async function loadUsers() {
    try {
        const response = await fetch(API_URL);
        if (!response.ok) {
            throw new Error('Failed to fetch users');
        }

        const users = await response.json();
        displayUsers(users);
    } catch (error) {
        console.error('Error loading users:', error);
        alert('Failed to load users');
    }
}

// Display users in the table
function displayUsers(users) {
    const tbody = document.getElementById('userTableBody');
    tbody.innerHTML = '';

    users.forEach(user => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${user.id}</td>
            <td>${user.name}</td>
        `;
        tbody.appendChild(row);
    });
}

// Create a new user
async function createUser() {
    const nameInput = document.getElementById('createName');
    const name = nameInput.value.trim();

    if (!name) {
        alert('Please enter a user name');
        return;
    }

    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name: name })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create user');
        }

        const newUser = await response.json();
        console.log('Created user:', newUser);

        // Clear input and reload users
        nameInput.value = '';
        await loadUsers();
        alert(`User "${newUser.name}" created successfully!`);
    } catch (error) {
        console.error('Error creating user:', error);
        alert('Failed to create user: ' + error.message);
    }
}

// Update an existing user
async function updateUser() {
    const idInput = document.getElementById('updateId');
    const nameInput = document.getElementById('updateName');
    const id = parseInt(idInput.value);
    const name = nameInput.value.trim();

    if (!id || !name) {
        alert('Please enter both User ID and new name');
        return;
    }

    try {
        const response = await fetch(`${API_URL}/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name: name })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to update user');
        }

        const updatedUser = await response.json();
        console.log('Updated user:', updatedUser);

        // Clear inputs and reload users
        idInput.value = '';
        nameInput.value = '';
        await loadUsers();
        alert(`User ID ${id} updated successfully!`);
    } catch (error) {
        console.error('Error updating user:', error);
        alert('Failed to update user: ' + error.message);
    }
}

// Delete a user
async function deleteUser() {
    const idInput = document.getElementById('deleteId');
    const id = parseInt(idInput.value);

    if (!id) {
        alert('Please enter a User ID');
        return;
    }

    if (!confirm(`Are you sure you want to delete user ID ${id}?`)) {
        return;
    }

    try {
        const response = await fetch(`${API_URL}/${id}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to delete user');
        }

        console.log(`Deleted user ID ${id}`);

        // Clear input and reload users
        idInput.value = '';
        await loadUsers();
        alert(`User ID ${id} deleted successfully!`);
    } catch (error) {
        console.error('Error deleting user:', error);
        alert('Failed to delete user: ' + error.message);
    }
}
