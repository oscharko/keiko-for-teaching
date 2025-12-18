/**
 * Tests for Button component.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Button } from '../button'

describe('Button', () => {
  it('should render button with text', () => {
    render(<Button>Click me</Button>)

    expect(screen.getByRole('button', { name: 'Click me' })).toBeInTheDocument()
  })

  it('should handle click events', async () => {
    const handleClick = vi.fn()
    const user = userEvent.setup()

    render(<Button onClick={handleClick}>Click me</Button>)

    await user.click(screen.getByRole('button'))

    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('should be disabled when disabled prop is true', () => {
    render(<Button disabled>Disabled</Button>)

    const button = screen.getByRole('button')

    expect(button).toBeDisabled()
  })

  it('should not call onClick when disabled', async () => {
    const handleClick = vi.fn()
    const user = userEvent.setup()

    render(
      <Button disabled onClick={handleClick}>
        Disabled
      </Button>
    )

    await user.click(screen.getByRole('button'))

    expect(handleClick).not.toHaveBeenCalled()
  })

  it('should render with default variant', () => {
    render(<Button>Default</Button>)

    const button = screen.getByRole('button')

    expect(button).toHaveClass('bg-keiko-primary')
  })

  it('should render with destructive variant', () => {
    render(<Button variant="destructive">Delete</Button>)

    const button = screen.getByRole('button')

    expect(button).toHaveClass('bg-destructive')
  })

  it('should render with outline variant', () => {
    render(<Button variant="outline">Outline</Button>)

    const button = screen.getByRole('button')

    expect(button).toHaveClass('border')
  })

  it('should render with secondary variant', () => {
    render(<Button variant="secondary">Secondary</Button>)

    const button = screen.getByRole('button')

    expect(button).toHaveClass('bg-secondary')
  })

  it('should render with ghost variant', () => {
    render(<Button variant="ghost">Ghost</Button>)

    const button = screen.getByRole('button')

    expect(button).toHaveClass('hover:bg-accent')
  })

  it('should render with link variant', () => {
    render(<Button variant="link">Link</Button>)

    const button = screen.getByRole('button')

    expect(button).toHaveClass('underline-offset-4')
  })

  it('should render with small size', () => {
    render(<Button size="sm">Small</Button>)

    const button = screen.getByRole('button')

    expect(button).toHaveClass('h-9')
  })

  it('should render with large size', () => {
    render(<Button size="lg">Large</Button>)

    const button = screen.getByRole('button')

    expect(button).toHaveClass('h-11')
  })

  it('should render with icon size', () => {
    render(<Button size="icon">Icon</Button>)

    const button = screen.getByRole('button')

    expect(button).toHaveClass('h-10', 'w-10')
  })

  it('should accept custom className', () => {
    render(<Button className="custom-class">Custom</Button>)

    const button = screen.getByRole('button')

    expect(button).toHaveClass('custom-class')
  })

  it('should support button type attribute', () => {
    render(<Button type="submit">Submit</Button>)

    const button = screen.getByRole('button')

    expect(button).toHaveAttribute('type', 'submit')
  })

  it('should render children correctly', () => {
    render(
      <Button>
        <span>Icon</span>
        <span>Text</span>
      </Button>
    )

    expect(screen.getByText('Icon')).toBeInTheDocument()
    expect(screen.getByText('Text')).toBeInTheDocument()
  })
})

