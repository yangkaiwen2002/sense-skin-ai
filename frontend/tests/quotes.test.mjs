import test from 'node:test'
import assert from 'node:assert/strict'
import { quoteMetadata } from '../src/utils/quotes.js'

const now = Date.parse('2026-11-06T02:00:00Z')

test('naive API timestamps are interpreted as UTC, preserving explicit offsets', () => {
  for (const snapshot_time of ['2026-11-06T01:00:00', '2026-11-06T01:00:00Z', '2026-11-06T09:00:00+08:00']) {
    const result = quoteMetadata({ price_kind: 'observed', snapshot_time }, now)
    assert.equal(result.date.toISOString(), '2026-11-06T01:00:00.000Z')
    assert.equal(result.label, '采集报价')
    assert.equal(result.stale, false)
  }
})

test('a quote expires only after 24 hours, or when explicitly marked stale', () => {
  const quote = { price_kind: 'demo', snapshot_time: '2026-11-05T02:00:00Z' }
  assert.equal(quoteMetadata(quote, now).stale, false)
  assert.equal(quoteMetadata(quote, now + 1).stale, true)
  assert.equal(quoteMetadata({ ...quote, is_stale: true }, now).stale, true)
  assert.equal(quoteMetadata(quote, now).label, '演示数据')
})

test('missing, invalid and unknown provenance never appear as verified or dated', () => {
  for (const quote of [undefined, {}, { price_kind: 'legacy_unknown', snapshot_time: 'bad-date' }, { price_kind: 'unrecognized' }]) {
    const result = quoteMetadata(quote, now)
    assert.equal(result.label, '来源未核验')
    assert.equal(result.date, null)
    assert.equal(result.stale, false)
  }
})
