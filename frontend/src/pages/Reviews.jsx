import React, { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import apiClient from '../api/client'
import ReviewCard from '../components/ReviewCard'
import { ChevronLeft, Filter, AlertCircle, Loader2 } from 'lucide-react'

export default function Reviews() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const platform = searchParams.get('platform') || 'gbp'
  const locationName = searchParams.get('location')
  const placeId = searchParams.get('place_id')

  const [filter, setFilter] = useState('all') // Start with 'all' - load everything at once
  const [naverPage, setNaverPage] = useState(1)
  
  // 🚀 Reset page to 1 when filter changes
  useEffect(() => {
    setNaverPage(1)
  }, [filter])
  const pageSize = 20
  const [loadingProgress, setLoadingProgress] = useState(0)
  const [estimatedTime, setEstimatedTime] = useState(25)
  
  // 🚀 NEW: Load count selection
  const [showLoadCountModal, setShowLoadCountModal] = useState(false)
  const [selectedLoadCount, setSelectedLoadCount] = useState(300) // Default: 300
  const [hasSelectedCount, setHasSelectedCount] = useState(false) // Track if user has chosen
  
  // 🚀 ASYNC Loading (타임아웃 우회)
  const [useAsyncLoading, setUseAsyncLoading] = useState(false)
  const [asyncTaskId, setAsyncTaskId] = useState(null)
  const [asyncProgress, setAsyncProgress] = useState(null)

  // Fetch GBP reviews
  const { data: gbpReviewsData, isLoading: gbpLoading, error: gbpError, refetch: refetchGBP } = useQuery({
    queryKey: ['gbp-reviews', locationName, filter],
    queryFn: async () => {
      const response = await apiClient.get('/api/gbp/reviews', {
        params: {
          location_name: locationName,
          filter: filter,
          page_size: 50
        }
      })
      return response.data
    },
    enabled: platform === 'gbp' && !!locationName,
    retry: false
  })

  // 🚀 Show load count modal for Naver (first time only)
  useEffect(() => {
    if (platform === 'naver' && placeId && !hasSelectedCount) {
      setShowLoadCountModal(true)
    }
  }, [platform, placeId, hasSelectedCount])

  // Get active user for cache key
  const activeNaverUser = localStorage.getItem('active_naver_user') || 'default'
  
  // 🚀 Naver reviews - 비동기만 사용 (동기 API 비활성화)
  const { data: naverReviewsData, isLoading: naverLoading, error: naverError, refetch: refetchNaver } = useQuery({
    queryKey: ['naver-reviews', placeId, naverPage, selectedLoadCount, activeNaverUser],
    queryFn: async () => {
      // 비동기 모드에서는 실행 안 됨 (비활성화됨)
      return []
    },
    enabled: false,  // 🚀 완전 비활성화 (비동기 API만 사용)
    retry: false
  })

  // Fetch location info
  const { data: locations } = useQuery({
    queryKey: ['locations'],
    queryFn: async () => {
      try {
        const response = await apiClient.get('/api/gbp/locations')
        return response.data
      } catch (err) {
        console.error('Failed to fetch locations:', err)
        return []
      }
    },
    enabled: platform === 'gbp',
    retry: false
  })

  // Fetch Naver places
  const { data: naverPlaces } = useQuery({
    queryKey: ['naverPlaces'],
    queryFn: async () => {
      try {
        const response = await apiClient.get('/api/naver/places')
        return response.data
      } catch (err) {
        console.error('Failed to fetch Naver places:', err)
        return []
      }
    },
    enabled: platform === 'naver',
    retry: false
  })

  // 🚀 Handle different data structures (including async result)
  let allReviewsData = platform === 'gbp' 
    ? gbpReviewsData 
    : (asyncProgress?.status === 'completed' && asyncProgress?.result)
      ? asyncProgress.result?.reviews || asyncProgress.result  // 비동기 로딩 완료 시
      : naverReviewsData?.reviews || naverReviewsData  // 동기 로딩
  
  // 🚀 NEW: Client-side filtering for Naver (backend returns ALL reviews)
  let filteredReviews = allReviewsData
  if (platform === 'naver' && allReviewsData && Array.isArray(allReviewsData)) {
    if (filter === 'unreplied') {
      filteredReviews = allReviewsData.filter(review => !review.has_reply)
    } else if (filter === 'replied') {
      filteredReviews = allReviewsData.filter(review => review.has_reply)
    } else {
      filteredReviews = allReviewsData  // 'all' = no filtering
    }
  }
  
  // 🚀 Client-side pagination for Naver (after filtering)
  let reviewsData = filteredReviews
  if (platform === 'naver' && filteredReviews && Array.isArray(filteredReviews)) {
    const startIdx = (naverPage - 1) * pageSize
    const endIdx = startIdx + pageSize
    reviewsData = filteredReviews.slice(startIdx, endIdx)
  }
  
  const totalReviews = platform === 'gbp'
    ? gbpReviewsData?.total_count
    : naverReviewsData?.total || (Array.isArray(allReviewsData) ? allReviewsData.length : 0)
  
  // 🚀 Calculate filter counts for Naver
  const filterCounts = {
    all: 0,
    unreplied: 0,
    replied: 0
  }
  
  if (platform === 'naver' && allReviewsData && Array.isArray(allReviewsData)) {
    filterCounts.all = allReviewsData.length
    filterCounts.unreplied = allReviewsData.filter(r => !r.has_reply).length
    filterCounts.replied = allReviewsData.filter(r => r.has_reply).length
  }
  
  const isLoading = platform === 'gbp' ? gbpLoading : naverLoading
  const error = platform === 'gbp' ? gbpError : naverError
  
  const currentLocation = platform === 'gbp'
    ? locations?.find(loc => loc.name === locationName)
    : naverPlaces?.find(place => place.place_id === placeId)

  // Removed real-time progress polling (simplified approach)

  // 🎨 Loading progress animation (aligned with actual loading time)
  useEffect(() => {
    if (isLoading && platform === 'naver') {
      setLoadingProgress(0)
      
      // 🚀 Realistic time estimate (based on actual testing + overhead)
      // Base overhead: cookies(3s) + page load(2s) + setup(2s) + parsing(3s) = 10s
      // Scroll speed: varies by count
      let estimatedTotal = 15
      if (selectedLoadCount <= 50) estimatedTotal = 15
      else if (selectedLoadCount <= 150) estimatedTotal = 30
      else if (selectedLoadCount <= 300) estimatedTotal = 50
      else if (selectedLoadCount <= 500) estimatedTotal = 70
      else if (selectedLoadCount <= 1000) estimatedTotal = 120 // 2 minutes
      else estimatedTotal = 240 // 4 minutes for "all"
      
      setEstimatedTime(estimatedTotal)
      
      const startTime = Date.now()
      const interval = setInterval(() => {
        const elapsed = (Date.now() - startTime) / 1000 // seconds
        const progress = Math.min(95, (elapsed / estimatedTotal) * 100) // Max 95% until complete
        const remaining = Math.max(0, Math.ceil(estimatedTotal - elapsed))
        
        setLoadingProgress(progress)
        setEstimatedTime(remaining)
        
        if (elapsed >= estimatedTotal + 5) { // Safety timeout
          clearInterval(interval)
        }
      }, 100)
      
      return () => clearInterval(interval)
    } else if (!isLoading) {
      setLoadingProgress(100)
      setEstimatedTime(0)
    }
  }, [isLoading, platform, naverPage])

  // 🚀 비동기 리뷰 로딩 시작
  const startAsyncLoading = async () => {
    try {
      const activeUser = localStorage.getItem('active_naver_user') || 'default'
      
      const response = await apiClient.post('/api/naver/reviews/load-async', {
        place_id: placeId,
        load_count: selectedLoadCount,
        user_id: activeUser
      })
      
      setAsyncTaskId(response.data.task_id)
      setUseAsyncLoading(true)
      
      console.log(`🚀 Async loading started: ${response.data.task_id}`)
    } catch (err) {
      console.error('Failed to start async loading:', err)
      alert('비동기 로딩 시작 실패: ' + (err.response?.data?.detail || err.message))
    }
  }
  
  // 🚀 작업 진행 상황 폴링
  const { data: taskStatus } = useQuery({
    queryKey: ['task-status', asyncTaskId],
    queryFn: async () => {
      if (!asyncTaskId) return null
      
      const response = await apiClient.get(`/api/naver/tasks/${asyncTaskId}`)
      const task = response.data
      
      console.log(`📊 Task progress: ${task.progress?.current || 0}/${task.progress?.total || 0} - ${task.status}`)
      
      setAsyncProgress(task)
      
      // 완료되면 폴링 중지하고 결과 표시
      if (task.status === 'completed' && task.result) {
        setUseAsyncLoading(false)
        setAsyncTaskId(null)
        // 결과를 캐시에 저장
        // (수동으로 naverReviewsData 업데이트하거나 refetch)
      }
      
      return task
    },
    enabled: !!asyncTaskId && useAsyncLoading,
    refetchInterval: 2000, // 2초마다 폴링
    retry: false
  })
  
  const handleReplyPosted = async () => {
    if (platform === 'gbp') {
      refetchGBP()
    } else {
      // For Naver, wait longer for cloud environment (Heroku needs more time)
      console.log('✅ 답글이 등록되었습니다. 잠시 후 새로고침합니다.')
      
      // Show success message immediately
      alert('✅ 답글이 성공적으로 등록되었습니다!')
      
      // Wait 3 seconds then refetch to get updated data
      setTimeout(() => {
        console.log('🔄 리뷰 목록을 새로고침합니다...')
        refetchNaver().catch(err => {
          console.warn('새로고침 중 오류 발생 (답글은 정상 등록됨):', err)
          // Even if refetch fails, the reply was posted successfully
        })
      }, 3000)
    }
  }

  if ((platform === 'gbp' && !locationName) || (platform === 'naver' && !placeId)) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">매장을 선택해주세요</p>
          <button
            onClick={() => navigate('/dashboard')}
            className="mt-4 text-blue-600 hover:text-blue-700"
          >
            대시보드로 돌아가기
          </button>
        </div>
      </div>
    )
  }

  // Load count options with realistic estimated times (including overhead)
  const loadCountOptions = [
    { count: 50, time: '~15초', desc: '최근 리뷰만 빠르게' },
    { count: 150, time: '~30초', desc: '최근 1-2개월 리뷰' },
    { count: 300, time: '~50초', desc: '균형잡힌 선택 (추천)' },
    { count: 500, time: '~70초', desc: '많은 리뷰 확인' },
    { count: 1000, time: '~2분', desc: '거의 모든 리뷰' },
    { count: 9999, time: '~3-5분', desc: '전체 (모든 리뷰)' }
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Load Count Selection Modal */}
      {showLoadCountModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-2xl w-full mx-4">
            <div className="text-center mb-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">🎯 리뷰 로딩 설정</h2>
              <p className="text-sm text-gray-600">
                몇 개의 리뷰를 불러올까요? 많을수록 시간이 더 걸립니다.
              </p>
            </div>
            
            <div className="space-y-3 mb-6">
              {loadCountOptions.map(option => (
                <button
                  key={option.count}
                  onClick={async () => {
                    console.log(`🔵 Option clicked: ${option.count}`)
                    setSelectedLoadCount(option.count)
                    setHasSelectedCount(true)
                    setShowLoadCountModal(false)
                    
                    // 🚀 즉시 비동기 로딩 시작
                    setTimeout(async () => {
                      console.log('🚀 Starting async loading from option button...')
                      try {
                        await startAsyncLoading()
                      } catch (err) {
                        console.error('❌ Async loading error:', err)
                        alert('리뷰 로딩 시작 실패')
                      }
                    }, 100)
                  }}
                  className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
                    selectedLoadCount === option.count
                      ? 'border-green-500 bg-green-50'
                      : 'border-gray-200 hover:border-green-300 hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3">
                        <span className="text-2xl font-bold text-gray-900">{option.count === 9999 ? '전체' : option.count + '개'}</span>
                        <span className="text-sm font-medium text-green-600">{option.time}</span>
                        {option.count === 300 && (
                          <span className="text-xs px-2 py-0.5 bg-green-500 text-white rounded-full">추천</span>
                        )}
                        {option.count === 50 && (
                          <span className="text-xs px-2 py-0.5 bg-blue-500 text-white rounded-full">가장 빠름</span>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 mt-1">{option.desc}</p>
                    </div>
                    <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                      selectedLoadCount === option.count
                        ? 'border-green-500 bg-green-500'
                        : 'border-gray-300'
                    }`}>
                      {selectedLoadCount === option.count && (
                        <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 12 12">
                          <path d="M10 3L4.5 8.5 2 6" stroke="currentColor" strokeWidth="2" fill="none"/>
                        </svg>
                      )}
                    </div>
                  </div>
                </button>
              ))}
            </div>
            
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
              <p className="text-xs text-blue-800">
                💡 <strong>팁:</strong> 한 번 불러온 리뷰는 캐시에 저장되어, 이후 필터/페이지 전환은 즉시 가능합니다!
              </p>
            </div>
            
            <button
              onClick={async () => {
                console.log('🔵 Button clicked!')
                console.log(`📦 Selected count: ${selectedLoadCount}`)
                console.log(`🏪 Place ID: ${placeId}`)
                
                setHasSelectedCount(true)
                setShowLoadCountModal(false)
                
                // 🚀 모든 로딩을 비동기로 (타임아웃 방지)
                console.log('🚀 Starting async loading...')
                
                try {
                  await startAsyncLoading()
                  console.log('✅ Async loading function completed')
                } catch (err) {
                  console.error('❌ Async loading error:', err)
                  alert('비동기 로딩 시작 실패: ' + err.message)
                }
              }}
              className="w-full bg-green-600 text-white py-3 rounded-lg font-semibold hover:bg-green-700 transition-colors"
            >
              {selectedLoadCount === 9999 ? '전체' : selectedLoadCount + '개'} 리뷰 불러오기 →
              <span className="text-xs ml-2">(안전한 비동기 모드)</span>
            </button>
          </div>
        </div>
      )}
      
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <button
                onClick={() => navigate('/dashboard')}
                className="mr-4 text-gray-600 hover:text-gray-900"
              >
                <ChevronLeft className="w-6 h-6" />
              </button>
              <div>
                <div className="flex items-center space-x-3">
                  <h1 className="text-2xl font-bold text-gray-900">
                    {platform === 'gbp' ? currentLocation?.location_name : currentLocation?.name || '리뷰 관리'}
                  </h1>
                  <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${
                    platform === 'gbp' 
                      ? 'bg-blue-100 text-blue-700' 
                      : 'bg-green-100 text-green-700'
                  }`}>
                    {platform === 'gbp' ? 'GBP' : '네이버'}
                  </span>
                </div>
                {currentLocation?.address && (
                  <p className="text-sm text-gray-600 mt-1">{currentLocation.address}</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Bar */}
        {reviewsData && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <p className="text-sm font-medium text-gray-600">총 리뷰</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">
                  {totalReviews || 0}
                </p>
                {platform === 'naver' && filteredReviews && filter !== 'all' && (
                  <p className="text-xs text-gray-500 mt-1">
                    (필터 결과: {filteredReviews.length}개)
                  </p>
                )}
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">평균 평점</p>
                <p className="text-3xl font-bold text-gray-900 mt-1">
                  {platform === 'gbp' 
                    ? (reviewsData.average_rating?.toFixed(1) || '-')
                    : '사용안함'
                  }
                </p>
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">필터</p>
                <div className="flex items-center space-x-2 mt-2">
                  <Filter className="w-4 h-4 text-gray-500" />
                  {platform === 'gbp' ? (
                    <select
                      value={filter}
                      onChange={(e) => setFilter(e.target.value)}
                      className="border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="all">전체 리뷰</option>
                      <option value="unreplied">미답변 리뷰</option>
                      <option value="replied">답변완료 리뷰</option>
                    </select>
                  ) : (
                    <select
                      value={filter}
                      onChange={(e) => setFilter(e.target.value)}
                      className="border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    >
                      <option value="all">전체 리뷰 {filterCounts.all > 0 && `(${filterCounts.all})`}</option>
                      <option value="unreplied">미답변 리뷰 {filterCounts.unreplied > 0 && `(${filterCounts.unreplied})`}</option>
                      <option value="replied">답변완료 리뷰 {filterCounts.replied > 0 && `(${filterCounts.replied})`}</option>
                    </select>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Reviews List */}
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-12 space-y-6">
            {/* Cute animated icon */}
            <div className="relative">
              <Loader2 className={`w-16 h-16 animate-spin ${
                platform === 'gbp' ? 'text-blue-600' : 'text-green-600'
              }`} />
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-2xl animate-bounce">📝</span>
              </div>
            </div>
            
            {/* Loading message */}
            <div className="text-center space-y-2">
              <h3 className="text-lg font-semibold text-gray-700">
                {platform === 'naver' ? `리뷰 ${selectedLoadCount === 9999 ? '전체' : selectedLoadCount + '개'} 불러오는 중...` : '리뷰를 불러오는 중...'}
              </h3>
              <p className="text-sm text-gray-500">
                {platform === 'naver' 
                  ? '스마트플레이스에서 리뷰를 수집하고 있어요...' 
                  : '잠시만 기다려주세요...'}
              </p>
            </div>
            
            {/* Progress bar for Naver */}
            {platform === 'naver' && (
              <div className="w-full max-w-md space-y-2">
                <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                  <div 
                    className="bg-gradient-to-r from-green-500 to-emerald-500 h-2 rounded-full transition-all duration-300 ease-out"
                    style={{ width: `${loadingProgress}%` }}
                  ></div>
                </div>
                <div className="flex justify-between text-xs text-gray-500">
                  <span>진행 중... {Math.round(loadingProgress)}%</span>
                  {estimatedTime > 0 && (
                    <span className="font-medium">⏱️ 약 {estimatedTime}초 남음</span>
                  )}
                </div>
              </div>
            )}
            
            {/* Why Naver Review Replies Matter - Cute Educational Content */}
            {platform === 'naver' && (
              <div className="bg-gradient-to-br from-green-50 to-emerald-50 border-2 border-green-200 rounded-2xl p-6 max-w-2xl shadow-sm">
                <div className="text-center mb-4">
                  <h4 className="text-lg font-bold text-green-800 flex items-center justify-center gap-2">
                    <span className="text-2xl">💚</span>
                    네이버 리뷰 답글이 중요한 이유
                    <span className="text-2xl">✨</span>
                  </h4>
                </div>
                
                <div className="space-y-4">
                  {/* Reason 1 */}
                  <div className="flex gap-3 items-start">
                    <div className="flex-shrink-0 w-8 h-8 bg-green-500 text-white rounded-full flex items-center justify-center font-bold text-sm">
                      1
                    </div>
                    <div>
                      <h5 className="font-semibold text-gray-800 mb-1">고객 신뢰를 빠르게 높입니다 🤝</h5>
                      <p className="text-sm text-gray-600">
                        답글이 있는 매장은 "관리 잘 되는 곳"이라는 인상을 줘서 첫 방문 장벽을 낮춰줘요.
                      </p>
                    </div>
                  </div>
                  
                  {/* Reason 2 */}
                  <div className="flex gap-3 items-start">
                    <div className="flex-shrink-0 w-8 h-8 bg-emerald-500 text-white rounded-full flex items-center justify-center font-bold text-sm">
                      2
                    </div>
                    <div>
                      <h5 className="font-semibold text-gray-800 mb-1">재방문과 충성도를 만듭니다 🔄</h5>
                      <p className="text-sm text-gray-600">
                        칭찬엔 감사 인사, 아쉬움엔 해결 의지를 보여주면 고객 경험이 훨씬 좋아집니다.
                      </p>
                    </div>
                  </div>
                  
                  {/* Reason 3 */}
                  <div className="flex gap-3 items-start">
                    <div className="flex-shrink-0 w-8 h-8 bg-teal-500 text-white rounded-full flex items-center justify-center font-bold text-sm">
                      3
                    </div>
                    <div>
                      <h5 className="font-semibold text-gray-800 mb-1">매장 '활동성' 신호로 노출에도 유리합니다 📈</h5>
                      <p className="text-sm text-gray-600">
                        꾸준한 소통은 리뷰 흐름을 건강하게 만들고, 다음 행동(저장/방문)을 자연스럽게 돕습니다.
                      </p>
                    </div>
                  </div>
                </div>
                
                {/* Bottom cute message */}
                <div className="mt-4 pt-4 border-t border-green-200 text-center">
                  <p className="text-xs text-green-700 font-medium">
                    💡 이 시스템으로 빠르고 쉽게 답글을 관리해보세요! 
                  </p>
                </div>
              </div>
            )}
          </div>
        ) : asyncProgress && asyncProgress.status !== 'completed' ? (
          /* 🚀 비동기 로딩 진행률 표시 */
          <div className="bg-gradient-to-br from-green-50 to-emerald-50 border-2 border-green-200 rounded-lg p-8">
            <div className="max-w-md mx-auto">
              <div className="text-center mb-6">
                <div className="animate-spin rounded-full h-12 w-12 border-b-3 border-green-600 mx-auto mb-4"></div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">
                  리뷰 로딩 중...
                </h3>
                <p className="text-sm text-gray-600">
                  {asyncProgress.progress?.message || '준비 중...'}
                </p>
              </div>
              
              {/* 진행률 바 */}
              <div className="mb-4">
                <div className="flex justify-between text-sm text-gray-700 mb-2">
                  <span>진행률</span>
                  <span className="font-semibold">
                    {asyncProgress.progress?.current || 0} / {asyncProgress.progress?.total || selectedLoadCount}
                    ({Math.round(((asyncProgress.progress?.current || 0) / (asyncProgress.progress?.total || selectedLoadCount)) * 100)}%)
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                  <div 
                    className="bg-gradient-to-r from-green-500 to-emerald-600 h-3 rounded-full transition-all duration-500"
                    style={{
                      width: `${Math.min(100, ((asyncProgress.progress?.current || 0) / (asyncProgress.progress?.total || selectedLoadCount)) * 100)}%`
                    }}
                  ></div>
                </div>
              </div>
              
              <div className="text-center text-xs text-gray-500">
                <p>타임아웃 걱정 없이 안전하게 로딩 중입니다</p>
                <p className="mt-1">잠시만 기다려주세요... ☕</p>
              </div>
            </div>
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
            <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-red-900 mb-2">리뷰를 불러올 수 없습니다</h3>
            <p className="text-red-700">{error.response?.data?.detail || error.message}</p>
          </div>
        ) : reviewsData && (platform === 'gbp' ? reviewsData.reviews?.length > 0 : Array.isArray(reviewsData) && reviewsData.length > 0) ? (
          <div className="space-y-4">
            {platform === 'gbp' 
              ? reviewsData.reviews.map((review) => (
                  <ReviewCard
                    key={review.review_id}
                    review={review}
                    platform="gbp"
                    locationName={locationName}
                    onReplyPosted={handleReplyPosted}
                  />
                ))
              : Array.isArray(reviewsData) && reviewsData.map((review) => (
                  <ReviewCard
                    key={review.review_id}
                    review={review}
                    platform="naver"
                    placeId={placeId}
                    onReplyPosted={handleReplyPosted}
                  />
                ))
            }
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
            {platform === 'naver' && filter === 'unreplied' && !isLoading ? (
              <div className="space-y-4">
                <div className="text-4xl animate-bounce">🎉</div>
                <h3 className="text-xl font-bold text-green-700">참 잘했어요!</h3>
                <p className="text-gray-600">
                  모든 리뷰에 답글을 작성하셨네요.<br/>
                  완벽한 고객 관리입니다! 👏
                </p>
                <button
                  onClick={() => setFilter('all')}
                  className="mt-4 px-6 py-2 bg-green-50 text-green-700 font-semibold rounded-full hover:bg-green-100 transition-colors"
                >
                  전체 리뷰 확인하기
                </button>
              </div>
            ) : (
              <>
                <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">리뷰가 없습니다</h3>
                <p className="text-gray-600">
                  {filter === 'unreplied' && '미답변 리뷰가 없습니다.'}
                  {filter === 'replied' && '답변완료 리뷰가 없습니다.'}
                  {filter === 'all' && '아직 작성된 리뷰가 없습니다.'}
                </p>
              </>
            )}
          </div>
        )}

        {/* Pagination for Naver */}
        {platform === 'naver' && reviewsData && Array.isArray(reviewsData) && reviewsData.length > 0 && (
          <div className="space-y-4">
            {/* Standard Pagination */}
            <div className="flex items-center justify-center space-x-2">
              <button
                onClick={() => setNaverPage(p => Math.max(1, p - 1))}
                disabled={naverPage === 1}
                className={`px-4 py-2 rounded-md ${
                  naverPage === 1
                    ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                }`}
              >
                이전
              </button>
            <span className="px-4 py-2 text-gray-700">
              페이지 {naverPage} {filteredReviews && `(전체 ${filteredReviews.length}개)`}
            </span>
            <button
              onClick={() => setNaverPage(p => p + 1)}
              disabled={!filteredReviews || naverPage * pageSize >= filteredReviews.length}
              className={`px-4 py-2 rounded-md ${
                (!filteredReviews || naverPage * pageSize >= filteredReviews.length)
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
              }`}
            >
              다음
            </button>
            </div>
            
            {/* "Load More" hint when approaching cache limit */}
            {reviewsData.length === pageSize && naverPage >= 14 && (
              <div className="text-center">
                <p className="text-xs text-gray-500 mb-2">
                  💡 더 많은 리뷰를 보려면 계속 페이지를 넘겨주세요. 
                  필요 시 자동으로 추가 로딩됩니다.
                </p>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  )
}




