const https = require('https');
const fs = require('fs');

const USERNAME = process.env.GITHUB_USERNAME || 'desuqcafe';
const TOKEN = process.env.GITHUB_TOKEN || '';

// Color palette (Madoka/Miku theme)
const COLORS = {
  empty: '#161b22',
  levels: [
    '#161b22',
    'rgba(155, 89, 182, 0.30)',
    'rgba(155, 89, 182, 0.50)',
    'rgba(200, 109, 215, 0.70)',
    'rgba(233, 30, 144, 0.80)',
  ],
  // Solid hex equivalents for SVG compatibility
  levelsHex: ['#161b22', '#3b2350', '#5c3578', '#a453b8', '#d4207a'],
  ripple: '#39c5bb',
  rippleHighlight: '#c86dd7',
  bg: '#0d1117',
};

const CELL = 11;
const GAP = 3;
const COLS = 52;
const ROWS = 7;
const PADDING = 8;
const WIDTH = PADDING * 2 + COLS * (CELL + GAP) - GAP;
const HEIGHT = PADDING * 2 + ROWS * (CELL + GAP) - GAP;

async function fetchContributions() {
  const query = `
    query {
      user(login: "${USERNAME}") {
        contributionsCollection {
          contributionCalendar {
            weeks {
              contributionDays {
                contributionCount
                contributionLevel
                date
              }
            }
          }
        }
      }
    }
  `;

  return new Promise((resolve, reject) => {
    const data = JSON.stringify({ query });
    const options = {
      hostname: 'api.github.com',
      path: '/graphql',
      method: 'POST',
      headers: {
        'Authorization': `bearer ${TOKEN}`,
        'Content-Type': 'application/json',
        'User-Agent': 'contribution-ripple-generator',
        'Content-Length': Buffer.byteLength(data),
      },
    };

    const req = https.request(options, (res) => {
      let body = '';
      res.on('data', (chunk) => body += chunk);
      res.on('end', () => {
        try {
          const json = JSON.parse(body);
          if (json.errors) {
            reject(new Error(JSON.stringify(json.errors)));
            return;
          }
          const weeks = json.data.user.contributionsCollection.contributionCalendar.weeks;
          resolve(weeks);
        } catch (e) {
          reject(e);
        }
      });
    });

    req.on('error', reject);
    req.write(data);
    req.end();
  });
}

function levelToIndex(level) {
  switch (level) {
    case 'NONE': return 0;
    case 'FIRST_QUARTILE': return 1;
    case 'SECOND_QUARTILE': return 2;
    case 'THIRD_QUARTILE': return 3;
    case 'FOURTH_QUARTILE': return 4;
    default: return 0;
  }
}

function generateRipplePoints(grid) {
  // Pick cells with contributions for ripple origins
  const candidates = [];
  for (let col = 0; col < grid.length; col++) {
    for (let row = 0; row < grid[col].length; row++) {
      if (grid[col][row] > 0) {
        candidates.push({ col, row });
      }
    }
  }

  // Select 4-6 ripple points spread across the graph
  const count = Math.min(Math.max(4, Math.floor(candidates.length / 30)), 6);
  const selected = [];
  const shuffled = candidates.sort(() => Math.random() - 0.5);

  for (const c of shuffled) {
    if (selected.length >= count) break;
    // Ensure some spacing between ripple points
    const tooClose = selected.some(s => {
      const dx = Math.abs(s.col - c.col);
      const dy = Math.abs(s.row - c.row);
      return dx < 8 && dy < 3;
    });
    if (!tooClose) selected.push(c);
  }

  // If we couldn't get enough with spacing, fill in
  if (selected.length < 3) {
    for (const c of shuffled) {
      if (selected.length >= 4) break;
      if (!selected.includes(c)) selected.push(c);
    }
  }

  return selected;
}

function generateSVG(grid) {
  const ripplePoints = generateRipplePoints(grid);
  const maxRippleRadius = 100;

  let svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${WIDTH} ${HEIGHT}">
<defs>
  <style>
`;

  // Generate ripple animations for each point
  ripplePoints.forEach((point, i) => {
    const delay = i * 3.5;
    const duration = 8;
    svg += `
    .ripple-ring-${i} {
      animation: rippleExpand${i} ${duration}s ease-out infinite;
      animation-delay: ${delay}s;
      opacity: 0;
    }
    @keyframes rippleExpand${i} {
      0% { r: 0; opacity: 0; stroke-width: 2; }
      5% { opacity: 0.18; }
      40% { opacity: 0.08; }
      100% { r: ${maxRippleRadius}; opacity: 0; stroke-width: 0.5; }
    }

    .ripple-inner-${i} {
      animation: rippleInner${i} ${duration}s ease-out infinite;
      animation-delay: ${delay + 0.3}s;
      opacity: 0;
    }
    @keyframes rippleInner${i} {
      0% { r: 0; opacity: 0; }
      5% { opacity: 0.1; }
      35% { opacity: 0.04; }
      80% { r: ${maxRippleRadius * 0.65}; opacity: 0; }
      100% { opacity: 0; }
    }

    .ripple-dot-${i} {
      animation: rippleDot${i} ${duration}s ease-out infinite;
      animation-delay: ${delay}s;
      opacity: 0;
    }
    @keyframes rippleDot${i} {
      0% { opacity: 0.7; r: 2.5; }
      15% { opacity: 0; r: 1; }
      100% { opacity: 0; }
    }
`;
  });

  // Cell glow animations
  ripplePoints.forEach((point, i) => {
    const cx = PADDING + point.col * (CELL + GAP) + CELL / 2;
    const cy = PADDING + point.row * (CELL + GAP) + CELL / 2;
    const delay = i * 3.5;
    const duration = 8;

    for (let col = 0; col < grid.length; col++) {
      for (let row = 0; row < grid[col].length; row++) {
        const cellCx = PADDING + col * (CELL + GAP) + CELL / 2;
        const cellCy = PADDING + row * (CELL + GAP) + CELL / 2;
        const dist = Math.sqrt((cellCx - cx) ** 2 + (cellCy - cy) ** 2);

        if (dist < maxRippleRadius && dist > 0) {
          const cellDelay = delay + (dist / maxRippleRadius) * (duration * 0.8);
          const glowDuration = 1.5;
          const cellId = `c${col}-${row}`;

          svg += `
    .glow-${i}-${cellId} {
      animation: cellGlow ${glowDuration}s ease-in-out infinite;
      animation-delay: ${cellDelay.toFixed(2)}s;
    }`;
        }
      }
    }
  });

  svg += `
    @keyframes cellGlow {
      0%, 100% { filter: brightness(1); }
      50% { filter: brightness(1.6); }
    }
  </style>
</defs>

<!-- Background -->
<rect width="${WIDTH}" height="${HEIGHT}" fill="${COLORS.bg}" rx="6"/>

<!-- Contribution cells -->
`;

  // Draw cells
  for (let col = 0; col < grid.length; col++) {
    for (let row = 0; row < grid[col].length; row++) {
      const x = PADDING + col * (CELL + GAP);
      const y = PADDING + row * (CELL + GAP);
      const level = grid[col][row];
      const color = COLORS.levelsHex[level];

      // Collect glow classes for this cell
      const glowClasses = [];
      ripplePoints.forEach((point, i) => {
        const cx = PADDING + point.col * (CELL + GAP) + CELL / 2;
        const cy = PADDING + point.row * (CELL + GAP) + CELL / 2;
        const cellCx = PADDING + col * (CELL + GAP) + CELL / 2;
        const cellCy = PADDING + row * (CELL + GAP) + CELL / 2;
        const dist = Math.sqrt((cellCx - cx) ** 2 + (cellCy - cy) ** 2);
        if (dist < maxRippleRadius && dist > 0) {
          glowClasses.push(`glow-${i}-c${col}-${row}`);
        }
      });

      const classStr = glowClasses.length > 0 ? ` class="${glowClasses[0]}"` : '';
      svg += `  <rect${classStr} x="${x}" y="${y}" width="${CELL}" height="${CELL}" rx="2" fill="${color}"/>\n`;
    }
  }

  // Draw ripple effects
  svg += '\n<!-- Ripple effects -->\n';
  ripplePoints.forEach((point, i) => {
    const cx = PADDING + point.col * (CELL + GAP) + CELL / 2;
    const cy = PADDING + point.row * (CELL + GAP) + CELL / 2;

    svg += `  <circle class="ripple-ring-${i}" cx="${cx}" cy="${cy}" r="0" fill="none" stroke="${COLORS.ripple}" stroke-width="1.5"/>\n`;
    svg += `  <circle class="ripple-inner-${i}" cx="${cx}" cy="${cy}" r="0" fill="none" stroke="${COLORS.rippleHighlight}" stroke-width="1"/>\n`;
    svg += `  <circle class="ripple-dot-${i}" cx="${cx}" cy="${cy}" r="2" fill="${COLORS.rippleHighlight}"/>\n`;
  });

  svg += '</svg>';
  return svg;
}

async function main() {
  let grid;

  try {
    console.log(`Fetching contributions for ${USERNAME}...`);
    const weeks = await fetchContributions();

    // Convert to grid format [col][row]
    grid = [];
    const recentWeeks = weeks.slice(-COLS);
    for (let col = 0; col < recentWeeks.length; col++) {
      grid[col] = [];
      for (let row = 0; row < recentWeeks[col].contributionDays.length; row++) {
        grid[col][row] = levelToIndex(recentWeeks[col].contributionDays[row].contributionLevel);
      }
      // Pad if week is incomplete
      while (grid[col].length < ROWS) {
        grid[col].push(0);
      }
    }
    // Pad if fewer than 52 weeks
    while (grid.length < COLS) {
      grid.unshift(new Array(ROWS).fill(0));
    }

    console.log(`Fetched ${weeks.length} weeks of data.`);
  } catch (err) {
    console.error('Failed to fetch contributions, using generated data:', err.message);
    // Fallback: generate simulated data
    grid = [];
    for (let col = 0; col < COLS; col++) {
      grid[col] = [];
      for (let row = 0; row < ROWS; row++) {
        const r = Math.random();
        let level = 0;
        if (r > 0.50) level = 1;
        if (r > 0.70) level = 2;
        if (r > 0.85) level = 3;
        if (r > 0.94) level = 4;
        grid[col][row] = level;
      }
    }
  }

  const svg = generateSVG(grid);

  const outputDir = process.env.OUTPUT_DIR || './dist';
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  const outputPath = `${outputDir}/contribution-ripple.svg`;
  fs.writeFileSync(outputPath, svg);
  console.log(`Generated: ${outputPath}`);
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
