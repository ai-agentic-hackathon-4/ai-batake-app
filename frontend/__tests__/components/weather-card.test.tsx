/**
 * Tests for WeatherCard component
 */
import React from 'react'
import { render, screen } from '@testing-library/react'
import { WeatherCard } from '@/components/weather-card'

describe('WeatherCard Component', () => {
  test('renders weather card title', () => {
    render(<WeatherCard />)
    
    expect(screen.getByText('本日の天気予報')).toBeInTheDocument()
  })

  test('renders current temperature', () => {
    render(<WeatherCard />)
    
    expect(screen.getByText('26°C')).toBeInTheDocument()
  })

  test('renders weather description', () => {
    render(<WeatherCard />)
    
    expect(screen.getByText('晴れ時々曇り')).toBeInTheDocument()
  })

  test('renders wind speed', () => {
    render(<WeatherCard />)
    
    expect(screen.getByText('3 m/s')).toBeInTheDocument()
  })

  test('renders sunrise time', () => {
    render(<WeatherCard />)
    
    expect(screen.getByText('5:42')).toBeInTheDocument()
  })

  test('renders sunset time', () => {
    render(<WeatherCard />)
    
    expect(screen.getByText('18:23')).toBeInTheDocument()
  })

  test('renders hourly forecast times', () => {
    render(<WeatherCard />)
    
    expect(screen.getByText('9時')).toBeInTheDocument()
    expect(screen.getByText('12時')).toBeInTheDocument()
    expect(screen.getByText('15時')).toBeInTheDocument()
    expect(screen.getByText('18時')).toBeInTheDocument()
  })

  test('renders hourly forecast temperatures', () => {
    render(<WeatherCard />)
    
    expect(screen.getByText('24°')).toBeInTheDocument()
    expect(screen.getByText('28°')).toBeInTheDocument()
    expect(screen.getByText('27°')).toBeInTheDocument()
    expect(screen.getByText('23°')).toBeInTheDocument()
  })

  test('renders multiple weather icons', () => {
    const { container } = render(<WeatherCard />)
    
    // Should have multiple SVG icons (weather icons)
    const icons = container.querySelectorAll('svg')
    expect(icons.length).toBeGreaterThan(1)
  })
})
