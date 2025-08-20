// server.js

const express = require('express');
const multer = require('multer');
const cors = require('cors');
const fs = require('fs');
const path = require('path');

// Initialize the express app
const app = express();
const port = 3001;

// --- Middleware ---

// Enable Cross-Origin Resource Sharing (CORS)
// This is crucial for allowing our React frontend (running on localhost:3000)
// to communicate with our backend (running on localhost:3001)
app.use(cors());

// --- File Storage Configuration with Multer ---

// Define the destination for uploaded files
const uploadDir = 'uploads';

// Create the 'uploads' directory if it doesn't exist
if (!fs.existsSync(uploadDir)) {
    fs.mkdirSync(uploadDir);
    console.log(`Created directory: ${uploadDir}`);
}

// Configure multer's storage engine
const storage = multer.diskStorage({
    // Set the destination directory for uploaded files
    destination: function (req, file, cb) {
        cb(null, uploadDir);
    },
    // Set the filename. We'll keep the original filename.
    filename: function (req, file, cb) {
        // Using Date.now() to prevent filename conflicts if a file is uploaded multiple times
        const uniquePrefix = Date.now() + '-';
        cb(null, uniquePrefix + file.originalname);
    }
});

// Initialize multer with the storage configuration
const upload = multer({ storage: storage });

// --- API Routes ---

// POST endpoint for file uploads
// The 'document' string must match the key used in the FormData on the frontend
app.post('/upload', upload.single('document'), (req, res) => {
    // req.file is the 'document' file
    // req.body will hold the text fields, if there were any

    if (!req.file) {
        // If no file is uploaded, send an error response
        return res.status(400).json({ error: 'No file uploaded.' });
    }

    // If the file is uploaded successfully, send a success response
    console.log(`File uploaded successfully: ${req.file.filename}`);
    res.status(200).json({
        message: 'File uploaded successfully!',
        filename: req.file.filename,
        path: req.file.path,
        size: req.file.size
    });
});

// A simple health check route
app.get('/', (req, res) => {
    res.send('Knowledge Base Backend is running!');
});


// --- Start the Server ---

app.listen(port, () => {
    console.log(`Backend server listening at http://localhost:${port}`);
    console.log(`Uploaded files will be stored in the '${path.resolve(uploadDir)}' directory.`);
});
