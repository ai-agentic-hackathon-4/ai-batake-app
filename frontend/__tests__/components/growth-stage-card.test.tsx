/**
 * Tests for GrowthStageCard component
 */
import React from 'react'
import { render, screen } from '@testing-library/react'
import { GrowthStageCard } from '@/components/growth-stage-card'

describe('GrowthStageCard Component', () => {
  test('renders growth stage card title', () => {
    render(<GrowthStageCard />)
    
    expect(screen.getByText('生育段階')).toBeInTheDocument()
  })

  test('renders current stage name', () => {
    render(<GrowthStageCard />)
    
    expect(screen.getByText('開花期')).toBeInTheDocument()
  })

  test('renders days since planting', () => {
    render(<GrowthStageCard />)
    
    expect(screen.getByText('播種から42日目')).toBeInTheDocument()
  })

  test('renders progress percentage', () => {
    render(<GrowthStageCard />)
    
    // 2 completed stages out of 5 = 40%
    expect(screen.getByText('40%')).toBeInTheDocument()
  })

  test('renders progress label', () => {
    render(<GrowthStageCard />)
    
    expect(screen.getByText('進捗')).toBeInTheDocument()
  })

  test('renders all stage abbreviations', () => {
    render(<GrowthStageCard />)
    
    expect(screen.getByText('発芽')).toBeInTheDocument()
    expect(screen.getByText('栄養')).toBeInTheDocument()
    expect(screen.getByText('開花')).toBeInTheDocument()
    expect(screen.getByText('結実')).toBeInTheDocument()
    expect(screen.getByText('収穫')).toBeInTheDocument()
  })

  test('renders progress bar', () => {
    const { container } = render(<GrowthStageCard />)
    
    // Check for progress bar container
    const progressBar = container.querySelector('.bg-muted.rounded-full')
    expect(progressBar).toBeInTheDocument()
  })

  test('renders stage timeline dots', () => {
    const { container } = render(<GrowthStageCard />)
    
    // Check for stage indicator dots
    const dots = container.querySelectorAll('.rounded-full')
    // Should have progress bar + 5 stage dots = at least 6 rounded elements
    expect(dots.length).toBeGreaterThanOrEqual(6)
  })

  test('renders sprout icon', () => {
    const { container } = render(<GrowthStageCard />)
    
    // Check that icons are rendered (should have multiple SVG elements)
    const icons = container.querySelectorAll('svg')
    expect(icons.length).toBeGreaterThan(0)
  })
})
