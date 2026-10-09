import test from "node:test";
import assert from "node:assert/strict";
import { consumeSSE } from "../src/utils/sse.js";
function stream(bytes, step = 1) {
  return new ReadableStream({
    start(c) {
      for (let i = 0; i < bytes.length; i += step)
        c.enqueue(bytes.slice(i, i + step));
      c.close();
    },
  });
}
const encode = (text) => new TextEncoder().encode(text);
test("handles fragmented UTF-8, CRLF, comments and final sentinel", async () => {
  const events = [];
  await consumeSSE(
    stream(
      encode(
        ': ping\r\n\r\ndata: {"type":"text","text":"中文"}\r\n\r\ndata:[DONE]\r\n\r\n',
      ),
    ),
    (e) => events.push(e),
  );
  assert.deepEqual(events, [{ type: "text", text: "中文" }]);
});
test("unexpected EOF preserves content but reports interruption", async () => {
  const events = [];
  await assert.rejects(
    consumeSSE(stream(encode('data: {"text":"partial"}\n\n')), (e) =>
      events.push(e),
    ),
    /连接提前结束/,
  );
  assert.equal(events[0].text, "partial");
});
test("malformed events are not silently treated as successful answers", async () => {
  await assert.rejects(
    consumeSSE(stream(encode("data: invalid\n\ndata: [DONE]\n\n")), () => {}),
    SyntaxError,
  );
});
