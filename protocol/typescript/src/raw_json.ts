interface ObjectFrame {
  keys: Set<string> | undefined;
  expectsKey: boolean;
}

function stringEnd(raw: string, opening: number): number {
  let offset = opening + 1;
  while (offset < raw.length) {
    const character = raw.charAt(offset);
    if (character === '\\') {
      offset += 2;
    } else if (character === '"') {
      return offset;
    } else {
      offset += 1;
    }
  }
  return offset;
}

export function isUnambiguousJson(raw: string, maximumDepth: number): boolean {
  const frames: ObjectFrame[] = [];
  let offset = 0;
  while (offset < raw.length) {
    const character = raw.charAt(offset);
    const frame = frames.at(-1);
    if (/[ \t\r\n:]/u.test(character)) {
      offset += 1;
    } else if (character === '{' || character === '[') {
      if (frames.length > maximumDepth) return false;
      frames.push({
        keys: character === '{' ? new Set() : undefined,
        expectsKey: character === '{',
      });
      offset += 1;
    } else if (character === '}' || character === ']') {
      frames.pop();
      offset += 1;
    } else if (character === ',') {
      if (frame?.keys) frame.expectsKey = true;
      offset += 1;
    } else if (character === '"') {
      const ending = stringEnd(raw, offset);
      if (frame?.keys && frame.expectsKey) {
        const key = JSON.parse(raw.slice(offset, ending + 1)) as string;
        if (frame.keys.has(key)) return false;
        frame.keys.add(key);
        frame.expectsKey = false;
      } else if (frames.length > maximumDepth) {
        return false;
      }
      offset = ending + 1;
    } else {
      if (frames.length > maximumDepth) return false;
      while (
        offset < raw.length &&
        !/[ \t\r\n,}\]]/u.test(raw.charAt(offset))
      ) {
        offset += 1;
      }
    }
  }
  return frames.length === 0;
}
