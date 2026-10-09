/** Parse complete SSE events across arbitrary UTF-8/network chunk boundaries. */
export async function consumeSSE(body, onEvent) {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let completed = false;
  function consume(flush = false) {
    if (flush && buffer.trim()) buffer += "\n\n";
    let match;
    while ((match = /\r?\n\r?\n/.exec(buffer))) {
      const block = buffer.slice(0, match.index);
      buffer = buffer.slice(match.index + match[0].length);
      const data = block
        .split(/\r?\n/)
        .filter((l) => l.startsWith("data:"))
        .map((l) => l.slice(5).replace(/^ /, ""))
        .join("\n");
      if (!data) continue;
      if (data === "[DONE]") {
        completed = true;
        return;
      }
      onEvent(JSON.parse(data));
    }
  }
  try {
    while (!completed) {
      const { done, value } = await reader.read();
      buffer += done
        ? decoder.decode()
        : decoder.decode(value, { stream: true });
      consume(done);
      if (done) {
        if (!completed)
          throw new Error("连接提前结束，已保留收到的内容，请重试。");
        break;
      }
    }
  } finally {
    try {
      await reader.cancel();
    } finally {
      reader.releaseLock();
    }
  }
}
