# BDD Test Design

## Feature: Discover modern dotfiles-related repositories

Scenario: Default recency window
Given the user does not provide days
When discovery runs
Then the query uses a 60-day updated window

Scenario: Topic and tag filtering
Given the user provides tags including dotfiles and zsh
When discovery runs
Then results include repos matching one or more configured tags/topics

Scenario: Structured output
Given discovery returns repositories
When output is rendered
Then each item includes name, owner, url, updatedAt, matchedTags, and score

Scenario: Rate limiting
Given GitHub API responds with secondary rate limit
When discovery retries
Then retries back off and final output includes rate-limit metadata
