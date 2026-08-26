import { useRef, useState } from 'react';

interface Point {
  label: string;
  value: number;
}

export function AreaChart({ data, unit = 'finding' }: { data: Point[]; unit?: string }) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [hover, setHover] = useState<{ x: number; y: number; i: number } | null>(null);

  const W = 640;
  const H = 200;
  const padL = 28;
  const padR = 10;
  const padT = 14;
  const padB = 22;
  const iw = W - padL - padR;
  const ih = H - padT - padB;
  const max = Math.max(1, ...data.map((d) => d.value));
  const n = Math.max(1, data.length - 1);
  const X = (i: number) => padL + (i / n) * iw;
  const Y = (v: number) => padT + (1 - v / max) * ih;

  const line = data.map((d, i) => `${i === 0 ? 'M' : 'L'}${X(i)} ${Y(d.value)}`).join(' ');
  const area = `M${X(0)} ${Y(0)} ${data.map((d, i) => `L${X(i)} ${Y(d.value)}`).join(' ')} L${X(n)} ${Y(0)} Z`;

  const grid: number[] = [];
  for (let g = 0; g <= max; g += Math.max(1, Math.ceil(max / 4))) grid.push(g);

  const move = (e: React.MouseEvent) => {
    const svg = svgRef.current;
    if (!svg) return;
    const r = svg.getBoundingClientRect();
    const px = ((e.clientX - r.left) / r.width) * W;
    let i = Math.round(((px - padL) / iw) * n);
    i = Math.max(0, Math.min(data.length - 1, i));
    setHover({ x: X(i), y: Y((data[i]?.value ?? 0)), i });
  };

  return (
    <div className="chartwrap">
      <svg
        ref={svgRef}
        className="chart"
        viewBox={`0 0 ${W} ${H}`}
        preserveAspectRatio="none"
        role="img"
        aria-label={`${unit}s over time`}
        onMouseMove={move}
        onMouseLeave={() => setHover(null)}
      >
        {grid.map((g) => (
          <g key={g}>
            <line x1={padL} y1={Y(g)} x2={W - padR} y2={Y(g)} stroke="var(--line-soft)" strokeWidth={1} />
            <text x={padL - 6} y={Y(g) + 3} textAnchor="end" className="axlabel">
              {g}
            </text>
          </g>
        ))}
        {Array.from(new Set([0, Math.floor(n / 2), n])).map((i) => (
          <text
            key={i}
            x={X(i)}
            y={H - 6}
            textAnchor={i === 0 ? 'start' : i === n ? 'end' : 'middle'}
            className="axlabel"
          >
            {data[i]?.label}
          </text>
        ))}
        <path d={area} fill="var(--acc-fill)" />
        <path d={line} fill="none" stroke="var(--acc)" strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" />
        <circle cx={X(n)} cy={Y(data[data.length - 1]?.value ?? 0)} r={3.2} fill="var(--acc)" />
        {hover && (
          <>
            <line x1={hover.x} y1={padT} x2={hover.x} y2={padT + ih} stroke="var(--acc)" strokeWidth={1} opacity={0.5} />
            <circle cx={hover.x} cy={hover.y} r={3.5} fill="var(--acc)" stroke="var(--bg)" strokeWidth={2} />
          </>
        )}
      </svg>
      {hover && data[hover.i] && (
        <div
          className="tooltip"
          style={{
            opacity: 1,
            left: `calc(${(hover.x / W) * 100}% - 46px)`,
            top: `calc(${(hover.y / H) * 100}% - 42px)`,
          }}
        >
          <span className="tv">
            {data[hover.i]!.value} {unit}
            {data[hover.i]!.value === 1 ? '' : 's'}
          </span>
          <br />
          <span className="td">{data[hover.i]!.label}</span>
        </div>
      )}
    </div>
  );
}
