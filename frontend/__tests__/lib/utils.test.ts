/**
 * Tests for utility functions in lib/utils.ts
 */
import { cn } from '@/lib/utils'

describe('cn utility function', () => {
  test('merges class names correctly', () => {
    const result = cn('class1', 'class2')
    expect(result).toContain('class1')
    expect(result).toContain('class2')
  })

  test('handles conditional classes', () => {
    const result = cn('base', false && 'conditional', 'always')
    expect(result).toContain('base')
    expect(result).toContain('always')
    expect(result).not.toContain('conditional')
  })

  test('handles undefined and null values', () => {
    const result = cn('class1', undefined, null, 'class2')
    expect(result).toContain('class1')
    expect(result).toContain('class2')
  })

  test('merges tailwind classes correctly', () => {
    // Testing tailwind-merge functionality
    const result = cn('p-4', 'p-6')
    // tailwind-merge should keep only the last padding class
    expect(result).toBe('p-6')
  })

  test('handles empty input', () => {
    const result = cn()
    expect(result).toBe('')
  })

  test('handles array of classes', () => {
    const result = cn(['class1', 'class2'])
    expect(result).toContain('class1')
    expect(result).toContain('class2')
  })

  test('handles object with conditional classes', () => {
    const result = cn({
      'active': true,
      'inactive': false,
      'visible': true
    })
    expect(result).toContain('active')
    expect(result).toContain('visible')
    expect(result).not.toContain('inactive')
  })
})
