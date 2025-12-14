import React, { useState, useEffect } from 'react'
import { X, Save, RotateCcw } from 'lucide-react'
import apiClient from '../api/client'

export default function AISettingsModal({ isOpen, onClose, placeId, placeName }) {
  const [activeTab, setActiveTab] = useState('basic')
  const [settings, setSettings] = useState({
    friendliness: 7,
    formality: 7,
    reply_length_min: 100,
    reply_length_max: 450,
    diversity: 0.9,
    use_text_emoticons: true,
    mention_specifics: true,
    brand_voice: 'warm',
    response_style: 'quick_thanks',
    custom_instructions: ''
  })
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [isDefault, setIsDefault] = useState(true)

  // Load settings when modal opens
  useEffect(() => {
    if (isOpen && placeId) {
      loadSettings()
    }
  }, [isOpen, placeId])

  const loadSettings = async () => {
    try {
      setLoading(true)
      const response = await apiClient.get(`/api/naver/places/${placeId}/ai-settings`)
      setSettings(response.data.settings)
      setIsDefault(response.data.is_default || false)
    } catch (error) {
      console.error('Failed to load AI settings:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    try {
      setSaving(true)
      await apiClient.put(`/api/naver/places/${placeId}/ai-settings`, settings)
      alert('✅ AI 답글 설정이 저장되었습니다!')
      setIsDefault(false)
      onClose()
    } catch (error) {
      console.error('Failed to save AI settings:', error)
      alert('❌ 설정 저장에 실패했습니다. 다시 시도해주세요.')
    } finally {
      setSaving(false)
    }
  }

  const handleReset = async () => {
    if (confirm('기본 설정으로 되돌리시겠습니까?')) {
      setSettings({
        friendliness: 7,
        formality: 7,
        reply_length_min: 100,
        reply_length_max: 450,
        diversity: 0.9,
        use_text_emoticons: true,
        mention_specifics: true,
        brand_voice: 'warm',
        response_style: 'quick_thanks',
        custom_instructions: ''
      })
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-600 to-indigo-600 px-6 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-white">AI 답글 생성 설정</h2>
            <p className="text-purple-100 text-sm mt-1">{placeName || `매장 ID: ${placeId}`}</p>
            {isDefault && (
              <span className="inline-block mt-2 px-2 py-1 bg-yellow-400 text-yellow-900 text-xs rounded">
                기본값 사용 중
              </span>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-white hover:bg-white hover:bg-opacity-20 p-2 rounded-lg transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 px-6">
          <div className="flex space-x-1">
            <button
              onClick={() => setActiveTab('basic')}
              className={`px-4 py-3 font-medium text-sm border-b-2 transition ${
                activeTab === 'basic'
                  ? 'border-purple-600 text-purple-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              기본 설정
            </button>
            <button
              onClick={() => setActiveTab('advanced')}
              className={`px-4 py-3 font-medium text-sm border-b-2 transition ${
                activeTab === 'advanced'
                  ? 'border-purple-600 text-purple-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              고급 설정
            </button>
            <button
              onClick={() => setActiveTab('custom')}
              className={`px-4 py-3 font-medium text-sm border-b-2 transition ${
                activeTab === 'custom'
                  ? 'border-purple-600 text-purple-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              추가 요청사항
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="px-6 py-6 overflow-y-auto" style={{ maxHeight: 'calc(90vh - 200px)' }}>
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
            </div>
          ) : (
            <>
              {/* Basic Settings Tab */}
              {activeTab === 'basic' && (
                <div className="space-y-6">
                  {/* Friendliness */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      친절함 정도 <span className="text-purple-600 font-bold">{settings.friendliness}</span>/10
                    </label>
                    <input
                      type="range"
                      min="1"
                      max="10"
                      value={settings.friendliness}
                      onChange={(e) => setSettings({ ...settings, friendliness: parseInt(e.target.value) })}
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-purple-600"
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>정중하게</span>
                      <span>친절하게</span>
                      <span>매우 따뜻하게</span>
                    </div>
                  </div>

                  {/* Formality */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      격식 수준 <span className="text-purple-600 font-bold">{settings.formality}</span>/10
                    </label>
                    <input
                      type="range"
                      min="1"
                      max="10"
                      value={settings.formality}
                      onChange={(e) => setSettings({ ...settings, formality: parseInt(e.target.value) })}
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-purple-600"
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>반말</span>
                      <span>자연스러운 존댓말</span>
                      <span>격식있는 존댓말</span>
                    </div>
                  </div>

                  {/* Reply Length */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      답글 길이
                    </label>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-xs text-gray-600 mb-1">최소</label>
                        <input
                          type="number"
                          min="50"
                          max="450"
                          value={settings.reply_length_min}
                          onChange={(e) => setSettings({ ...settings, reply_length_min: parseInt(e.target.value) })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-600 mb-1">최대</label>
                        <input
                          type="number"
                          min="50"
                          max="450"
                          value={settings.reply_length_max}
                          onChange={(e) => setSettings({ ...settings, reply_length_max: parseInt(e.target.value) })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                        />
                      </div>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      {settings.reply_length_min}~{settings.reply_length_max}자 범위로 답글이 생성됩니다
                    </p>
                  </div>

                  {/* Text Emoticons Toggle */}
                  <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        텍스트 이모티콘 사용
                      </label>
                      <p className="text-xs text-gray-500 mt-1">^^, ㅎㅎ, :) 등</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={settings.use_text_emoticons}
                        onChange={(e) => setSettings({ ...settings, use_text_emoticons: e.target.checked })}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                    </label>
                  </div>

                  {/* Mention Specifics Toggle */}
                  <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">
                        리뷰 구체 내용 언급
                      </label>
                      <p className="text-xs text-gray-500 mt-1">맛, 분위기, 서비스 등</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={settings.mention_specifics}
                        onChange={(e) => setSettings({ ...settings, mention_specifics: e.target.checked })}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-purple-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
                    </label>
                  </div>
                </div>
              )}

              {/* Advanced Settings Tab */}
              {activeTab === 'advanced' && (
                <div className="space-y-6">
                  {/* Diversity */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      다양성 강도 <span className="text-purple-600 font-bold">{settings.diversity.toFixed(1)}</span>
                    </label>
                    <input
                      type="range"
                      min="0.5"
                      max="1.0"
                      step="0.1"
                      value={settings.diversity}
                      onChange={(e) => setSettings({ ...settings, diversity: parseFloat(e.target.value) })}
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-purple-600"
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>일관적</span>
                      <span>균형</span>
                      <span>창의적</span>
                    </div>
                    <p className="text-xs text-gray-600 mt-2 bg-blue-50 p-2 rounded">
                      💡 높을수록 매번 다른 스타일의 답글이 생성됩니다
                    </p>
                  </div>

                  {/* Brand Voice */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      브랜드 톤
                    </label>
                    <div className="grid grid-cols-2 gap-3">
                      {[
                        { value: 'warm', label: '따뜻한', emoji: '🤗' },
                        { value: 'professional', label: '전문적인', emoji: '💼' },
                        { value: 'casual', label: '캐주얼한', emoji: '😎' },
                        { value: 'friendly', label: '친근한', emoji: '😊' }
                      ].map((option) => (
                        <button
                          key={option.value}
                          onClick={() => setSettings({ ...settings, brand_voice: option.value })}
                          className={`p-3 border-2 rounded-lg transition ${
                            settings.brand_voice === option.value
                              ? 'border-purple-600 bg-purple-50'
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                        >
                          <div className="text-2xl mb-1">{option.emoji}</div>
                          <div className="text-sm font-medium">{option.label}</div>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Response Style */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      응답 스타일
                    </label>
                    <div className="space-y-2">
                      {[
                        { value: 'quick_thanks', label: '신속한 감사', desc: '빠르게 감사 표현' },
                        { value: 'empathy', label: '공감 중심', desc: '고객의 경험에 공감' },
                        { value: 'solution', label: '해결책 제시', desc: '개선 의지 표현' }
                      ].map((option) => (
                        <label
                          key={option.value}
                          className={`flex items-center p-3 border-2 rounded-lg cursor-pointer transition ${
                            settings.response_style === option.value
                              ? 'border-purple-600 bg-purple-50'
                              : 'border-gray-200 hover:border-gray-300'
                          }`}
                        >
                          <input
                            type="radio"
                            name="response_style"
                            value={option.value}
                            checked={settings.response_style === option.value}
                            onChange={(e) => setSettings({ ...settings, response_style: e.target.value })}
                            className="mr-3 text-purple-600 focus:ring-purple-500"
                          />
                          <div>
                            <div className="font-medium text-sm">{option.label}</div>
                            <div className="text-xs text-gray-500">{option.desc}</div>
                          </div>
                        </label>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Custom Instructions Tab */}
              {activeTab === 'custom' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    매장 특성 및 추가 요청사항
                  </label>
                  <textarea
                    value={settings.custom_instructions}
                    onChange={(e) => setSettings({ ...settings, custom_instructions: e.target.value })}
                    placeholder="예시:&#10;- 우리 매장은 사진관이므로 '추억', '순간' 같은 감성적인 단어를 사용해주세요&#10;- 가족 단위 고객이 많으므로 따뜻한 톤을 유지해주세요&#10;- 주차 관련 언급 시 '주차 공간이 협소하지만 최선을 다하고 있다'고 안내해주세요"
                    rows="10"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
                  />
                  <p className="text-xs text-gray-500 mt-2">
                    💡 매장만의 특별한 요청사항을 자유롭게 작성하세요. AI가 이를 반영하여 답글을 생성합니다.
                  </p>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 px-6 py-4 flex items-center justify-between bg-gray-50">
          <button
            onClick={handleReset}
            className="flex items-center space-x-2 px-4 py-2 text-gray-600 hover:text-gray-800 transition"
          >
            <RotateCcw className="w-4 h-4" />
            <span>기본값으로 되돌리기</span>
          </button>
          <div className="flex items-center space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-600 hover:text-gray-800 transition"
            >
              취소
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex items-center space-x-2 px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Save className="w-4 h-4" />
              <span>{saving ? '저장 중...' : '저장'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

