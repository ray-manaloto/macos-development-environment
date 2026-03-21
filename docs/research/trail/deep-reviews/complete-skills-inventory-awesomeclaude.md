# Complete Awesome Claude Skills Inventory

**Source:** https://awesomeclaude.ai/awesome-claude-skills
**Fetched:** 2026-03-21
**Total Skills:** 105 across 13 categories

## Overview

This is the definitive catalog of Claude Code skills indexed by awesomeclaude.ai. Skills are reusable capabilities that extend Claude's functionality for specific domains. Official Anthropic skills focus on document processing and web artifacts; community skills span DevOps, security, scientific research, media processing, and domain-specific tools.

## Quick Stats

- **Total Skills:** 105
- **Categories:** 13
- **Official Anthropic Skills:** 6 (all with 94.6k stars)
- **Highest Community Stars:** Claude Scientific Skills (15.1k), AWS Skills (209), Revealjs (228)
- **Installation:** GitHub repos (primary), npm packages, Claude Code plugins, MCP integration

## Installation Methods Discovered

1. **GitHub Repository** (most common)
   - Direct clone or GitHub URL in Claude Code
   - Example: `github.com/anthropics/skills/tree/main/skills/docx`

2. **npm Packages**
   - Global install: `npm install -g @skill-name`
   - Some skills published as standalone packages

3. **Claude Code Plugin/MCP**
   - Direct plugin integration via Claude settings
   - MCP server registration for advanced tools

4. **Cloud APIs**
   - Some skills wrap cloud services (Polaris DataInsight, ElevenLabs, VideoDB)

## Complete Skills by Category

### Document Skills (6)

- **docx** — Create, edit, analyze Word docs with tracked changes, comments, formatting. (94.6k stars)
- **pdf** — Extract text, tables, metadata, merge & annotate PDFs. (94.6k stars)
- **pptx** — Read, generate, and adjust slides, layouts, templates. (94.6k stars)
- **xlsx** — Spreadsheet manipulation: formulas, charts, data transformations. (94.6k stars)
- **revealjs-skill** — Generate polished, professional presentations using Reveal.js HTML framework. (228 stars)
- **polaris-datainsight-doc-extract** — Extract structured data from Office documents (DOCX, PPTX, XLSX, HWP, HWPX) using Polaris API. (2 stars)

### Development & Code Tools (27)

- **web-artifacts-builder** — Suite of tools for creating elaborate Claude.ai HTML artifacts using React, Tailwind CSS, shadcn/ui. (94.6k stars)
- **test-driven-development** — Use when implementing features or bugfixes, before writing implementation code. (87.2k stars)
- **using-git-worktrees** — Creates isolated git worktrees with smart directory selection and safety verification. (87.2k stars)
- **finishing-a-development-branch** — Guides completion of development work by presenting clear options and handling workflows. (87.2k stars)
- **aws-skills** — AWS development with CDK best practices, cost optimization, serverless patterns. (209 stars)
- **claude-starter** — Production-ready Claude Code config with 40 auto-activating skills, TOON format support. (63 stars)
- **design-auditor** — Analyzes design systems and component libraries for consistency and accessibility.
- **Playwright Skill** — Browser automation testing and web scraping capabilities.
- **agnix** — Linter for AI agent configurations; validates SKILL.md, CLAUDE.md, hooks, MCP configs. (114 stars)
- **azure-devops** — Manage Azure DevOps projects, repos, PRs, pipelines, work items via REST API.
- **charles-proxy-extract** — Extract and analyze HTTP requests from Charles Proxy sessions.
- **claude-code-terminal-title** — Dynamic terminal title management for Claude Code sessions.
- **email-html-mjml** — Generate responsive HTML emails using MJML framework.
- **hashicorp-agent-skills** — HashiCorp product integration (Terraform, Vault, Consul patterns).
- **jules** — AI-powered code review and quality analysis.
- **lightning-architecture-review** — Technical reference for Lightning Network architectures and LSP patterns.
- **move-code-quality-skill** — Analyzes Move language packages for Move 2024 Edition compliance.
- **oiloil-ui-ux-guide** — UI/UX design guidelines and pattern documentation.
- **plugin-authoring** — Create and publish Claude Code plugins with best practices.
- **pypict-claude-skill** — Design test cases using PICT (Pairwise Independent Combinatorial Testing). (48 stars)

### Data & Analysis (11)

- **csv-data-summarizer-claude-skill** — Summarize and analyze CSV data with statistical insights.
- **elicitation** — Extract and analyze requirements from documents and conversations.
- **kaggle-skill** — Access and analyze Kaggle datasets and competitions.
- **mssql** — Microsoft SQL Server query and database management.
- **mysql** — MySQL database operations and query optimization.
- **notebooklm** — Create interactive learning notebooks from documents and research.
- **octav-api-skill** — Octavia API integration for data processing.
- **postgres** — PostgreSQL database management and optimization.
- **recommendations** — Generate recommendations based on data analysis.
- **root-cause-tracing** — Systematic root cause analysis and debugging methodology.
- **x-twitter-scraper** — Twitter/X data extraction and analysis.

### Media & Content (13)

- **Claude Code Video Toolkit** — Video processing, analysis, and generation.
- **VideoDB Skills** — Video database integration and semantic search.
- **claude-epub-skill** — EPUB ebook creation and manipulation.
- **elevenlabs** — Text-to-speech synthesis with voice cloning.
- **find-scene** — Scene detection and video segment extraction.
- **google-tts** — Google Text-to-Speech integration.
- **image-enhancer** — Image upscaling, enhancement, and restoration.
- **imagen** — Google Imagen integration for image generation.
- **moltdj** — Music and audio processing.
- **video-downloader** — Download and process videos from various platforms.
- **video-prompting-skill** — Generate video content from text prompts.
- **youtube-transcript** — Extract and analyze YouTube video transcripts.
- **deapi-ai/claude-code-skills** — Collection of AI-focused development skills.

### Security & Web Testing (9)

- **Trail of Bits Security Skills** — Security analysis and vulnerability assessment.
- **VibeSec-Skill** — Vibrant security testing and penetration testing.
- **defense-in-depth** — Layered security architecture and threat modeling.
- **ffuf_claude_skill** — Fuzzing and web reconnaissance automation.
- **owasp-security** — OWASP security guidelines and best practices.
- **sanitize** — Input validation and sanitization patterns.
- **systematic-debugging** — Structured debugging methodology.
- **varlock-claude-skill** — Variable and dependency locking strategies.
- **webapp-testing** — Comprehensive web application testing automation.

### Collaboration & Project Management (14)

- **linear-claude-skill** — Linear issue tracking and project management.
- **linear-cli-skill** — Linear CLI command automation.
- **kanban-skill** — Kanban board management and workflow automation.
- **meeting-insights-analyzer** — Analyze meeting transcripts and extract action items.
- **outline** — Document organization and knowledge base management.
- **plannotator** — Planning and annotation tools for projects.
- **pm-skills** — Product manager workflows and templates.
- **Product-Manager-Skills** — PM-specific tools and best practices.
- **git-pushing** — Git workflow and push automation.
- **google-workspace-skills** — Google Docs, Sheets, Drive integration.
- **review-implementing** — Code review and implementation tracking.
- **test-fixing** — Test failure diagnosis and repair automation.
- **product-manager-skills** — Additional PM workflow support.
- **claude-skills** — General Claude workflow patterns.

### Scientific & Research Tools (4)

- **claude-scientific-skills** — Ready-to-use skills for research, science, engineering, analysis, finance. (15.1k stars)
- **deep-research** — Comprehensive research methodology and literature review.
- **manus** — Manual and documentation processing for technical fields.
- **materials-simulation-skills** — Materials science simulation and analysis.

### Writing & Research (6)

- **article-extractor** — Extract and summarize article content.
- **avoid-ai-writing** — Detect and replace AI-generated text patterns.
- **brainstorming** — Structured brainstorming and ideation tools.
- **content-research-writer** — Research-driven content creation.
- **family-history-research** — Genealogy and family history research.
- **internal-comms** — Internal communication and documentation.

### Health & Life Sciences (2)

- **claude-ally-health** — Health tracking and wellness coaching.
- **dna-claude-analysis** — Personal genome analysis from 23andMe/AncestryDNA. (17 categories of analysis)

### Learning & Knowledge (2)

- **ship-learn-next** — Continuous learning and skill development tracking.
- **tapestry** — Knowledge graph and learning pathway visualization.

### Utility & Automation (8)

- **agentfund-mcp** — Agent fund management and allocation.
- **file-organizer** — Intelligent file organization and categorization.
- **glitternetwork/pinme** — Pinboard and bookmarking integration.
- **invoice-organizer** — Invoice processing and accounting.
- **linkedin** — LinkedIn profile and networking automation.
- **skill-creator** — Generate new Claude Code skills from templates.
- **task-observer** — Task tracking and monitoring.
- **template-skill** — Skill templating and generation.

### Collections & Curated Sets (5)

- **@clawfu/mcp-skills** — Curated MCP server and skill collection.
- **OpenPaw** — Community-sourced OpenAI-compatible skills.
- **wondelai/skills** — Comprehensive skill set from Wondelai.
- **find-skills** — Skill discovery and search tools.
- **devmarketing-skills** — Developer marketing and advocacy skills.

### Articles & Blog Posts (1)

- **Agent Skills** — Educational content on Claude Code agent patterns.

## Key Findings

### Gaps in Skill Coverage

1. **Infrastructure as Code (chezmoi, mise, homebrew)**
   - No skills for dotfiles management
   - No skills for mise task automation
   - No skills for macOS-specific development environment setup
   - **Opportunity:** Package our chezmoi + mise integration as a community skill

2. **Language-Specific Development**
   - No dedicated Python project skills
   - No PyRight LSP setup skills
   - No linting/type-checking domain skills
   - **Opportunity:** Create pyright-lsp setup skill for macOS Python developers

3. **DevOps/Infrastructure Tooling**
   - Only cc-devops-skills covers DevOps comprehensively
   - AWS skills available but limited to CDK
   - No Kubernetes, Terraform-specific skills
   - No Docker/container orchestration skills

### High-Quality Skills Worth Studying

1. **claude-scientific-skills** (15.1k stars)
   - Comprehensive research/science/engineering domain
   - 60+ modular skills
   - Well-documented patterns

2. **Claude Code Agents** (72 stars on awesome-claude-code)
   - E2E development workflow
   - Subagent coordination patterns
   - QA automation

3. **cc-devops-skills** (114 stars)
   - Infrastructure as code patterns
   - Multi-platform coverage
   - Production-ready examples

4. **aws-skills** (209 stars)
   - Cloud-native patterns
   - Best practices integration
   - CDK examples

5. **claude-starter** (63 stars)
   - 40 auto-activating skills
   - 8-domain organization
   - Token optimization (TOON format)

### Skills Relevant to Our Project

**Current tech stack matches:**
- Development & Code Tools: test-driven-development, finishing-a-development-branch, using-git-worktrees
- Data & Analysis: postgres, notebooklm
- Security: owasp-security, defense-in-depth

**Skills we should create:**
1. `chezmoi-mise-macos-setup` — Automate dotfiles + environment setup
2. `pyright-lsp-configuration` — LSP server setup and diagnostics
3. `mde-python-project` — Our mde Python library and CLI tools

## Installation Path for Skills

Skills are primarily installed by:
1. Adding GitHub URLs to Claude Code plugin references
2. Using `claude plugin add <url>` or similar CLI
3. Direct GitHub repository cloning
4. npm package installation
5. MCP server registration

Example reference in SKILL.md:
```
references:
  - test-driven-development (github.com/obra/superpowers/tree/main/skills/test-driven-development)
  - using-git-worktrees (github.com/obra/superpowers/blob/main/skills/using-git-worktrees/)
```

## Related Resources

- **Awesome Claude Code:** https://awesomeclaude.ai/awesome-claude-code (40+ agent/workflow patterns)
- **Claude Code Cheatsheet:** https://awesomeclaude.ai/code-cheatsheet (installation, keyboard shortcuts)
- **Skills Directory:** https://github.com/skills-directory
- **Anthropic Official Skills:** https://github.com/anthropics/skills (docx, pdf, pptx, xlsx, web-artifacts-builder)
- **Superpowers Repository:** https://github.com/obra/superpowers (test-driven-development, git-worktrees, finishing-branch)
