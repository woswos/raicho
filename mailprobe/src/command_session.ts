import { COMMAND_IDENTIFIER, parseCommand, objectValue } from './validation.js';
import type { Command } from './validation.js';

export class CommandSession {
  private readonly identifiers = new Set<string>();

  constructor(private readonly dispatch: (command: Command) => Promise<unknown>) {}

  async execute(value: unknown) {
    let identifier = 'invalid';
    try {
      const candidate = objectValue(value);
      if (typeof candidate.id === 'string' && COMMAND_IDENTIFIER.test(candidate.id)) {
        identifier = candidate.id;
      }
      const command = parseCommand(value);
      if (this.identifiers.has(command.id)) throw new Error('Command identifier already used.');
      if (this.identifiers.size >= 1000) throw new Error('Probe command limit reached.');
      this.identifiers.add(command.id);
      const result = await this.dispatch(command);
      if (new TextEncoder().encode(JSON.stringify(result)).length > 60000) {
        throw new Error('Probe result exceeds the fixture limit.');
      }
      return { type: 'result', id: command.id, ok: true, result };
    } catch (error) {
      return {
        type: 'result',
        id: identifier,
        ok: false,
        error: error instanceof Error ? error.message.slice(0, 512) : 'Probe command failed.',
      };
    }
  }
}
