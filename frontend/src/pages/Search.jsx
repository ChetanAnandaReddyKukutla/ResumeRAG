import { useState } from 'react'
import { Link } from 'react-router-dom'

function Search() {
  const [query, setQuery] = useState('')
  const [k, setK] = useState(20)
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage] = useState(5)

  const handleSearch = async (e) => {
    e.preventDefault()
    
    if (!query.trim()) {
      setError('Please enter a search query')
      return
    }

    setLoading(true)
    setError('')
    setResults(null)
    setCurrentPage(1) // Reset to first page on new search

    try {
      const response = await fetch('/api/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query, k }),
      })

      const data = await response.json()

      if (response.ok) {
        setResults(data)
      } else {
        setError(data.error?.message || 'Search failed')
      }
    } catch (err) {
      setError(`Error: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="px-4 py-6">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-2">Search Resumes</h2>
        <p className="text-gray-600">Find the perfect candidate using natural language queries</p>
      </div>
      
      <div className="bg-white shadow-xl rounded-2xl overflow-hidden border border-gray-100">
        <div className="bg-gradient-to-r from-indigo-500 to-purple-600 px-6 py-4">
          <h3 className="text-white text-lg font-semibold flex items-center">
            <svg className="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            Semantic Search
          </h3>
        </div>
        
        <form onSubmit={handleSearch} className="p-6">
          <div className="mb-6">
            <label className="block text-sm font-semibold text-gray-700 mb-3">
              Search Query
            </label>
            <div className="relative">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="e.g., Who knows React and Node.js?"
                className="w-full px-4 py-3 pl-12 border-2 border-gray-200 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all duration-200"
              />
              <svg className="absolute left-4 top-3.5 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
          </div>

          <div className="mb-6">
            <label className="block text-sm font-semibold text-gray-700 mb-3">
              Number of Results
            </label>
            <div className="flex items-center space-x-4">
              <input
                type="range"
                value={k}
                onChange={(e) => setK(parseInt(e.target.value))}
                min="1"
                max="20"
                className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
              />
              <div className="w-16 px-3 py-2 text-center bg-indigo-50 text-indigo-700 font-semibold rounded-lg border-2 border-indigo-200">
                {k}
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 px-6 border border-transparent rounded-xl shadow-lg text-base font-semibold text-white bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-[1.02]"
          >
            {loading ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Searching...
              </span>
            ) : (
              <span className="flex items-center justify-center">
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                Search Resumes
              </span>
            )}
          </button>
        </form>

        {error && (
          <div className="mx-6 mb-6 p-4 rounded-xl bg-red-50 border-l-4 border-red-500 text-red-800 flex items-start animate-fade-in">
            <svg className="w-5 h-5 mr-3 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <div>{error}</div>
          </div>
        )}

        {results && (
          <div className="border-t border-gray-200">
            <div className="flex items-center justify-between px-6 py-4 bg-gray-50">
              <div className="flex items-center">
                <h3 className="text-lg font-semibold text-gray-900">
                  Results ({results.answers.length})
                </h3>
                {results.answers.length > 0 && (
                  <span className="ml-3 px-3 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
                    {results.cached ? '⚡ Cached' : '✨ Fresh'}
                  </span>
                )}
              </div>
            </div>

            {results.answers.length === 0 ? (
              <div className="px-6 py-12 text-center">
                <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="mt-4 text-gray-500 font-medium">No matching resumes found.</p>
                <p className="mt-2 text-sm text-gray-400">Try adjusting your search query or uploading more resumes</p>
              </div>
            ) : (
              <>
                <div className="px-6 py-4 space-y-4">
                  {results.answers
                    .slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage)
                    .map((answer, idx) => {
                  // Extract keywords from search query for highlighting
                  const extractKeywords = (searchQuery) => {
                    // Split by common delimiters and keep all words including short ones
                    return searchQuery
                      .split(/[,;\s]+/)
                      .map(k => k.trim())
                      .filter(k => k.length > 0); // Changed from > 2 to > 0 to include short words
                  };

                  // Function to highlight matched keywords in text
                  const highlightText = (text, searchQuery) => {
                    if (!searchQuery || !text) return text;
                    
                    // Escape special regex characters
                    const escapeRegex = (str) => {
                      return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                    };
                    
                    // Get keywords from search query
                    const keywords = extractKeywords(searchQuery);
                    
                    if (keywords.length === 0) return text;
                    
                    // Create regex pattern for all keywords with word boundaries
                    const pattern = keywords.map(k => escapeRegex(k)).join('|');
                    const regex = new RegExp(`\\b(${pattern})\\b`, 'gi');
                    
                    // Split text by matches
                    const parts = text.split(regex);
                    
                    return parts.map((part, index) => {
                      // Check if this part matches any keyword (case-insensitive)
                      const isMatch = keywords.some(k => 
                        part.toLowerCase() === k.toLowerCase()
                      );
                      
                      if (isMatch) {
                        return (
                          <mark
                            key={index}
                            className="bg-yellow-300 text-gray-900 font-semibold px-1 rounded shadow-sm"
                          >
                            {part}
                          </mark>
                        );
                      }
                      return <span key={index}>{part}</span>;
                    });
                  };

                  return (
                    <div key={idx} className="border border-gray-200 rounded-xl p-5 hover:shadow-lg transition-all duration-200 bg-white hover:border-indigo-300">
                      <div className="flex items-center justify-between mb-3">
                        <Link
                          to={`/candidates/${answer.resume_id}`}
                          className="text-lg font-semibold text-indigo-600 hover:text-indigo-800 flex items-center transition-colors duration-200"
                        >
                          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                          </svg>
                          {answer.filename || `Resume ${answer.resume_id}`}
                        </Link>
                        <div className="flex items-center space-x-2">
                          <span className="px-3 py-1 text-sm font-bold bg-gradient-to-r from-green-100 to-emerald-100 text-green-700 rounded-full border border-green-300">
                            {(answer.score * 100).toFixed(1)}% Match
                          </span>
                        </div>
                      </div>

                      <div className="mt-4">
                        <p className="text-sm font-semibold text-gray-700 mb-3 flex items-center">
                          <svg className="w-4 h-4 mr-2 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                          </svg>
                          Relevant Snippets:
                        </p>
                        <div className="space-y-2">
                          {answer.snippets.map((snippet, sidx) => (
                            <div key={sidx} className="bg-gradient-to-r from-gray-50 to-blue-50 p-4 rounded-lg border border-gray-200 hover:border-indigo-300 transition-colors duration-200">
                              <p className="text-sm text-gray-800 leading-relaxed">
                                {highlightText(snippet.text, query)}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  );
                })}
                </div>

                {/* Pagination Controls */}
                {results.answers.length > itemsPerPage && (
                  <div className="mt-6 flex items-center justify-between border-t border-gray-200 pt-4">
                    <div className="flex-1 flex justify-between sm:hidden">
                      <button
                        onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                        disabled={currentPage === 1}
                        className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:bg-gray-100 disabled:text-gray-400"
                      >
                        Previous
                      </button>
                      <button
                        onClick={() => setCurrentPage(p => Math.min(Math.ceil(results.answers.length / itemsPerPage), p + 1))}
                        disabled={currentPage === Math.ceil(results.answers.length / itemsPerPage)}
                        className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:bg-gray-100 disabled:text-gray-400"
                      >
                        Next
                      </button>
                    </div>
                    <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                      <div>
                        <p className="text-sm text-gray-700">
                          Showing{' '}
                          <span className="font-medium">{(currentPage - 1) * itemsPerPage + 1}</span>
                          {' '}-{' '}
                          <span className="font-medium">
                            {Math.min(currentPage * itemsPerPage, results.answers.length)}
                          </span>
                          {' '}of{' '}
                          <span className="font-medium">{results.answers.length}</span>
                          {' '}results
                        </p>
                      </div>
                      <div>
                        <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                          <button
                            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                            disabled={currentPage === 1}
                            className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:bg-gray-100 disabled:text-gray-400"
                          >
                            <span className="sr-only">Previous</span>
                            <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                              <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                          </button>
                          
                          {[...Array(Math.ceil(results.answers.length / itemsPerPage))].map((_, idx) => (
                            <button
                              key={idx}
                              onClick={() => setCurrentPage(idx + 1)}
                              className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                                currentPage === idx + 1
                                  ? 'z-10 bg-indigo-50 border-indigo-500 text-indigo-600'
                                  : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                              }`}
                            >
                              {idx + 1}
                            </button>
                          ))}
                          
                          <button
                            onClick={() => setCurrentPage(p => Math.min(Math.ceil(results.answers.length / itemsPerPage), p + 1))}
                            disabled={currentPage === Math.ceil(results.answers.length / itemsPerPage)}
                            className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:bg-gray-100 disabled:text-gray-400"
                          >
                            <span className="sr-only">Next</span>
                            <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                              <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                            </svg>
                          </button>
                        </nav>
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default Search
