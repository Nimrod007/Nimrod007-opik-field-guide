export interface Chunk {
  id: string;
  source: string;
  heading: string;
  text: string;
}

/** Split a markdown care guide into one chunk per "## " section. */
export function chunkMarkdown(source: string, markdown: string): Chunk[] {
  const chunks: Chunk[] = [];
  let heading = "";
  let lines: string[] = [];
  const flush = () => {
    const text = lines.join("\n").trim();
    if (heading && text) {
      chunks.push({ id: `${source}#${chunks.length}`, source, heading, text: `${heading}\n${text}` });
    }
    lines = [];
  };
  for (const line of markdown.split("\n")) {
    if (line.startsWith("## ")) {
      flush();
      heading = line.slice(3).trim();
    } else if (!line.startsWith("# ")) {
      lines.push(line);
    }
  }
  flush();
  return chunks;
}
