/**
 * Tests for CharacterCard component
 */
import React from 'react'
import { render, screen, waitFor } from '@testing-library/react'
import { CharacterCard } from '@/components/character-card'

// Mock fetch
global.fetch = jest.fn()

describe('CharacterCard Component', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks()
  })

  test('renders loading state initially', () => {
    (global.fetch as jest.Mock).mockImplementation(() => 
      new Promise(() => {}) // Never resolves to keep loading state
    )

    render(<CharacterCard />)
    
    expect(screen.getByText('読み込み中...')).toBeInTheDocument()
  })

  test('renders character message after fetch', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      json: async () => ({
        message: '気温がちょうど良い感じだね！🌱',
        mood: 'happy',
        sensor_status: { temperature: 25, humidity: 65 }
      })
    })

    render(<CharacterCard />)
    
    await waitFor(() => {
      expect(screen.getByText('気温がちょうど良い感じだね！🌱')).toBeInTheDocument()
    })
  })

  test('displays character avatar emoji', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      json: async () => ({
        message: 'テストメッセージ',
        mood: 'happy',
        sensor_status: {}
      })
    })

    render(<CharacterCard />)
    
    await waitFor(() => {
      expect(screen.getByText('🌱')).toBeInTheDocument()
    })
  })

  test('displays character label', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      json: async () => ({
        message: 'テストメッセージ',
        mood: 'happy',
        sensor_status: {}
      })
    })

    render(<CharacterCard />)
    
    await waitFor(() => {
      expect(screen.getByText('畑の見守りキャラクター')).toBeInTheDocument()
    })
  })

  test('handles fetch error gracefully', async () => {
    (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('API Error'))

    render(<CharacterCard />)
    
    await waitFor(() => {
      expect(screen.getByText('今日も一緒に見守っていこうね！🌱')).toBeInTheDocument()
    })
  })

  test('handles different mood states', async () => {
    const moods = ['happy', 'concerned', 'excited']
    
    for (const mood of moods) {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        json: async () => ({
          message: 'テストメッセージ',
          mood: mood,
          sensor_status: {}
        })
      })

      const { unmount } = render(<CharacterCard />)
      
      await waitFor(() => {
        expect(screen.getByText('テストメッセージ')).toBeInTheDocument()
      })
      
      unmount()
    }
  })

  test('calls fetch with correct endpoint', () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      json: async () => ({
        message: 'テスト',
        mood: 'happy',
        sensor_status: {}
      })
    })

    render(<CharacterCard />)
    
    expect(global.fetch).toHaveBeenCalledWith('/api/character/message')
  })
})
