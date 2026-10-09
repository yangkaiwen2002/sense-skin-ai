import test from "node:test";
import assert from "node:assert/strict";
import { buildResearchBrief, briefText } from "../src/utils/researchBrief.js";
test("compares valid positive prices, preserving zero returns and negative evidence", () => {
  const b = buildResearchBrief(
    {
      item_name: "Example",
      platforms: [
        { platform: "invalid", current_price: 0 },
        { platform: "B", current_price: 120 },
        { platform: "A", current_price: 100, return_7d: 0 },
      ],
    },
    {
      recommendation: "WATCH",
      score_summary: { total: 62, liquidity: 20 },
      supporting_signals: [
        { direction: "-", label: "risk", note: "traceable" },
      ],
    },
  );
  assert.match(b.facts[0], /A.*100.00/);
  assert.match(b.facts[1], /20.00.*20.0%/);
  assert.match(b.facts[2], /0.0%/);
  assert.equal(b.next.length, 3);
  assert.match(briefText(b), /traceable/);
});
test("missing data produces no invented prices or score", () => {
  const b = buildResearchBrief(
    { platforms: [{ current_price: null }, { current_price: NaN }] },
    null,
  );
  assert.deepEqual(b.facts, []);
  assert.equal(b.signals.length, 0);
  assert.match(b.next.join(""), /缺少有效报价/);
});

import { parseWatchlist } from "../src/utils/watchlist.js";
test("saved IDs tolerate corrupted storage and reject invalid entries", () => {
  assert.deepEqual(parseWatchlist("{bad"), []);
  assert.deepEqual(parseWatchlist('[1,1,2,null,-1,"3",0]'), [1, 2]);
  assert.deepEqual(parseWatchlist('{"id":1}'), []);
});
