import { Octokit } from '@octokit/rest';

export const DEFAULT_DAYS = 60;

export const DEFAULT_TAGS = [
  'dotfiles',
  'zsh',
  'zshrc',
  'starship',
  'tmux-conf',
  'sheldon',
  'chezmoi',
  'mise',
  'powerlevel10k',
  'claude-code',
  'macos',
  'homebrew',
  'nix-darwin',
  'home-manager',
  'terminal',
  'shell',
  'tmux',
  'neovim',
  'wezterm',
  'ghostty',
  'aerospace',
  'karabiner-elements',
];

const DAY_MS = 24 * 60 * 60 * 1000;

function toIsoDate(date) {
  return date.toISOString().slice(0, 10);
}

export function buildSinceDate(days = DEFAULT_DAYS, now = new Date()) {
  const safeDays = Number.isFinite(Number(days)) ? Number(days) : DEFAULT_DAYS;
  const sinceMs = now.getTime() - safeDays * DAY_MS;
  return toIsoDate(new Date(sinceMs));
}

export function buildTopicQuery(tag, sinceDate, minStars = 0, baseTopic = 'dotfiles') {
  const stars = Math.max(0, Number(minStars) || 0);
  const qualifiers = [];

  if (baseTopic && tag !== baseTopic) {
    qualifiers.push(`topic:${baseTopic}`);
  }

  qualifiers.push(`topic:${tag}`);
  qualifiers.push(`pushed:>=${sinceDate}`);
  qualifiers.push(`stars:>=${stars}`);
  qualifiers.push('archived:false');

  return qualifiers.join(' ');
}

function normalizeRepo(repo) {
  return {
    fullName: repo.full_name,
    stars: repo.stargazers_count,
    pushedAt: repo.pushed_at,
    url: repo.html_url,
  };
}

export function mergeAndRankRepositories(taggedResults) {
  const merged = new Map();

  for (const item of taggedResults) {
    const key = item.repo.fullName;

    if (!merged.has(key)) {
      merged.set(key, {
        fullName: item.repo.fullName,
        stars: item.repo.stars,
        pushedAt: item.repo.pushedAt,
        url: item.repo.url,
        matchedTags: [item.tag],
      });
      continue;
    }

    const existing = merged.get(key);
    if (!existing.matchedTags.includes(item.tag)) {
      existing.matchedTags.push(item.tag);
      existing.matchedTags.sort();
    }

    if (new Date(item.repo.pushedAt) > new Date(existing.pushedAt)) {
      existing.pushedAt = item.repo.pushedAt;
    }
    if (item.repo.stars > existing.stars) {
      existing.stars = item.repo.stars;
    }
  }

  return [...merged.values()].sort((a, b) => {
    if (a.pushedAt !== b.pushedAt) {
      return b.pushedAt.localeCompare(a.pushedAt);
    }
    if (a.stars !== b.stars) {
      return b.stars - a.stars;
    }
    return a.fullName.localeCompare(b.fullName);
  });
}

async function searchByTag({ octokit, tag, sinceDate, minStars, perTagLimit }) {
  const q = buildTopicQuery(tag, sinceDate, minStars);
  const response = await octokit.request('GET /search/repositories', {
    q,
    sort: 'updated',
    order: 'desc',
    per_page: perTagLimit,
  });

  return response.data.items.map((repo) => ({
    tag,
    repo: normalizeRepo(repo),
  }));
}

export async function discoverRepositories({
  octokit,
  tags = DEFAULT_TAGS,
  days = DEFAULT_DAYS,
  minStars = 0,
  perTagLimit = 30,
  now = new Date(),
  onTagError,
}) {
  if (!octokit || typeof octokit.request !== 'function') {
    throw new Error('discoverRepositories requires an octokit client with request()');
  }

  const sinceDate = buildSinceDate(days, now);
  const uniqueTags = [...new Set(tags.filter(Boolean).map((tag) => tag.trim()).filter(Boolean))];

  const allResults = [];
  for (const tag of uniqueTags) {
    try {
      const tagged = await searchByTag({
        octokit,
        tag,
        sinceDate,
        minStars,
        perTagLimit,
      });
      allResults.push(...tagged);
    } catch (error) {
      if (typeof onTagError === 'function') {
        onTagError({ tag, error });
      }
    }
  }

  return mergeAndRankRepositories(allResults);
}

export function createOctokit(token) {
  if (!token) {
    throw new Error('GitHub token is required. Set GITHUB_TOKEN or pass --token.');
  }

  return new Octokit({ auth: token });
}
