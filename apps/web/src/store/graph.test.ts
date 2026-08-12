import { beforeEach, describe, expect, it } from 'vitest';
import { useGraph } from './graph';

beforeEach(() => useGraph.setState({ positions: {} }));

describe('useGraph', () => {
  it('records a node position under its key', () => {
    useGraph.getState().setPos('run-1:agent-a', { x: 10, y: 20 });
    expect(useGraph.getState().positions['run-1:agent-a']).toEqual({ x: 10, y: 20 });
  });

  it('overwrites an existing key without touching the others', () => {
    const { setPos } = useGraph.getState();
    setPos('run-1:agent-a', { x: 1, y: 1 });
    setPos('run-1:agent-b', { x: 2, y: 2 });
    setPos('run-1:agent-a', { x: 9, y: 9 });
    expect(useGraph.getState().positions).toEqual({
      'run-1:agent-a': { x: 9, y: 9 },
      'run-1:agent-b': { x: 2, y: 2 },
    });
  });
});
