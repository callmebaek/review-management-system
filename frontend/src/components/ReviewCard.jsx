import React, { useState, useEffect } from 'react'
import { Star, User, Calendar, MessageSquare, Sparkles } from 'lucide-react'
import apiClient from '../api/client'
import { useQueryClient, useQuery } from '@tanstack/react-query'

export default function ReviewCard({ review, reviewIndex, platform = 'gbp', locationName, placeId, onReplyPosted }) {
  const queryClient = useQueryClient()
  const [showReplyForm, setShowReplyForm] = useState(false)
  const [replyText, setReplyText] = useState('')
  const [generating, setGenerating] = useState(false)
  const [posting, setPosting] = useState(false)
  const [error, setError] = useState(null)
  
  // 🚀 비동기 답글 게시
  const [replyTaskId, setReplyTaskId] = useState(null)
  const [replyProgress, setReplyProgress] = useState(null)
  
  // 🎯 로컬 상태: 답글 게시 완료 여부 (낙관적 업데이트)
  const [localHasReply, setLocalHasReply] = useState(false)

  const isNaver = platform === 'naver'
  // 🎯 서버 데이터 또는 로컬 상태 확인
  const hasReply = localHasReply || (isNaver ? !!review.has_reply : !!review.review_reply)
  
  // 🚀 답글 게시 작업 상태 폴링
  const { data: replyTaskStatus } = useQuery({
    queryKey: ['reply-task', replyTaskId],
    queryFn: async () => {
      if (!replyTaskId) return null
      
      const response = await apiClient.get(`/api/naver/tasks/${replyTaskId}`)
      const task = response.data
      
      console.log(`📊 Reply task status: ${task.status}, progress: ${task.progress?.message}`)
      
      setReplyProgress(task)
      
      // 🚀 KEEP posting true until completed or failed
      if (task.status === 'completed') {
        console.log('✅ Reply task completed!')
        
        // 🎯 즉시 UI 업데이트 (낙관적 업데이트)
        setLocalHasReply(true)
        
        // 🚀 성공 알림 표시
        alert('✅ 답글이 성공적으로 게시되었습니다!')
        
        setPosting(false)
        setReplyTaskId(null)
        setShowReplyForm(false)
        setReplyText('')
        
        // 🚀 백그라운드에서 캐시 무효화 (UI는 이미 업데이트됨)
        if (isNaver && placeId) {
          console.log(`🔄 Invalidating cache for place: ${placeId}`)
          queryClient.invalidateQueries(['naver-reviews'])
        }
        
        if (onReplyPosted) {
          onReplyPosted()
        }
      } else if (task.status === 'failed') {
        console.log('❌ Reply task failed:', task.error)
        setPosting(false)
        setReplyTaskId(null)
        setError(task.error || '답글 게시 실패')
      } else {
        // 🚀 진행 중이면 posting 유지
        if (!posting) {
          console.log('🔄 Setting posting to true (task in progress)')
          setPosting(true)
        }
      }
      
      return task
    },
    enabled: !!replyTaskId,
    refetchInterval: 2000,  // 2초마다 폴링
    retry: false
  })

  const getRatingStars = (rating) => {
    // Naver: rating is a number (1-5)
    // GBP: rating is a string ('ONE', 'TWO', etc.)
    let count = 0
    if (isNaver) {
      count = rating || 0
    } else {
      const ratingMap = { 'ONE': 1, 'TWO': 2, 'THREE': 3, 'FOUR': 4, 'FIVE': 5 }
      count = ratingMap[rating] || 0
    }
    
    return Array(5).fill(0).map((_, i) => (
      <Star
        key={i}
        className={`w-4 h-4 ${i < count ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'}`}
      />
    ))
  }

  const getRatingNumber = (rating) => {
    if (isNaver) return rating || 0
    const ratingMap = { 'ONE': 1, 'TWO': 2, 'THREE': 3, 'FOUR': 4, 'FIVE': 5 }
    return ratingMap[rating] || 0
  }

  const formatDate = (dateString) => {
    if (isNaver) {
      // Naver date format: "2025.01.08"
      return dateString
    }
    // GBP date format: ISO string
    const date = new Date(dateString)
    return date.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  const handleGenerateReply = async () => {
    try {
      setGenerating(true)
      setError(null)

      const reviewText = isNaver ? review.content : review.comment
      // Naver reviews don't have ratings, so use default value 3 (neutral)
      const rating = isNaver ? (review.rating || 3) : getRatingNumber(review.star_rating)

      const response = await apiClient.post('/api/reviews/generate-reply', {
        review_text: reviewText,
        rating: rating,
        store_name: locationName || null,
        custom_instructions: null
      })

      setReplyText(response.data.generated_reply)
      setGenerating(false)
    } catch (err) {
      console.error('Generate reply error:', err)
      const errorMsg = err.response?.data?.detail 
        ? (typeof err.response.data.detail === 'string' 
          ? err.response.data.detail 
          : JSON.stringify(err.response.data.detail))
        : '답글 생성 중 오류가 발생했습니다'
      setError(errorMsg)
      setGenerating(false)
    }
  }

  const handlePostReply = async () => {
    if (!replyText.trim()) {
      setError('답글 내용을 입력해주세요')
      return
    }
    
    // 🚀 이미 게시 중이면 중복 방지
    if (posting || replyTaskId) {
      console.warn('⚠️ Already posting reply, please wait...')
      alert('이미 답글을 게시하고 있습니다. 잠시만 기다려주세요.')
      return
    }

    try {
      setPosting(true)
      setError(null)

      const currentReplyText = replyText
      const currentDate = new Date().toISOString().split('T')[0].replace(/-/g, '.')
      
      // 🚀 네이버는 비동기 방식 사용 (타임아웃 우회)
      if (isNaver) {
        // Get active user from localStorage (for multi-account support)
        const activeUser = localStorage.getItem('active_naver_user') || 'default'
        
        // 비동기 답글 게시 시작 (작성자 + 날짜 + 내용 3중 매칭)
        const reviewContent = review.content || ""
        
        const response = await apiClient.post('/api/naver/reviews/reply-async', {
          place_id: placeId,
          author: review.author,
          date: review.date,
          content: reviewContent,
          reply_text: currentReplyText,
          user_id: activeUser,
          expected_review_count: 50  // 기본값 50
        })
        
        // 작업 ID 저장하고 폴링 시작
        setReplyTaskId(response.data.task_id)
        // posting은 true 유지 (폴링에서 false로 변경)
        
        return // 폴링이 완료를 처리함
      } else {
        await apiClient.post('/api/gbp/reviews/reply', {
          review_id: review.review_id,
          reply_text: currentReplyText,
          location_name: locationName || review.name.split('/reviews/')[0]
        })
        
        // 🎯 GBP 답글 게시 성공 시 즉시 UI 업데이트
        setLocalHasReply(true)
        alert('✅ 답글이 성공적으로 게시되었습니다!')
      }
      
      // 🚀 SUCCESS: Now close form and update UI
      setShowReplyForm(false)
      setReplyText('')
      
      // Update the review object in cache (optimistic)
      if (isNaver && placeId) {
        // Invalidate all related caches (simpler and more reliable)
        queryClient.invalidateQueries(['naver-reviews', placeId])
      } else {
        // GBP cache invalidation
        queryClient.invalidateQueries(['gbp-reviews'])
      }
      
      if (onReplyPosted) {
        onReplyPosted()
      }
    } catch (err) {
      // Keep form open on error
      const errorMsg = err.response?.data?.detail || '답글 게시 중 오류가 발생했습니다'
      setError(errorMsg)
      alert(`❌ 답글 게시 실패: ${errorMsg}`)
    } finally {
      setPosting(false)
    }
  }

  const reviewerName = isNaver ? review.author : review.reviewer?.display_name
  const reviewerPhoto = isNaver ? null : review.reviewer?.profile_photo_url
  const rating = isNaver ? review.rating : review.star_rating
  const reviewDate = isNaver ? review.date : review.create_time
  const reviewContent = isNaver ? review.content : review.comment
  const existingReply = isNaver ? review.reply : review.review_reply?.comment
  const replyDate = isNaver ? review.reply_date : review.review_reply?.update_time

  return (
    <div className={`bg-white rounded-lg shadow-sm border p-6 ${
      isNaver ? 'border-green-200' : 'border-gray-200'
    }`}>
      {/* Reviewer Info */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center">
          <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center">
            {reviewerPhoto ? (
              <img
                src={reviewerPhoto}
                alt={reviewerName}
                className="w-10 h-10 rounded-full"
              />
            ) : (
              <User className="w-5 h-5 text-gray-500" />
            )}
          </div>
          <div className="ml-3">
            <p className="font-medium text-gray-900">{reviewerName}</p>
            {/* 네이버는 평점 표시 안 함 */}
            {!isNaver && (
              <div className="flex items-center mt-1">
                {getRatingStars(rating)}
              </div>
            )}
          </div>
        </div>
        <div className="flex items-center text-sm text-gray-500">
          <Calendar className="w-4 h-4 mr-1" />
          {formatDate(reviewDate)}
        </div>
      </div>

      {/* Review Comment */}
      {reviewContent && (
        <p className="text-gray-700 mb-4 whitespace-pre-wrap">{reviewContent}</p>
      )}

      {/* Existing Reply */}
      {hasReply && existingReply && (
        <div className={`border rounded-lg p-4 mb-4 ${
          isNaver 
            ? 'bg-green-50 border-green-100' 
            : 'bg-blue-50 border-blue-100'
        }`}>
          <div className="flex items-start">
            <MessageSquare className={`w-4 h-4 mr-2 mt-1 ${
              isNaver ? 'text-green-600' : 'text-blue-600'
            }`} />
            <div className="flex-1">
              <p className={`text-sm font-medium mb-1 ${
                isNaver ? 'text-green-900' : 'text-blue-900'
              }`}>사장님 답글</p>
              <p className="text-sm text-gray-700">{existingReply}</p>
              {replyDate && (
                <p className="text-xs text-gray-500 mt-2">
                  {formatDate(replyDate)}
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Reply Actions */}
      {!hasReply ? (
        <>
          {!showReplyForm ? (
            <button
              onClick={() => setShowReplyForm(true)}
              className={`w-full py-2 px-4 border rounded-md font-medium ${
                isNaver
                  ? 'border-green-600 text-green-600 hover:bg-green-50'
                  : 'border-blue-600 text-blue-600 hover:bg-blue-50'
              }`}
            >
              답글 작성
            </button>
          ) : (
            <div className="space-y-3">
              {/* 🚀 답글 게시 중 알림 (명확하게) */}
              {posting && (
                <div className="bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-300 rounded-lg p-4 animate-pulse">
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-green-600 mr-3"></div>
                    <div>
                      <p className="text-sm font-semibold text-green-900">
                        {replyProgress?.progress?.message || '답글 게시 중...'}
                      </p>
                      <p className="text-xs text-green-700 mt-1">
                        타임아웃 걱정 없이 안전하게 처리하고 있습니다 ☕
                      </p>
                    </div>
                  </div>
                </div>
              )}
              
              {error && (
                <div className="bg-red-50 border border-red-200 rounded-md p-3">
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              )}

              <textarea
                value={replyText}
                onChange={(e) => setReplyText(e.target.value)}
                placeholder="답글을 입력하거나 AI로 생성하세요..."
                className={`w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:border-transparent resize-none ${
                  isNaver ? 'focus:ring-green-500' : 'focus:ring-blue-500'
                }`}
                rows={4}
              />

              <div className="flex items-center space-x-3">
                <button
                  onClick={handleGenerateReply}
                  disabled={generating}
                  className="flex-1 py-2 px-4 bg-purple-600 hover:bg-purple-700 disabled:bg-purple-400 text-white rounded-md font-medium flex items-center justify-center"
                >
                  {generating ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      생성 중...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4 mr-2" />
                      AI 답글 생성
                    </>
                  )}
                </button>

                <button
                  onClick={handlePostReply}
                  disabled={posting || !replyText.trim()}
                  className={`flex-1 py-2 px-4 text-white rounded-md font-medium flex items-center justify-center ${
                    isNaver
                      ? 'bg-green-600 hover:bg-green-700 disabled:bg-green-400'
                      : 'bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400'
                  }`}
                >
                  {posting ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      {replyProgress?.progress?.message || '답글 게시 중...'}
                    </>
                  ) : (
                    '답글 게시'
                  )}
                </button>

                <button
                  onClick={() => {
                    setShowReplyForm(false)
                    setReplyText('')
                    setError(null)
                  }}
                  className="py-2 px-4 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
                >
                  취소
                </button>
              </div>
            </div>
          )}
        </>
      ) : (
        // 🎯 답글 게시 완료 상태 표시
        <button
          disabled
          className="w-full py-2 px-4 border-2 rounded-md font-medium bg-gray-100 border-gray-300 text-gray-500 cursor-not-allowed flex items-center justify-center"
        >
          <MessageSquare className="w-4 h-4 mr-2" />
          답글 완료
        </button>
      )}
    </div>
  )
}




