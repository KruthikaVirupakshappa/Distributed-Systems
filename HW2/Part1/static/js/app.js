const api_base = '/api/books';

document.addEventListener('DOMContentLoaded', () => {
    loadBooks();
});

async function loadBooks() {
    try {
        const res = await fetch(api_base);
        if (!res.ok) throw new Error('Failed to fetch books');
        const books = await res.json();
        renderBooks(books);
    } catch (err) {
        console.error(err);
        alert('Could not load books. See console for details.');
    }
}

function renderBooks(books) {
    const tbody = document.getElementById('booksTableBody');
    tbody.innerHTML = '';
    if (!Array.isArray(books) || books.length === 0) {
        const row = document.createElement('tr');
        const cell = document.createElement('td');
        cell.colSpan = 3;
        cell.textContent = 'No books found';
        row.appendChild(cell);
        tbody.appendChild(row);
        return;
    }

    books.forEach(book => {
        const tr = document.createElement('tr');
        const idTd = document.createElement('td');
        idTd.textContent = book.id;
        const titleTd = document.createElement('td');
        titleTd.textContent = book.title;
        const authorTd = document.createElement('td');
        authorTd.textContent = book.author;

        tr.appendChild(idTd);
        tr.appendChild(titleTd);
        tr.appendChild(authorTd);
        tbody.appendChild(tr);
    });
}

// Search books by title
async function searchBooks() {
    const q = document.getElementById('searchTitle').value.trim().toLowerCase();
    try {
        const res = await fetch(api_base);
        if (!res.ok) throw new Error('Failed to fetch books');
        const books = await res.json();
        if (!q) return renderBooks(books);
        const filtered = books.filter(b => (b.title || '').toLowerCase().includes(q));
        renderBooks(filtered);
    } catch (err) {
        console.error(err);
        alert('Search failed. See console for details.');
    }
}

// Add new book
async function addBook() {
    const titleEl = document.getElementById('addTitle');
    const authorEl = document.getElementById('addAuthor');
    const title = titleEl.value.trim();
    const author = authorEl.value.trim();
    if (!title || !author) {
        alert('Please provide both title and author.');
        return;
    }
    try {
        const res = await fetch(api_base, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, author })
        });
        if (!res.ok) throw new Error('Failed to add book');
        titleEl.value = '';
        authorEl.value = '';
        await loadBooks();
    } catch (err) {
        console.error(err);
        alert('Could not add book. See console for details.');
    }
}

// Update book by ID
async function updateBook() {
    const id = Number(document.getElementById('updateId').value);
    const title = document.getElementById('updateTitle').value.trim();
    const author = document.getElementById('updateAuthor').value.trim();
    if (!id || id <= 0) {
        alert('Please provide a valid book ID to update.');
        return;
    }
    if (!title && !author) {
        alert('Provide at least a new title or a new author to update.');
        return;
    }
    const body = {};
    if (title) body.title = title;
    if (author) body.author = author;
    try {
        const res = await fetch(`${api_base}/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        if (!res.ok) throw new Error('Failed to update book');
        document.getElementById('updateId').value = '';
        document.getElementById('updateTitle').value = '';
        document.getElementById('updateAuthor').value = '';
        await loadBooks();
    } catch (err) {
        console.error(err);
        alert('Could not update book. See console for details.');
    }
}

// Delete the book with the highest numeric ID
async function deleteHighestIdBook() {
    try {
        const res = await fetch(api_base);
        if (!res.ok) throw new Error('Failed to fetch books');
        const books = await res.json();
        if (!Array.isArray(books) || books.length === 0) {
            alert('No books available to delete.');
            return;
        }
        const max = books.reduce((acc, b) => {
            const idNum = Number(b.id);
            if (!isNaN(idNum) && idNum > acc) return idNum;
            return acc;
        }, -Infinity);
        if (!isFinite(max)) {
            alert('No valid numeric IDs found.');
            return;
        }
        const del = await fetch(`${api_base}/${max}`, { method: 'DELETE' });
        if (!del.ok) throw new Error('Failed to delete book');
        await loadBooks();
    } catch (err) {
        console.error(err);
        alert('Could not delete book. See console for details.');
    }
}
