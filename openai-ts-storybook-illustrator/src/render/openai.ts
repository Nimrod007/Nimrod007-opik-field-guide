import OpenAI from "openai";
import type { Opik } from "opik";
import { trackOpenAI } from "opik-openai";

// Cheapest current image setup: gpt-image-1, lowest quality, smallest size it offers.
export const IMAGE_MODEL = "gpt-image-1";
export const IMAGE_SIZE = "1024x1024";
export const IMAGE_QUALITY = "low";

// Minimal shape we need, so tests can stub the client.
export interface ImageClient {
  images: {
    generate(args: {
      model: string;
      prompt: string;
      n: number;
      size: "1024x1024";
      quality: "low";
    }): Promise<{ data?: { b64_json?: string }[] }>;
  };
}

// trackOpenAI wraps the client: each images.generate call becomes a child span of
// `parent` (the page trace), with the rendered prompt as its input and token usage.
export function trackedClient(client: OpenAI, opik: Opik, parent: unknown): ImageClient {
  return trackOpenAI(client, {
    client: opik,
    parent: parent as never,
    generationName: "images.generate",
  }) as unknown as ImageClient;
}

export async function generateImage(client: ImageClient, prompt: string): Promise<string> {
  const result = await client.images.generate({
    model: IMAGE_MODEL,
    prompt,
    n: 1,
    size: IMAGE_SIZE,
    quality: IMAGE_QUALITY,
  });
  const b64 = result.data?.[0]?.b64_json;
  if (!b64) throw new Error(`${IMAGE_MODEL} returned no image data`);
  return b64;
}
