'use client'

import { useState } from 'react'

export default function GeneratePost() {
  const [userRequest, setUserRequest] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState<{
    conversation_id: string
    status: string
    final_output: string
  } | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!userRequest.trim()) return

    setIsLoading(true)
    try {
      const response = await fetch('http://127.0.0.1:8000/coordinator/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_request: userRequest,
          conversation_title: 'Generated Post',
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to generate post')
      }

      const data = await response.json()
      setResult(data)
    } catch (error) {
      console.error('Error:', error)
      alert('Failed to generate post. Make sure the backend server is running.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Generate Post</h1>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="userRequest" className="block text-sm font-medium text-gray-700 mb-2">
              What would you like to post about?
            </label>
            <textarea
              id="userRequest"
              value={userRequest}
              onChange={(e) => setUserRequest(e.target.value)}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="Write a LinkedIn post about remote work productivity..."
              disabled={isLoading}
            />
          </div>
          
          <button
            type="submit"
            disabled={isLoading || !userRequest.trim()}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-bold py-2 px-4 rounded"
          >
            {isLoading ? 'Generating...' : 'Run Coordinator'}
          </button>
        </form>

        {result && (
          <div className="mt-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Generated Content</h2>
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <div className="mb-4">
                <span className="inline-block bg-blue-100 text-blue-800 text-xs font-medium px-2.5 py-0.5 rounded">
                  {result.status}
                </span>
                <span className="ml-2 text-sm text-gray-500">
                  Conversation ID: {result.conversation_id}
                </span>
              </div>
              <div className="prose max-w-none">
                <pre className="whitespace-pre-wrap text-sm text-gray-700">
                  {result.final_output}
                </pre>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
