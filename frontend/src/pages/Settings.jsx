import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import apiClient from '../api/client'
import { ChevronLeft, Save, RefreshCw, CheckCircle, AlertCircle, Code } from 'lucide-react'

export default function Settings() {
  const navigate = useNavigate()
  const [openaiKey, setOpenaiKey] = useState('')
  const [promptsJson, setPromptsJson] = useState('')
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState(null)

  // Fetch auth status
  const { data: authStatus } = useQuery({
    queryKey: ['authStatus'],
    queryFn: async () => {
      const response = await apiClient.get('/auth/status')
      return response.data
    }
  })

  // Fetch prompts
  const { data: prompts, refetch: refetchPrompts } = useQuery({
    queryKey: ['prompts'],
    queryFn: async () => {
      const response = await apiClient.get('/api/reviews/prompts')
      return response.data
    }
  })

  useEffect(() => {
    if (prompts) {
      setPromptsJson(JSON.stringify(prompts, null, 2))
    }
  }, [prompts])

  const handleSaveOpenAIKey = () => {
    // In a real app, you'd save this to backend
    // For now, just show success message
    localStorage.setItem('openai_api_key', openaiKey)
    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  const handleReloadPrompts = async () => {
    try {
      setError(null)
      await apiClient.post('/api/reviews/reload-prompts')
      refetchPrompts()
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (err) {
      setError(err.response?.data?.detail || '프롬프트 새로고침 실패')
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center">
            <button
              onClick={() => navigate('/dashboard')}
              className="mr-4 text-gray-600 hover:text-gray-900"
            >
              <ChevronLeft className="w-6 h-6" />
            </button>
            <h1 className="text-2xl font-bold text-gray-900">설정</h1>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {saved && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
            <div className="flex items-center">
              <CheckCircle className="w-5 h-5 text-green-600 mr-3" />
              <p className="text-sm text-green-800">설정이 저장되었습니다!</p>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <div className="flex items-center">
              <AlertCircle className="w-5 h-5 text-red-600 mr-3" />
              <p className="text-sm text-red-800">{error}</p>
            </div>
          </div>
        )}

        {/* Google Account Status */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Google 계정 연결</h2>
          
          {authStatus?.authenticated ? (
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <CheckCircle className="w-5 h-5 text-green-600 mr-3" />
                <div>
                  <p className="text-sm font-medium text-gray-900">연결됨</p>
                  <p className="text-sm text-gray-600">Google Business Profile에 연결되어 있습니다</p>
                </div>
              </div>
              <button
                onClick={async () => {
                  await apiClient.post('/auth/logout')
                  navigate('/login')
                }}
                className="px-4 py-2 border border-red-600 text-red-600 rounded-md hover:bg-red-50"
              >
                연결 해제
              </button>
            </div>
          ) : (
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <AlertCircle className="w-5 h-5 text-yellow-600 mr-3" />
                <div>
                  <p className="text-sm font-medium text-gray-900">연결되지 않음</p>
                  <p className="text-sm text-gray-600">Google 계정을 연결해주세요</p>
                </div>
              </div>
              <button
                onClick={() => navigate('/login')}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                연결하기
              </button>
            </div>
          )}
        </div>

        {/* OpenAI API Key */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">OpenAI API 설정</h2>
          <p className="text-sm text-gray-600 mb-4">
            AI 답글 생성을 위해 OpenAI API 키가 필요합니다.
          </p>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                API 키
              </label>
              <input
                type="password"
                value={openaiKey}
                onChange={(e) => setOpenaiKey(e.target.value)}
                placeholder="sk-..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <p className="text-xs text-gray-500 mt-2">
                현재는 브라우저에만 저장됩니다. 실제로는 .env 파일에 OPENAI_API_KEY를 설정하세요.
              </p>
            </div>

            <button
              onClick={handleSaveOpenAIKey}
              disabled={!openaiKey}
              className="flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded-md"
            >
              <Save className="w-4 h-4 mr-2" />
              저장
            </button>
          </div>
        </div>

        {/* Prompt Templates */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">프롬프트 템플릿</h2>
            <button
              onClick={handleReloadPrompts}
              className="flex items-center px-3 py-1.5 text-sm border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
            >
              <RefreshCw className="w-4 h-4 mr-1" />
              새로고침
            </button>
          </div>

          <p className="text-sm text-gray-600 mb-4">
            AI 답글 생성에 사용되는 프롬프트 템플릿입니다. 
            <code className="bg-gray-100 px-1 py-0.5 rounded text-xs">data/prompts.json</code> 파일을 직접 수정한 후 새로고침하세요.
          </p>

          <div className="relative">
            <Code className="absolute top-3 left-3 w-5 h-5 text-gray-400" />
            <textarea
              value={promptsJson}
              readOnly
              className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md bg-gray-50 font-mono text-xs resize-none"
              rows={20}
            />
          </div>

          <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="text-sm font-medium text-blue-900 mb-2">템플릿 사용 방법</h3>
            <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
              <li><strong>positive</strong>: 4-5점 리뷰에 사용</li>
              <li><strong>neutral</strong>: 3점 리뷰에 사용</li>
              <li><strong>negative</strong>: 1-2점 리뷰에 사용</li>
              <li><code className="bg-blue-100 px-1 rounded">{'data/prompts.json'}</code> 파일을 수정 후 새로고침 버튼 클릭</li>
            </ul>
          </div>
        </div>
      </main>
    </div>
  )
}








