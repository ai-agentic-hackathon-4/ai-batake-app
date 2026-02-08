/**
 * Tests for PlantCamera component
 */
import React from 'react'
import { render, screen, waitFor, act } from '@testing-library/react'
import { PlantCamera } from '@/components/plant-camera'

// Mock fetch globally
global.fetch = jest.fn()

describe('PlantCamera Component', () => {
    beforeEach(() => {
        jest.clearAllMocks()
    })

    test('shows loading state initially', async () => {
        (global.fetch as jest.Mock).mockImplementationOnce(() =>
            new Promise(() => { })
        )

        await act(async () => {
            render(<PlantCamera />)
        })

        expect(screen.getByText('最新の画像を読み込み中...')).toBeInTheDocument()
    })

    test('renders component title and badge', async () => {
        (global.fetch as jest.Mock).mockResolvedValueOnce({
            ok: true,
            json: async () => ({ image: null })
        })

        await act(async () => {
            render(<PlantCamera />)
        })

        expect(screen.getByText('プラントカメラ')).toBeInTheDocument()
        expect(screen.getByText('ライブ')).toBeInTheDocument()
    })

    test('displays image when fetch succeeds', async () => {
        const mockImage = 'data:image/jpeg;base64,fake-image-data';
        const mockTimestamp = '2025-01-01T12:00:00Z';

        (global.fetch as jest.Mock).mockResolvedValueOnce({
            ok: true,
            json: async () => ({ image: mockImage, timestamp: mockTimestamp })
        })

        await act(async () => {
            render(<PlantCamera />)
        })

        await waitFor(() => {
            const img = screen.getByAltText('植物のライブカメラ映像')
            expect(img).toBeInTheDocument()
            expect(img).toHaveAttribute('src', mockImage)
        })
    })


    test('shows error message when no image found', async () => {
        (global.fetch as jest.Mock).mockResolvedValueOnce({
            ok: true,
            json: async () => ({ image: null })
        })

        await act(async () => {
            render(<PlantCamera />)
        })

        await waitFor(() => {
            expect(screen.getByText('画像が取得できませんでした')).toBeInTheDocument()
        })
    })

    test('handles fetch error gracefully', async () => {
        (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'))

        await act(async () => {
            render(<PlantCamera />)
        })

        await waitFor(() => {
            expect(screen.getByText('画像が取得できませんでした')).toBeInTheDocument()
        })
    })

    test('handles non-ok response', async () => {
        (global.fetch as jest.Mock).mockResolvedValueOnce({
            ok: false
        })

        await act(async () => {
            render(<PlantCamera />)
        })

        await waitFor(() => {
            expect(screen.getByText('画像が取得できませんでした')).toBeInTheDocument()
        })
    })
})
