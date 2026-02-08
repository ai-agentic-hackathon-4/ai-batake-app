/**
 * Tests for EnvironmentChart component
 */
import React from 'react'
import { render, screen, waitFor, act } from '@testing-library/react'
import { EnvironmentChart } from '@/components/environment-chart'

// Mock fetch globally
global.fetch = jest.fn()

// Mock ResizeObserver (required for Recharts ResponsiveContainer)
global.ResizeObserver = jest.fn().mockImplementation(() => ({
    observe: jest.fn(),
    unobserve: jest.fn(),
    disconnect: jest.fn(),
}))

describe('EnvironmentChart Component', () => {
    beforeEach(() => {
        jest.clearAllMocks()
    })

    test('renders component title', async () => {
        (global.fetch as jest.Mock).mockResolvedValueOnce({
            json: async () => ({ data: [] })
        })

        await act(async () => {
            render(<EnvironmentChart />)
        })

        expect(screen.getByText('環境データ')).toBeInTheDocument()
    })

    test('renders time range selector', async () => {
        (global.fetch as jest.Mock).mockResolvedValueOnce({
            json: async () => ({ data: [] })
        })

        await act(async () => {
            render(<EnvironmentChart />)
        })

        expect(screen.getByRole('combobox')).toBeInTheDocument()
    })

    test('fetches sensor data on mount', async () => {
        const mockData = [
            { unix_timestamp: 1704067200, temperature: 25, humidity: 60 },
            { unix_timestamp: 1704070800, temperature: 26, humidity: 65 }
        ];

        (global.fetch as jest.Mock).mockResolvedValueOnce({
            json: async () => ({ data: mockData })
        })

        await act(async () => {
            render(<EnvironmentChart />)
        })

        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalledWith('/api/sensor-history?hours=24')
        })
    })

    test('handles empty data gracefully', async () => {
        (global.fetch as jest.Mock).mockResolvedValueOnce({
            json: async () => ({ data: [] })
        })

        await act(async () => {
            render(<EnvironmentChart />)
        })

        await waitFor(() => {
            expect(screen.getByText('環境データ')).toBeInTheDocument()
        })
    })

    test('handles fetch error gracefully', async () => {
        (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'))

        await act(async () => {
            render(<EnvironmentChart />)
        })

        expect(screen.getByText('環境データ')).toBeInTheDocument()
    })

    test('displays Activity icon', async () => {
        (global.fetch as jest.Mock).mockResolvedValueOnce({
            json: async () => ({ data: [] })
        })

        let container: HTMLElement;
        await act(async () => {
            const result = render(<EnvironmentChart />)
            container = result.container
        })

        const iconElement = container!.querySelector('svg')
        expect(iconElement).toBeInTheDocument()
    })
})
