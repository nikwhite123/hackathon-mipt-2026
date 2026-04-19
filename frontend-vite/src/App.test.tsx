/* eslint-disable @typescript-eslint/no-explicit-any */
import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import App from './App'
import { useAuthStore } from './store/authStore'
import { useDashboardFiltersStore } from './store/dashboardFiltersStore'

(globalThis as unknown as { ResizeObserver: unknown }).ResizeObserver = vi.fn().mockImplementation(() => ({
    observe: vi.fn(),
    unobserve: vi.fn(),
    disconnect: vi.fn(),
}))

Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation(query => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
    })),
})

const mockCtx = {
    clearRect: vi.fn(), fillRect: vi.fn(), rect: vi.fn(), arc: vi.fn(),
    scale: vi.fn(), translate: vi.fn(), rotate: vi.fn(),
    createLinearGradient: vi.fn(() => ({ addColorStop: vi.fn() })),
    getImageData: vi.fn(() => ({ data: [] })), putImageData: vi.fn(),
    measureText: vi.fn(() => ({ width: 100 })), setTransform: vi.fn(),
    beginPath: vi.fn(), moveTo: vi.fn(), lineTo: vi.fn(), closePath: vi.fn(),
    stroke: vi.fn(), fill: vi.fn(), save: vi.fn(), restore: vi.fn(), fillText: vi.fn(),
};

HTMLCanvasElement.prototype.getContext = vi.fn().mockImplementation((contextId: string) => {
    if (contextId === '2d') return mockCtx;
    return null;
}) as unknown as typeof HTMLCanvasElement.prototype.getContext;

vi.mock('./api/analyticsService', () => ({
    fetchStatsFacets: vi.fn().mockResolvedValue({ regions: ['Москва'], industries: ['IT'] }),
    fetchStats: vi.fn().mockResolvedValue({}),
    fetchInfrastructureStats: vi.fn().mockResolvedValue({}),
}))

vi.mock('./api/authService', () => ({
    fetchCurrentUser: vi.fn().mockResolvedValue({}),
    logout: vi.fn(),
}))

describe('RT Infra Security Core UI', { timeout: 30000 }, () => {
    beforeEach(() => {
        vi.clearAllMocks()
        vi.spyOn(console, 'error').mockImplementation(() => {})
        vi.spyOn(console, 'warn').mockImplementation(() => {})
        useDashboardFiltersStore.getState().reset()
        window.history.pushState({}, '', '/')
    })

    it('корректно отображает основной интерфейс (Landing Page)', async () => {
        useAuthStore.setState({ user: null })

        render(<App />)

        const brand = await screen.findByText((_, element) => {
            if (!element) return false;
            const hasText = (node: Element | null) => node?.textContent?.includes("RT Infra") || false;
            const nodeHasText = hasText(element);
            const childrenDontHaveText = Array.from(element.children).every(child => !hasText(child as Element));
            return nodeHasText && childrenDontHaveText;
        }, {}, { timeout: 15000 });

        expect(brand).toBeInTheDocument()
    })
})