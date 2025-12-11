import React, { useState, useEffect } from 'react'
import { Star, User, Calendar, MessageSquare, Sparkles } from 'lucide-react'
import apiClient from '../api/client'
import { useQueryClient, useQuery } from '@tantml:react-query'

export default function ReviewCard({ review, platform = 'gbp', locationName, placeId, onReplyPosted }) {
  const queryClient = useQueryClient()
  const [showReplyForm, setShowReplyForm] = useState(false)
  const [replyText, setReplyText] = useState('')
  const [generating, setGenerating] = useState(false)
  const [posting, setPosting] = useState(false)
  const [error, setError] = useState(null)
  
  // 🚀 비동기 답글 게시
  const [replyTaskId, setReplyTaskId] = useState(null)
  const [replyProgress, setReplyProgress] = useState(null)

  const isNaver = platform === 'naver'
  const hasReply = isNaver ? !!review.has_reply : !!review.review_reply
  
  // 🚀 답글 게시 작업 상태 폴링
  const { data: replyTaskStatus } = useQuery({
    queryKey: ['reply-task', replyTaskId],
    queryFn: async () => {
      if (!replyTaskId) return null
      
      const response = await apiClient.get(`/api/naver/tasks/${replyTaskId}`)
      const task = response.data
      
      setReplyProgress(task)
      
      // 완료되면 폴링 중지
      if (task.status === 'completed') {
        setPosting(false)
        setReplyTaskId(null)
        setShowReplyForm(false)
        setReplyText('')
        
        // 캐시 무효화
        if (isNaver && placeId) {
          queryClient.invalidateQueries(['naver-reviews', placeId])
        }
        
        if (onReplyPosted) {
          onReplyPosted()
        }
      } else if (task.status === 'failed') {
        setPosting(false)
        setReplyTaskId(null)
        setError(task.error || '답글 게시 실패')
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

    try {
      setPosting(true)
      setError(null)

      const currentReplyText = replyText
      const currentDate = new Date().toISOString().split('T')[0].replace(/-/g, '.')
      
      // 🚀 네이버는 비동기 방식 사용 (타임아웃 우회)
      if (isNaver) {
        // Get active user from localStorage (for multi-account support)
        const activeUser = localStorage.getItem('active_naver_user') || 'default'
        
        // 비동기 답글 게시 시작
        const response = await apiClient.post('/api/naver/reviews/reply-async', {
          place_id: placeId,
          review_id: review.review_id,
          reply_text: currentReplyText,
          user_id: activeUser
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
      }
      
      // 🚀 SUCCESS: Now close form and update UI
      setShowReplyForm(false)
      setReplyText('')
      
      // Update the review object in cache (optimistic)
      if (isNaver && placeId) {
        // Get active user to match cache key
        const activeUser = localStorage.getItem('active_naver_user') || 'default'
        
        // Invalidate all related caches (simpler and more reliable)
        queryClient.invalidateQueries(['naver-reviews', placeId])
      }
      
      // Show success alert
      alert('✅ 답글이 성공적으로 게시되었습니다!')
      
      // Verify after 3 seconds (silent background check)
      setTimeout(() => {
        if (isNaver && placeId) {
          queryClient.invalidateQueries(['naver-reviews', placeId])
        }
      }, 3000)
      
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
      {!hasReply && (
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
      )}
    </div>
  )
}




