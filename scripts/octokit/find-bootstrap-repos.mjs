#!/usr/bin/env node

import {
  DEFAULT_DAYS,
  DEFAULT_TAGS,
  createOctokit,
  discoverRepositories,
} from './repo-discovery.mjs';

function parseArgs(argv) {
  const args = {
    days: DEFAULT_DAYS,
    tags: DEFAULT_TAGS,
    minStars: 0,
    perTagLimit: 30,
    format: 'table',
    token: process.env.GITHUB_TOKEN,
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    const next = argv[i + 1];

    if (arg === '--days' || arg === '-d') {
      args.days = Number(next);
      i += 1;
      continue;
    }

    if (arg === '--tags') {
      args.tags = next.split(',').map((tag) => tag.trim()).filter(Boolean);
      i += 1;
      continue;
    }

    if (arg === '--min-stars') {
      args.minStars = Number(next);
      i += 1;
      continue;
    }

    if (arg === '--per-tag-limit') {
      args.perTagLimit = Number(next);
      i += 1;
      continue;
    }

    if (arg === '--format') {
      args.format = next;
      i += 1;
      continue;
    }

    if (arg === '--token') {
      args.token = next;
      i += 1;
      continue;
    }

    if (arg === '--help' || arg === '-h') {
      args.help = true;
    }
  }

  return args;
}

function printHelp() {
  console.log(`Usage: node scripts/octokit/find-bootstrap-repos.mjs [options]

Options:
  -d, --days <n>           Last N days filter (default: ${DEFAULT_DAYS})
  --tags <csv>             Comma-separated topics (default: built-in tag set)
  --min-stars <n>          Minimum stars filter in query (default: 0)
  --per-tag-limit <n>      Max results requested per topic (default: 30)
  --format <table|json>    Output format (default: table)
  --token <token>          GitHub token (default: GITHUB_TOKEN env)
  -h, --help               Show help
`);
}

function printTable(repos) {
  const lines = repos.map((repo) => [
    repo.fullName,
    String(repo.stars),
    repo.pushedAt,
    repo.matchedTags.join(','),
    repo.url,
  ].join('\t'));

  console.log('fullName\tstars\tpushedAt\tmatchedTags\turl');
  for (const line of lines) {
    console.log(line);
  }
}

async function main() {
  const args = parseArgs(process.argv.slice(2));

  if (args.help) {
    printHelp();
    return;
  }

  if (!Number.isFinite(args.days) || args.days < 0) {
    throw new Error('--days must be a non-negative number');
  }

  if (!Number.isFinite(args.minStars) || args.minStars < 0) {
    throw new Error('--min-stars must be a non-negative number');
  }

  if (!Number.isFinite(args.perTagLimit) || args.perTagLimit <= 0) {
    throw new Error('--per-tag-limit must be a positive number');
  }

  if (args.format !== 'table' && args.format !== 'json') {
    throw new Error('--format must be one of: table, json');
  }

  const octokit = createOctokit(args.token);

  const repos = await discoverRepositories({
    octokit,
    tags: args.tags,
    days: args.days,
    minStars: args.minStars,
    perTagLimit: args.perTagLimit,
    onTagError: ({ tag, error }) => {
      console.error(`Warning: tag "${tag}" failed: ${error.message}`);
    },
  });

  if (args.format === 'json') {
    console.log(JSON.stringify(repos, null, 2));
    return;
  }

  printTable(repos);
}

main().catch((error) => {
  console.error(`Error: ${error.message}`);
  process.exit(1);
});
