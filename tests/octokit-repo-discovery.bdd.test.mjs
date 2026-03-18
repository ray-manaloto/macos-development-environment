import test from 'node:test';
import assert from 'node:assert/strict';

import {
  DEFAULT_TAGS,
  buildSinceDate,
  buildTopicQuery,
  mergeAndRankRepositories,
  discoverRepositories,
} from '../scripts/octokit/repo-discovery.mjs';

test('Given no explicit tags When loading defaults Then includes requested extra tags', () => {
  const expectedTags = [
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

  for (const tag of expectedTags) {
    assert.equal(DEFAULT_TAGS.includes(tag), true, `missing default tag: ${tag}`);
  }
});

test('Given a fixed now date When building cutoff Then defaults to 60 days', () => {
  const now = new Date('2026-02-28T20:00:00Z');
  assert.equal(buildSinceDate(undefined, now), '2025-12-30');
});

test('Given tag and cutoff When building topic query Then includes pushed and archived constraints', () => {
  const query = buildTopicQuery('dotfiles', '2025-12-30', 10);
  assert.equal(
    query,
    'topic:dotfiles pushed:>=2025-12-30 stars:>=10 archived:false'
  );
});

test('Given non-dotfiles tag When building topic query Then scopes results to dotfiles bootstrap repos', () => {
  const query = buildTopicQuery('mise', '2025-12-30', 5);
  assert.equal(
    query,
    'topic:dotfiles topic:mise pushed:>=2025-12-30 stars:>=5 archived:false'
  );
});

test('Given overlapping repos across tags When merging Then deduplicates and merges matched tags', () => {
  const merged = mergeAndRankRepositories([
    {
      tag: 'dotfiles',
      repo: {
        fullName: 'owner/repo-a',
        stars: 100,
        pushedAt: '2026-02-28T10:00:00Z',
        url: 'https://github.com/owner/repo-a',
      },
    },
    {
      tag: 'mise',
      repo: {
        fullName: 'owner/repo-a',
        stars: 100,
        pushedAt: '2026-02-28T10:00:00Z',
        url: 'https://github.com/owner/repo-a',
      },
    },
    {
      tag: 'zsh',
      repo: {
        fullName: 'owner/repo-b',
        stars: 40,
        pushedAt: '2026-02-27T10:00:00Z',
        url: 'https://github.com/owner/repo-b',
      },
    },
  ]);

  assert.equal(merged.length, 2);
  assert.equal(merged[0].fullName, 'owner/repo-a');
  assert.deepEqual(merged[0].matchedTags, ['dotfiles', 'mise']);
});

test('Given equal pushedAt When ranking Then sorts by stars desc then fullName asc', () => {
  const merged = mergeAndRankRepositories([
    {
      tag: 'dotfiles',
      repo: {
        fullName: 'owner/b-repo',
        stars: 50,
        pushedAt: '2026-02-28T10:00:00Z',
        url: 'https://github.com/owner/b-repo',
      },
    },
    {
      tag: 'dotfiles',
      repo: {
        fullName: 'owner/a-repo',
        stars: 50,
        pushedAt: '2026-02-28T10:00:00Z',
        url: 'https://github.com/owner/a-repo',
      },
    },
    {
      tag: 'dotfiles',
      repo: {
        fullName: 'owner/c-repo',
        stars: 100,
        pushedAt: '2026-02-28T10:00:00Z',
        url: 'https://github.com/owner/c-repo',
      },
    },
  ]);

  assert.deepEqual(
    merged.map((repo) => repo.fullName),
    ['owner/c-repo', 'owner/a-repo', 'owner/b-repo']
  );
});

test('Given mocked octokit search results When discovering Then returns normalized merged repos', async () => {
  const calls = [];
  const octokit = {
    request: async (_route, params) => {
      calls.push(params.q);

      if (params.q.includes('topic:mise')) {
        return {
          data: {
            items: [
              {
                full_name: 'owner/repo-a',
                stargazers_count: 10,
                pushed_at: '2026-02-28T11:00:00Z',
                html_url: 'https://github.com/owner/repo-a',
              },
              {
                full_name: 'owner/repo-b',
                stargazers_count: 20,
                pushed_at: '2026-02-28T12:00:00Z',
                html_url: 'https://github.com/owner/repo-b',
              },
            ],
          },
        };
      }

      if (params.q.includes('topic:dotfiles')) {
        return {
          data: {
            items: [
              {
                full_name: 'owner/repo-a',
                stargazers_count: 10,
                pushed_at: '2026-02-28T11:00:00Z',
                html_url: 'https://github.com/owner/repo-a',
              },
            ],
          },
        };
      }

      return { data: { items: [] } };
    },
  };

  const repos = await discoverRepositories({
    octokit,
    tags: ['dotfiles', 'mise'],
    days: 60,
    minStars: 0,
    perTagLimit: 10,
    now: new Date('2026-02-28T20:00:00Z'),
  });

  assert.equal(calls.length, 2);
  assert.equal(repos.length, 2);
  assert.equal(repos[0].fullName, 'owner/repo-b');
  assert.deepEqual(repos[1].matchedTags, ['dotfiles', 'mise']);
});

test('Given one tag request fails When discovering Then returns partial results and reports tag error', async () => {
  const errors = [];
  const octokit = {
    request: async (_route, params) => {
      if (params.q.includes('topic:mise')) {
        throw new Error('rate limited');
      }

      return {
        data: {
          items: [
            {
              full_name: 'owner/repo-a',
              stargazers_count: 10,
              pushed_at: '2026-02-28T11:00:00Z',
              html_url: 'https://github.com/owner/repo-a',
            },
          ],
        },
      };
    },
  };

  const repos = await discoverRepositories({
    octokit,
    tags: ['dotfiles', 'mise'],
    now: new Date('2026-02-28T20:00:00Z'),
    onTagError: (payload) => errors.push(payload),
  });

  assert.equal(repos.length, 1);
  assert.equal(repos[0].fullName, 'owner/repo-a');
  assert.equal(errors.length, 1);
  assert.equal(errors[0].tag, 'mise');
  assert.match(errors[0].error.message, /rate limited/);
});
