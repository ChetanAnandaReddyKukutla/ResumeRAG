import { useState } from 'react'

function Upload() {
  const [file, setFile] = useState(null)
  const [status, setStatus] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [isDragging, setIsDragging] = useState(false)

  const handleFileChange = (e) => {
    setFile(e.target.files[0])
    setStatus('')
    setResult(null)
  }

  const handleDragEnter = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    e.stopPropagation()
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)

    const files = e.dataTransfer.files
    if (files && files.length > 0) {
      const droppedFile = files[0]
      // Check file type
      const allowedTypes = ['.pdf', '.docx', '.txt', '.zip']
      const fileExtension = '.' + droppedFile.name.split('.').pop().toLowerCase()
      
      if (allowedTypes.includes(fileExtension)) {
        setFile(droppedFile)
        setStatus('')
        setResult(null)
      } else {
        setStatus('Error: Please upload PDF, DOCX, TXT, or ZIP files only')
      }
    }
  }

  const handleUpload = async (e) => {
    e.preventDefault()
    
    if (!file) {
      setStatus('Please select a file')
      return
    }

    setLoading(true)
    setStatus('Uploading...')

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('visibility', 'public')

      // Generate idempotency key
      const idempotencyKey = crypto.randomUUID()

      const response = await fetch('/api/resumes', {
        method: 'POST',
        headers: {
          'Idempotency-Key': idempotencyKey,
        },
        body: formData,
      })

      const data = await response.json()

      if (response.ok) {
        setResult(data)
        setStatus('✓ Resume uploaded successfully!')
      } else {
        setStatus(`Error: ${data.error?.message || 'Upload failed'}`)
      }
    } catch (error) {
      setStatus(`Error: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="px-4 py-6">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-2">Upload Resume</h2>
        <p className="text-gray-600">Upload resumes to build your candidate database</p>
      </div>
      
      <div className="bg-white shadow-xl rounded-2xl overflow-hidden max-w-3xl border border-gray-100">
        <div className="bg-gradient-to-r from-indigo-500 to-purple-600 px-6 py-4">
          <h3 className="text-white text-lg font-semibold flex items-center">
            <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            File Upload
          </h3>
        </div>
        
        <form onSubmit={handleUpload} className="p-6">
          <div className="mb-6">
            <label className="block text-sm font-semibold text-gray-700 mb-3">
              Select Resume File
            </label>
            <div 
              className={`mt-1 flex justify-center px-6 pt-8 pb-8 border-3 rounded-xl transition-all duration-200 ${
                file 
                  ? 'border-indigo-400 bg-indigo-50 border-solid' 
                  : isDragging
                    ? 'border-indigo-600 bg-indigo-100 border-solid'
                    : 'border-gray-300 border-dashed hover:border-indigo-400 hover:bg-gray-50'
              }`}
              onDragEnter={handleDragEnter}
              onDragLeave={handleDragLeave}
              onDragOver={handleDragOver}
              onDrop={handleDrop}
            >
              <div className="space-y-2 text-center">
                {file ? (
                  <>
                    <svg className="mx-auto h-16 w-16 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p className="text-lg font-semibold text-indigo-700">{file.name}</p>
                    <p className="text-sm text-gray-500">{(file.size / 1024).toFixed(2)} KB</p>
                  </>
                ) : (
                  <>
                    <svg
                      className="mx-auto h-16 w-16 text-gray-400"
                      stroke="currentColor"
                      fill="none"
                      viewBox="0 0 48 48"
                      aria-hidden="true"
                    >
                      <path
                        d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                        strokeWidth={2}
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                    <div className="flex text-base text-gray-600">
                      <label
                        htmlFor="file-upload"
                        className="relative cursor-pointer bg-white rounded-md font-semibold text-indigo-600 hover:text-indigo-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-indigo-500"
                      >
                        <span>Upload a file</span>
                        <input
                          id="file-upload"
                          name="file-upload"
                          type="file"
                          className="sr-only"
                          accept=".pdf,.docx,.txt,.zip"
                          onChange={handleFileChange}
                        />
                      </label>
                      <p className="pl-1">or drag and drop</p>
                    </div>
                    <p className="text-sm text-gray-500">
                      PDF, DOCX, TXT, or ZIP up to 10MB
                    </p>
                  </>
                )}
                {file && (
                  <button
                    type="button"
                    onClick={() => {
                      setFile(null)
                      setStatus('')
                      setResult(null)
                    }}
                    className="mt-3 text-sm text-indigo-600 hover:text-indigo-800 font-medium"
                  >
                    Choose different file
                  </button>
                )}
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || !file}
            className="w-full py-3 px-6 border border-transparent rounded-xl shadow-lg text-base font-semibold text-white bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-[1.02]"
          >
            {loading ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Uploading...
              </span>
            ) : (
              <span className="flex items-center justify-center">
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                Upload Resume
              </span>
            )}
          </button>
        </form>

        {status && (
          <div className={`mx-6 mb-6 p-4 rounded-xl border-l-4 flex items-start animate-fade-in ${
            status.startsWith('✓') 
              ? 'bg-green-50 border-green-500 text-green-800' 
              : 'bg-red-50 border-red-500 text-red-800'
          }`}>
            <svg className={`w-5 h-5 mr-3 flex-shrink-0 mt-0.5 ${status.startsWith('✓') ? 'text-green-500' : 'text-red-500'}`} fill="currentColor" viewBox="0 0 20 20">
              {status.startsWith('✓') ? (
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              ) : (
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              )}
            </svg>
            <div className="font-medium">{status}</div>
          </div>
        )}

        {result && (
          <div className="mx-6 mb-6 bg-gradient-to-r from-gray-50 to-blue-50 p-5 rounded-xl border border-gray-200">
            <h3 className="font-semibold text-gray-900 mb-3 flex items-center">
              <svg className="w-5 h-5 mr-2 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Upload Details
            </h3>
            <dl className="text-sm text-gray-700 space-y-2">
              <div className="flex items-center">
                <dt className="font-semibold mr-2">ID:</dt>
                <dd className="font-mono text-xs bg-white px-2 py-1 rounded border border-gray-300">{result.id}</dd>
              </div>
              <div className="flex items-center">
                <dt className="font-semibold mr-2">Filename:</dt>
                <dd>{result.filename}</dd>
              </div>
              <div className="flex items-center">
                <dt className="font-semibold mr-2">Status:</dt>
                <dd>
                  <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
                    {result.status}
                  </span>
                </dd>
              </div>
              <div className="flex items-center">
                <dt className="font-semibold mr-2">Uploaded:</dt>
                <dd>{new Date(result.uploaded_at).toLocaleString()}</dd>
              </div>
            </dl>
          </div>
        )}
      </div>
    </div>
  )
}

export default Upload
