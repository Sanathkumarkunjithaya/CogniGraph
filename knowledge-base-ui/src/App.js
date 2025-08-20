import React, { useState, useCallback, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { Loader, File, UploadCloud, X, CheckCircle, AlertCircle } from 'lucide-react';

// Main App Component
const App = () => {
  const [files, setFiles] = useState([]);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState(null);
  const [query, setQuery] = useState('');
  const [queryResult, setQueryResult] = useState('');
  const [isQuerying, setIsQuerying] = useState(false);
  const [queryError, setQueryError] = useState(null);

  const onDrop = useCallback(acceptedFiles => {
    const newFiles = acceptedFiles.map(file => Object.assign(file, {
      preview: URL.createObjectURL(file),
      status: 'queued'
    }));
    setFiles(prevFiles => [...prevFiles, ...newFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/plain': ['.txt'],
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']
    }
  });

  const removeFile = (fileName) => {
    setFiles(files.filter(file => file.name !== fileName));
  };

  const handleUpload = async () => {
    if (files.length === 0) {
      setError('Please select files to upload.');
      return;
    }
    setIsUploading(true);
    setError(null);

    const uploadPromises = files.map(async (file) => {
      const formData = new FormData();
      formData.append('document', file);
      try {
        // IMPORTANT: Replace with your actual backend URL
        const response = await fetch('http://localhost:3001/upload', {
          method: 'POST',
          body: formData,
        });
        if (!response.ok) {
          throw new Error(`Upload failed for ${file.name}`);
        }
        const result = await response.json();
        setFiles(prev => prev.map(f => f.name === file.name ? { ...f, status: 'success' } : f));
        return { name: file.name, status: 'success', data: result };
      } catch (error) {
        setFiles(prev => prev.map(f => f.name === file.name ? { ...f, status: 'error' } : f));
        return { name: file.name, status: 'error', error: error.message };
      }
    });

    const results = await Promise.all(uploadPromises);
    setUploadedFiles(prev => [...prev, ...results.filter(r => r.status === 'success')]);
    setIsUploading(false);
    setFiles([]); // Clear the queue after upload
  };

  const handleQuery = async () => {
    if (!query.trim()) {
      setQueryError("Please enter a query.");
      return;
    }
    setIsQuerying(true);
    setQueryError(null);
    setQueryResult('');
    try {
      // IMPORTANT: Replace with your actual query engine URL
      const response = await fetch('http://localhost:5000/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      });
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.error || 'Failed to fetch result from query engine.');
      }
      const data = await response.json();
      setQueryResult(data.answer);
    } catch (err) {
      setQueryError(err.message);
    } finally {
      setIsQuerying(false);
    }
  };


  return (
    <div className="min-h-screen bg-gray-50 font-sans text-gray-800">
      <div className="container mx-auto p-4 sm:p-6 lg:p-8">
        <header className="text-center mb-10">
          <h1 className="text-4xl sm:text-5xl font-bold text-gray-900">Document Processor - infoconnect</h1>
          <p className="text-lg text-gray-600 mt-2">Process documents, build a knowledge graph, and ask questions.</p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column: Document Upload */}
          <div className="bg-white p-6 rounded-xl shadow-lg border border-gray-200">
            <h2 className="text-2xl font-semibold mb-4 text-gray-800">1. Upload Documents</h2>

            <div {...getRootProps()} className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors duration-300 ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'}`}>
              <input {...getInputProps()} />
              <UploadCloud className="mx-auto h-12 w-12 text-gray-400" />
              <p className="mt-4 text-gray-600">
                {isDragActive ? "Drop the files here..." : "Drag 'n' drop some files here, or click to select files"}
              </p>
              <p className="text-sm text-gray-500 mt-1">.txt, .pdf, .docx supported</p>
            </div>

            {files.length > 0 && (
              <div className="mt-6">
                <h3 className="font-semibold text-lg">Files Queued for Upload:</h3>
                <ul className="mt-3 space-y-2">
                  {files.map(file => (
                    <li key={file.name} className="flex items-center justify-between bg-gray-100 p-3 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <File className="h-5 w-5 text-gray-500" />
                        <span className="text-sm font-medium">{file.name}</span>
                      </div>
                      <button onClick={() => removeFile(file.name)} className="text-gray-500 hover:text-red-600">
                        <X className="h-5 w-5" />
                      </button>
                    </li>
                  ))}
                </ul>
                <button
                  onClick={handleUpload}
                  disabled={isUploading}
                  className="w-full mt-4 bg-blue-600 text-white font-bold py-3 px-4 rounded-lg hover:bg-blue-700 transition-all duration-300 disabled:bg-blue-300 disabled:cursor-not-allowed flex items-center justify-center"
                >
                  {isUploading ? <><Loader className="animate-spin mr-2" /> Uploading...</> : 'Upload Files'}
                </button>
              </div>
            )}

            {error && <div className="mt-4 text-red-600 bg-red-100 p-3 rounded-lg flex items-center"><AlertCircle className="mr-2" />{error}</div>}

            {uploadedFiles.length > 0 && (
              <div className="mt-6">
                <h3 className="font-semibold text-lg">Successfully Uploaded:</h3>
                <ul className="mt-3 space-y-2">
                  {uploadedFiles.map((file, index) => (
                    <li key={index} className="flex items-center bg-green-100 p-3 rounded-lg text-green-800">
                      <CheckCircle className="h-5 w-5 mr-3" />
                      <span className="text-sm font-medium">{file.name}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Right Column: Query Engine */}
          <div className="bg-white p-6 rounded-xl shadow-lg border border-gray-200">
            <h2 className="text-2xl font-semibold mb-4 text-gray-800">2. Query the Knowledge Base</h2>
            <p className="text-gray-600 mb-4">Once documents are processed, ask questions in natural language.</p>

            <div className="space-y-4">
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g., 'What were the main findings of the research paper?' or 'Summarize the project update.'"
                className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-shadow duration-200"
                rows="4"
              />
              <button
                onClick={handleQuery}
                disabled={isQuerying}
                className="w-full bg-green-600 text-white font-bold py-3 px-4 rounded-lg hover:bg-green-700 transition-all duration-300 disabled:bg-green-300 disabled:cursor-not-allowed flex items-center justify-center"
              >
                {isQuerying ? <><Loader className="animate-spin mr-2" /> Asking...</> : 'Get Insights'}
              </button>
            </div>

            {queryError && <div className="mt-4 text-red-600 bg-red-100 p-3 rounded-lg flex items-center"><AlertCircle className="mr-2" />{queryError}</div>}

            {isQuerying && (
              <div className="mt-6 text-center">
                <Loader className="animate-spin inline-block h-8 w-8 text-gray-500" />
                <p className="text-gray-600 mt-2">Searching the knowledge graph...</p>
              </div>
            )}

            {queryResult && (
              <div className="mt-6">
                <h3 className="font-semibold text-lg">Answer:</h3>
                <div className="mt-3 p-4 bg-gray-100 rounded-lg border border-gray-200 whitespace-pre-wrap font-mono text-sm">
                  {queryResult}
                </div>
              </div>
            )}
          </div>
        </div>
        <footer className="text-center mt-12 text-gray-500 text-sm">
          <p>AI Knowledge Base System - Case Study</p>
        </footer>
      </div>
    </div>
  );
};

export default App;
