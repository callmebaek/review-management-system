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
    
    // DISABLED: OAuth callback 처리 (not working)
    /*
    const urlParams = new URLSearchParams(window.location.search)
    const success = urlParams.get('success')
    const error = urlParams.get('error')
    
    if (success === 'true') {
      // OAuth 로그인 성공!
      setTimeout(() => {
        loadSessions()  // 세션 목록 새로고침
      }, 1000)
      
      // URL에서 파라미터 제거
      window.history.replaceState({}, document.title, window.location.pathname)
    } else if (error) {
      setError(`OAuth 로그인 실패: ${decodeURIComponent(error)}`)
      // URL에서 파라미터 제거
      window.history.replaceState({}, document.title, window.location.pathname)
    }
    */
  }, [])
  
  // 🚀 페이지가 보일 때마다 localStorage 동기화
  useEffect(() => {
    const syncActiveSession = () => {
      const storedActiveUser = localStorage.getItem('active_naver_user')
      if (storedActiveUser && storedActiveUser !== activeSession) {
        console.log(`🔄 Syncing active session: ${activeSession} → ${storedActiveUser}`)
        setActiveSession(storedActiveUser)
      }
    }
    
    // 페이지 포커스 시 동기화
    window.addEventListener('focus', syncActiveSession)
    
    // 컴포넌트 마운트 시에도 한 번 실행
    syncActiveSession()
    
    return () => {
      window.removeEventListener('focus', syncActiveSession)
    }
  }, [activeSession])

  const loadSessions = async () => {
    try {
      setLoading(true)
      
      // 🚀 현재 로그인한 Google 계정의 세션만 조회
      const googleEmail = localStorage.getItem('google_email') || null
      const params = googleEmail ? { google_email: googleEmail } : {}
      
      const response = await apiClient.get('/api/naver/sessions/list', { params, timeout: 5000 })
      setSessions(response.data.sessions || [])
      
      // 🚀 localStorage에서 현재 활성 계정 읽기 (우선순위 1)
      const storedActiveUser = localStorage.getItem('active_naver_user')
      
      if (response.data.sessions && response.data.sessions.length > 0) {
        // 저장된 활성 계정이 있고, 세션 목록에 존재하면 사용
        if (storedActiveUser && response.data.sessions.some(s => s.user_id === storedActiveUser)) {
          console.log(`🔄 Using stored active user: ${storedActiveUser}`)
          setActiveSession(storedActiveUser)
        } else {
          // 없으면 첫 번째 세션 사용
          const active = response.data.sessions.find(s => s.user_id === 'default') || response.data.sessions[0]
          console.log(`🔄 Setting default active user: ${active.user_id}`)
          setActiveSession(active.user_id)
          localStorage.setItem('active_naver_user', active.user_id)
        }
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
      
      // 🚀 STEP 1: localStorage 업데이트
      localStorage.setItem('active_naver_user', user_id)
      console.log(`🔄 localStorage updated to: ${user_id}`)
      
      // 🚀 STEP 2: 모든 캐시 완전 제거
      queryClient.clear()
      console.log('🗑️ All cache cleared')
      
      setActiveSession(user_id)
      
      alert(`✅ ${user_id} 계정으로 전환되었습니다!`)
      
      // 🚀 STEP 3: URL 파라미터로 user_id 전달하여 이동
      setTimeout(() => {
        window.location.href = `/dashboard?switched_user=${encodeURIComponent(user_id)}&_t=${Date.now()}`
      }, 300)
    } catch (err) {
      console.error('Account switch error:', err)
      alert('계정 전환 중 오류가 발생했습니다')
    }
  }

  const handleDeleteSession = async (user_id) => {
    // 🔐 현재 로그인한 구글 계정 정보
    const googleEmail = localStorage.getItem('google_email')
    const googleName = localStorage.getItem('google_name') || googleEmail
    
    if (!confirm(
      `'${user_id}' 세션에서 연결을 해제하시겠습니까?\n\n` +
      `현재 계정: ${googleName}\n` +
      `- 다른 사용자가 이 세션을 공유 중이면 본인만 연결 해제됩니다.\n` +
      `- 본인만 사용 중이면 세션이 완전히 삭제됩니다.`
    )) {
      return
    }
    
    try {
      setLoading(true)
      const response = await apiClient.delete(`/api/naver/session?user_id=${user_id}`)
      
      // 🎯 백엔드 응답에 따라 다른 메시지 표시
      if (response.data.action === 'deleted') {
        // 세션 완전 삭제됨
        alert(`✅ 세션이 완전히 삭제되었습니다.\n다시 사용하려면 EXE로 세션을 재생성하세요.`)
      } else if (response.data.action === 'disconnected') {
        // 본인만 연결 해제됨
        alert(
          `✅ 연결이 해제되었습니다.\n\n` +
          `다른 사용자 ${response.data.remaining_users}명은 계속 이 세션을 사용할 수 있습니다.`
        )
      }
      
      // Reload sessions
      await loadSessions()
      
      // 🔄 삭제한 세션이 활성 세션이었다면 초기화
      if (activeSession === user_id) {
        localStorage.removeItem('active_naver_user')
        setActiveSession(null)
      }
      
      setError(null)
    } catch (err) {
      console.error('세션 삭제 오류:', err)
      const errorMsg = err.response?.data?.detail || '세션 삭제 중 오류가 발생했습니다'
      setError(errorMsg)
      alert(`❌ ${errorMsg}`)
    } finally {
      setLoading(false)
    }
  }

  // DISABLED: OAuth login not working
  /*
  const handleOAuthLogin = async () => {
    try {
      const googleEmail = localStorage.getItem('google_email')
      
      // OAuth URL 요청
      const response = await apiClient.get('/api/naver/oauth/login', {
        params: { google_email: googleEmail }
      })
      
      // OAuth 페이지로 리다이렉트
      window.location.href = response.data.oauth_url
      
    } catch (err) {
      console.error('OAuth login error:', err)
      setError(err.response?.data?.detail || 'OAuth 로그인 시작 실패')
    }
  }
  */

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

        {/* OAuth Login Section (DISABLED - Not working) */}
        {/* 
        <div className="bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-300 rounded-lg p-6 mb-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-semibold text-gray-900">🚀 간편 로그인 (추천!)</h3>
            <span className="bg-green-100 text-green-800 text-xs font-semibold px-2.5 py-0.5 rounded">NEW</span>
          </div>
          
          <p className="text-sm text-gray-700 mb-4">
            네이버 계정으로 바로 로그인하세요. EXE 다운로드 없이 웹에서 바로 완료됩니다!
          </p>
          
          <div className="bg-white rounded-lg p-4 mb-4 space-y-2 text-sm text-gray-600">
            <div className="flex items-start">
              <span className="font-bold text-green-600 mr-2">✓</span>
              <span>EXE 다운로드 불필요 - 웹에서 바로 로그인</span>
            </div>
            <div className="flex items-start">
              <span className="font-bold text-green-600 mr-2">✓</span>
              <span>자동 갱신 - 세션 만료 걱정 없음</span>
            </div>
            <div className="flex items-start">
              <span className="font-bold text-green-600 mr-2">✓</span>
              <span>모든 플랫폼 지원 - Windows/Mac/Linux</span>
            </div>
          </div>
          
          <button
            onClick={handleOAuthLogin}
            className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-4 px-4 rounded-lg flex items-center justify-center space-x-2 transition-all transform hover:scale-105 shadow-lg"
          >
            <CheckCircle className="w-6 h-6" />
            <span>네이버로 로그인하기</span>
          </button>
          
          <p className="text-xs text-gray-500 mt-3 text-center">
            OAuth 2.0 인증 | 안전하고 빠름 | 2단계 인증 필요
          </p>
        </div>
        */}

        {/* Download Tool Section */}
        <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border-2 border-indigo-200 rounded-lg p-6 mb-6">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-semibold text-gray-900">💻 세션 생성 도구</h3>
            <span className="bg-gray-100 text-gray-600 text-xs font-semibold px-2.5 py-0.5 rounded">기존 방식</span>
          </div>
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




