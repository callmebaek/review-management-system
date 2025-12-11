import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import apiClient from '../api/client'
import { Download, CheckCircle, XCircle, AlertCircle, Info, RefreshCw, Trash2, HelpCircle, Users } from 'lucide-react'

export default function NaverLogin() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [sessions, setSessions] = useState([])
  const [activeSession, setActiveSession] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [showGuide, setShowGuide] = useState(false)

  // Check all sessions
  useEffect(() => {
    loadSessions()
  }, [])

  const loadSessions = async () => {
    try {
      setLoading(true)
      const response = await apiClient.get('/api/naver/sessions/list', { timeout: 5000 })
      setSessions(response.data.sessions || [])
      
      // Set first active session as default
      if (response.data.sessions && response.data.sessions.length > 0) {
        const active = response.data.sessions.find(s => s.user_id === 'default') || response.data.sessions[0]
        setActiveSession(active.user_id)
        // Store in localStorage
        localStorage.setItem('active_naver_user', active.user_id)
      }
      
      setError(null)
    } catch (err) {
      setSessions([])
      console.log('No sessions found')
    } finally {
      setLoading(false)
    }
  }

  const switchSession = async (user_id) => {
    try {
      await apiClient.post(`/api/naver/session/switch?user_id=${user_id}`)
      setActiveSession(user_id)
      localStorage.setItem('active_naver_user', user_id)
      
      // 🚀 캐시 무효화: 이전 계정의 데이터 제거
      queryClient.invalidateQueries(['naverPlaces'])
      queryClient.invalidateQueries(['naverStatus'])
      queryClient.removeQueries(['naver-reviews'])  // 모든 리뷰 캐시 제거
      
      alert(`✅ ${user_id} 계정으로 전환되었습니다!\n\n잠시 후 해당 계정의 매장 목록이 표시됩니다.`)
      
      // 전환 후 잠시 대기하고 Dashboard로 자동 이동
      setTimeout(() => {
        navigate('/dashboard')
      }, 1000)
    } catch (err) {
      alert('계정 전환 중 오류가 발생했습니다')
    }
  }

  const handleDeleteSession = async (user_id) => {
    if (!confirm(`'${user_id}' 세션을 삭제하시겠습니까? 다시 로그인해야 합니다.`)) {
      return
    }
    
    try {
      setLoading(true)
      await apiClient.delete(`/api/naver/session?user_id=${user_id}`)
      
      // Reload sessions
      await loadSessions()
      
      setError(null)
    } catch (err) {
      setError('세션 삭제 중 오류가 발생했습니다')
    } finally {
      setLoading(false)
    }
  }

  const handleDownloadTool = () => {
    // GitHub Releases에서 다운로드 (최신 버전)
    window.open('https://github.com/callmebaek/review-management-system/releases/latest/download/NaverSessionCreator.exe', '_blank')
  }

  const formatDate = (dateString) => {
    if (!dateString) return '-'
    const date = new Date(dateString)
    const now = new Date()
    const diff = Math.floor((now - date) / 1000)
    
    if (diff < 60) return '방금 전'
    if (diff < 3600) return `${Math.floor(diff / 60)}분 전`
    if (diff < 86400) return `${Math.floor(diff / 3600)}시간 전`
    return `${Math.floor(diff / 86400)}일 전`
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-xl p-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto"></div>
          <p className="text-center mt-4 text-gray-600">세션 상태 확인 중...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl p-8 max-w-2xl w-full">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">📱 네이버 플레이스 연결</h1>
          <p className="text-gray-600">세션 생성 도구로 간편하게 연결하세요</p>
        </div>

        {/* Multi-Account Sessions */}
        {sessions.length > 0 ? (
          <div className="mb-6">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center">
                <Users className="w-5 h-5 mr-2" />
                연결된 계정 ({sessions.length}개)
              </h2>
              <button
                onClick={loadSessions}
                disabled={loading}
                className="text-sm text-gray-600 hover:text-gray-900 flex items-center"
              >
                <RefreshCw className={`w-4 h-4 mr-1 ${loading ? 'animate-spin' : ''}`} />
                새로고침
              </button>
            </div>
            
            <div className="space-y-3">
              {sessions.map((session) => (
                <div
                  key={session.user_id}
                  className={`border-2 rounded-lg p-4 transition-all ${
                    activeSession === session.user_id
                      ? 'bg-green-50 border-green-300 shadow-sm'
                      : 'bg-white border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start flex-1">
                      {activeSession === session.user_id ? (
                        <CheckCircle className="w-5 h-5 text-green-600 mr-3 mt-0.5 flex-shrink-0" />
                      ) : (
                        <div className="w-5 h-5 mr-3 mt-0.5" />
                      )}
                      <div className="flex-1">
                        <div className="flex items-center">
                          <h3 className="text-sm font-semibold text-gray-900">
                            {session.username || session.user_id}
                          </h3>
                          {activeSession === session.user_id && (
                            <span className="ml-2 text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">
                              활성
                            </span>
                          )}
                          {session.is_expired && (
                            <span className="ml-2 text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full">
                              만료됨
                            </span>
                          )}
                        </div>
                        <div className="mt-2 space-y-1 text-xs text-gray-600">
                          <p>계정 ID: {session.user_id}</p>
                          <p>생성: {formatDate(session.created_at)}</p>
                          <p>
                            유효 기간:{' '}
                            {session.is_expired ? (
                              <span className="text-red-600 font-semibold">만료됨</span>
                            ) : session.remaining_days === 0 ? (
                              <span className="text-orange-600 font-semibold">오늘 만료</span>
                            ) : (
                              <span className="text-green-600">{session.remaining_days}일 남음</span>
                            )}
                          </p>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2 ml-4">
                      {activeSession !== session.user_id && !session.is_expired && (
                        <button
                          onClick={() => switchSession(session.user_id)}
                          className="text-xs bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded-md font-medium transition-colors"
                        >
                          전환
                        </button>
                      )}
                      <button
                        onClick={() => handleDeleteSession(session.user_id)}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50 p-1.5 rounded-md transition-colors"
                        title="삭제"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            
            <div className="mt-4 flex space-x-2">
              <button
                onClick={() => navigate('/dashboard')}
                className="flex-1 bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
              >
                📋 네이버 리뷰 보기
              </button>
            </div>
          </div>
        ) : (
          <div className="bg-gray-50 border-2 border-gray-200 rounded-lg p-6 mb-6">
            <div className="flex items-start">
              <XCircle className="w-6 h-6 text-gray-400 mr-3 mt-1 flex-shrink-0" />
              <div>
                <h3 className="text-lg font-semibold text-gray-900">세션 없음</h3>
                <p className="text-sm text-gray-600 mt-1">
                  네이버 스마트플레이스와 연결하려면 세션을 생성해야 합니다.
                </p>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-start">
            <AlertCircle className="w-5 h-5 text-red-500 mr-3 mt-0.5" />
            <div>
              <h3 className="text-sm font-medium text-red-800">오류</h3>
              <p className="text-sm text-red-700 mt-1">{error}</p>
            </div>
          </div>
        )}

        {/* Download Tool Section */}
        <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border-2 border-indigo-200 rounded-lg p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">💻 세션 생성 도구</h3>
          <p className="text-sm text-gray-700 mb-4">
            Windows PC에서 실행하는 간단한 프로그램입니다. 자동으로 네이버 로그인 후 세션을 생성합니다.
          </p>
          
          <div className="bg-white rounded-lg p-4 mb-4 space-y-2 text-sm text-gray-600">
            <div className="flex items-start">
              <span className="font-bold text-indigo-600 mr-2">1.</span>
              <span>도구를 다운로드합니다</span>
            </div>
            <div className="flex items-start">
              <span className="font-bold text-indigo-600 mr-2">2.</span>
              <span>실행 후 네이버 계정 정보를 입력합니다</span>
            </div>
            <div className="flex items-start">
              <span className="font-bold text-indigo-600 mr-2">3.</span>
              <span>브라우저가 자동으로 열리고 2단계 인증을 완료합니다</span>
            </div>
            <div className="flex items-start">
              <span className="font-bold text-indigo-600 mr-2">4.</span>
              <span>세션이 자동으로 서버에 업로드됩니다 (완료!)</span>
            </div>
          </div>
          
          <button
            onClick={handleDownloadTool}
            className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-3 px-4 rounded-lg flex items-center justify-center space-x-2 transition-colors"
          >
            <Download className="w-5 h-5" />
            <span>세션 생성 도구 다운로드 (Windows)</span>
          </button>
          
          <p className="text-xs text-gray-500 mt-3 text-center">
            파일 크기: 약 25MB | Windows 10 이상 | Chrome 자동 설치
          </p>
        </div>

        {/* Help Guide Button */}
        <button
          onClick={() => setShowGuide(!showGuide)}
          className="w-full bg-white hover:bg-gray-50 border-2 border-gray-200 text-gray-700 font-medium py-3 px-4 rounded-lg flex items-center justify-center space-x-2 transition-colors mb-6"
        >
          <HelpCircle className="w-5 h-5" />
          <span>{showGuide ? '가이드 닫기' : '자세한 사용 가이드 보기'}</span>
        </button>

        {/* Detailed Guide */}
        {showGuide && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6">
            <h3 className="text-lg font-semibold text-blue-900 mb-4">📚 상세 가이드</h3>
            
            <div className="space-y-4 text-sm text-blue-900">
              <div>
                <h4 className="font-semibold mb-2">🔐 보안</h4>
                <ul className="list-disc list-inside space-y-1 text-blue-800">
                  <li>비밀번호는 로그인 시에만 사용되고 저장되지 않습니다</li>
                  <li>세션 데이터는 암호화되어 MongoDB에 안전하게 저장됩니다</li>
                  <li>HTTPS로 모든 통신이 암호화됩니다</li>
                </ul>
              </div>
              
              <div>
                <h4 className="font-semibold mb-2">⏰ 세션 유효 기간</h4>
                <ul className="list-disc list-inside space-y-1 text-blue-800">
                  <li>생성된 세션은 약 7일간 유효합니다</li>
                  <li>만료 1일 전에 알림을 받게 됩니다</li>
                  <li>만료 시 도구를 다시 실행하여 갱신하세요</li>
                </ul>
              </div>
              
              <div>
                <h4 className="font-semibold mb-2">❓ 문제 해결</h4>
                <ul className="list-disc list-inside space-y-1 text-blue-800">
                  <li>Windows Defender 경고: "추가 정보" → "실행" 클릭</li>
                  <li>2단계 인증: 2분 내에 휴대폰에서 인증 완료</li>
                  <li>실패 시: 프로그램을 다시 실행해보세요</li>
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Warning */}
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
          <div className="flex items-start">
            <Info className="w-5 h-5 text-yellow-600 mr-3 mt-0.5 flex-shrink-0" />
            <div>
              <h3 className="text-sm font-medium text-yellow-900">⚠️ 주의사항</h3>
              <p className="text-xs text-yellow-800 mt-1">
                네이버는 공식 리뷰 관리 API를 제공하지 않습니다. 
                이 기능은 웹 자동화를 사용하며, <strong>개인 사용 목적으로만</strong> 사용하시기 바랍니다.
              </p>
            </div>
          </div>
        </div>

        {/* Back Button */}
        <div className="text-center">
          <button
            onClick={() => navigate('/dashboard')}
            className="text-sm text-gray-600 hover:text-gray-900 transition-colors"
          >
            ← 대시보드로 돌아가기
          </button>
        </div>
      </div>
    </div>
  )
}




