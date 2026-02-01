/**
 * Tests for MetricCard component
 */
import React from 'react'
import { render, screen } from '@testing-library/react'
import { MetricCard } from '@/components/metric-card'
import { Thermometer } from 'lucide-react'

describe('MetricCard Component', () => {
  test('renders with basic props', () => {
    render(
      <MetricCard
        title="Temperature"
        value="25"
        unit="°C"
        icon={Thermometer}
      />
    )
    
    expect(screen.getByText('Temperature')).toBeInTheDocument()
    expect(screen.getByText('25')).toBeInTheDocument()
    expect(screen.getByText('°C')).toBeInTheDocument()
  })

  test('renders with normal status by default', () => {
    const { container } = render(
      <MetricCard
        title="Temperature"
        value="25"
        unit="°C"
        icon={Thermometer}
      />
    )
    
    const valueElement = screen.getByText('25')
    expect(valueElement).toHaveClass('text-primary')
  })

  test('renders with warning status', () => {
    const { container } = render(
      <MetricCard
        title="Temperature"
        value="35"
        unit="°C"
        icon={Thermometer}
        status="warning"
      />
    )
    
    const valueElement = screen.getByText('35')
    expect(valueElement).toHaveClass('text-chart-2')
  })

  test('renders with critical status', () => {
    const { container } = render(
      <MetricCard
        title="Temperature"
        value="40"
        unit="°C"
        icon={Thermometer}
        status="critical"
      />
    )
    
    const valueElement = screen.getByText('40')
    expect(valueElement).toHaveClass('text-destructive')
  })

  test('displays icon correctly', () => {
    const { container } = render(
      <MetricCard
        title="Temperature"
        value="25"
        unit="°C"
        icon={Thermometer}
      />
    )
    
    // Check that icon is rendered (lucide-react icons have specific classes)
    const iconElement = container.querySelector('svg')
    expect(iconElement).toBeInTheDocument()
  })
})
