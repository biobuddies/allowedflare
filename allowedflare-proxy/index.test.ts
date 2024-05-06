import { afterAll, beforeAll, describe, expect, it, vi } from 'vitest'
import { unstable_dev } from 'wrangler'
import type { UnstableDevWorker } from 'wrangler'

global.fetch = vi.fn()

function fetchResponse(data) {
    return {
        json: () => new Promise((resolve) => resolve(data)),
    }
}

describe('Worker', () => {
    let worker: UnstableDevWorker

    beforeAll(async () => {
        worker = await unstable_dev('allowedflare-proxy/index.ts', {
            experimental: { disableExperimentalWarning: true },
        })
    })

    afterAll(async () => {
        await worker.stop()
    })

    it('should fetch the subdomain', async () => {
        fetch.mockResolvedValue(fetchResponse({}))
        await worker.fetch('https://subdomain.example.com/x/subbysub/path?query=string')
        expect(fetch).toHaveBeenCalledWith('https://subbysub.example.com/path?query=string')
    })
})
