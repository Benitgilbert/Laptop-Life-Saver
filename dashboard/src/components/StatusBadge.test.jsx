import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import StatusBadge from './StatusBadge'

describe('StatusBadge Component', () => {
    it('renders green status correctly', () => {
        render(<StatusBadge status="green" />)
        const badge = screen.getByText(/Healthy/i).closest('.badge')
        expect(badge).toBeInTheDocument()
        expect(badge).toHaveClass('bg-health-green-bg')
    })

    it('renders red status correctly', () => {
        render(<StatusBadge status="red" />)
        const badge = screen.getByText(/Critical/i).closest('.badge')
        expect(badge).toBeInTheDocument()
        expect(badge).toHaveClass('bg-health-red-bg')
    })

    it('renders yellow status correctly', () => {
        render(<StatusBadge status="yellow" />)
        const badge = screen.getByText(/Warning/i).closest('.badge')
        expect(badge).toBeInTheDocument()
        expect(badge).toHaveClass('bg-health-yellow-bg')
    })
})
