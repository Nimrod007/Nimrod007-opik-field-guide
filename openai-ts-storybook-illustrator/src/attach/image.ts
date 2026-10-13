// Turning a generated image into something Opik shows as an attachment.

export function toDataUri(b64: string, mime = "image/png"): string {
  return `data:${mime};base64,${b64}`;
}

// The trace output we log. Opik's SDK scans trace/span payloads for large base64
// data URIs (over OPIK_MIN_BASE64_EMBEDDED_ATTACHMENT_SIZE, 256k chars by default),
// uploads them as real attachments and replaces them with a [file.png] reference.
// Without a data URI here the trace would only show text and no picture.
export function imageTraceOutput(b64: string, model: string, size: string) {
  return { image: toDataUri(b64), model, size };
}
