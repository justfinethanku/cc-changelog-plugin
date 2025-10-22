# The Definitive Guide to Claude Skills: Code vs Web vs Desktop
*Finally, a clear explanation of what the hell is going on*

> **⚠️ Documentation Status:** The official documentation is fragmented and sometimes contradictory. This guide is based on:
> - [Claude Code Skills Documentation](https://docs.claude.com/en/docs/claude-code/skills)
> - [Claude Support: How to Create Custom Skills](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills)
> - [Claude Support: Using Skills in Claude](https://support.claude.com/en/articles/12512180-using-skills-in-claude)
> - Practical testing and community experience
>
> **Skills Launch:** Claude Skills were officially announced on October 15, 2025
> **Last verified:** October 22, 2025

## Table of Contents
1. [The Products: What Are We Even Talking About?](#the-products)
2. [Quick Answer: Do I Need .zip Files?](#quick-answer)
3. [Claude Code Skills (The CLI Tool)](#claude-code-skills)
4. [claude.ai and Claude Desktop Skills (Web & Native App)](#claude-ai-desktop-skills)
5. [Why Everyone Is Confused](#why-everyone-is-confused)
6. [Practical Examples](#practical-examples)
7. [Sharing Skills via GitHub](#github-sharing)
8. [Quick Reference Cheat Sheet](#quick-reference)

## The Products: What Are We Even Talking About? {#the-products}

There are FOUR different Claude products that use "Skills", and they work differently:

| Product | What It Is | How Skills Work | .zip Required? | Documentation |
|---------|------------|-----------------|----------------|---------------|
| **Claude Code** | CLI tool that runs in your terminal | Directory-based, filesystem storage | **NO** ❌ | [Docs](https://docs.claude.com/en/docs/claude-code/skills) |
| **claude.ai** | Web interface in your browser | Upload .zip files through Settings | **YES** ✅ | [Support](https://support.claude.com/en/articles/12512180-using-skills-in-claude) |
| **Claude Desktop** | Native app for macOS/Windows | Upload .zip files through Settings | **YES** ✅ | [Support](https://support.claude.com/en/articles/12512180-using-skills-in-claude) |
| **Claude API** | Programmatic access for developers | Can use either format | **DEPENDS** 🤷 | [API Docs](https://docs.claude.com/en/api/skills-guide) |

**Important Clarification:**
- **claude.ai** is the web interface you access in your browser
- **Claude Desktop** is a separate native application you download and install on your computer
- Both claude.ai AND Claude Desktop require .zip files for skills
- Only Claude Code uses directory-based skills

## Quick Answer: Do I Need .zip Files? {#quick-answer}

- **Using Claude Code (CLI)?** → NO, just create directories
- **Using claude.ai (Web)?** → YES, you need .zip files
- **Using Claude Desktop (Native App)?** → YES, you need .zip files
- **Building a plugin for Claude Code?** → NO, use directories
- **Sharing skills with claude.ai/Desktop users?** → YES, create a .zip

## Claude Code Skills (The CLI Tool) {#claude-code-skills}

### How Claude Code Skills Work

According to the [official Claude Code documentation](https://docs.claude.com/en/docs/claude-code/skills), Claude Code uses a **filesystem-based approach**. Skills are directories with a `SKILL.md` file inside. The documentation states:

> "Skills are stored as directories containing a `SKILL.md` file."

**Notably absent from the Claude Code docs:** Any mention of .zip files, upload interfaces, or packaging requirements.

### Three Types of Claude Code Skills

#### 1. Personal Skills
- **Location:** `~/.claude/skills/skill-name/`
- **Scope:** Available across all your projects
- **Example:** `~/.claude/skills/git-wizard/SKILL.md`

#### 2. Project Skills
- **Location:** `.claude/skills/skill-name/`
- **Scope:** Specific to that project, shared via git
- **Example:** `my-project/.claude/skills/database-migrator/SKILL.md`

#### 3. Plugin Skills
- **Location:** Inside plugin repositories
- **Scope:** Distributed via plugin marketplaces
- **Example:** `plugin-repo/skills/commit/SKILL.md`

### Creating a Claude Code Skill

```bash
# Create the directory
mkdir -p ~/.claude/skills/my-awesome-skill

# Create the SKILL.md file
cat > ~/.claude/skills/my-awesome-skill/SKILL.md << 'EOF'
---
name: My Awesome Skill
description: Does awesome things when I need awesome stuff done
---

# My Awesome Skill

This skill helps you do awesome things.

## What This Skill Does

When you ask me to "make something awesome", I will:
1. Analyze the current level of awesomeness
2. Increase it by 1000%
3. Add explosions (optional)

## Implementation Details

[Your detailed instructions for Claude here]
EOF

# That's it. No .zip. No packaging. It just works.
```

### Distributing Claude Code Skills

#### Via Plugin (Like Your Changelog Plugin!)
```json
// In .claude-plugin/marketplace.json
{
  "plugins": [{
    "name": "my-plugin",
    "source": "./skills/my-skill"  // Just point to the directory!
  }]
}
```

#### Via Git (Project Skills)
```bash
# Just commit the directory
git add .claude/skills/my-skill/
git commit -m "Add awesome skill"
git push
# Team members get it automatically when they pull
```

## claude.ai and Claude Desktop Skills (Web & Native App) {#claude-ai-desktop-skills}

### How claude.ai and Claude Desktop Skills Work

According to [Claude Support documentation](https://support.claude.com/en/articles/12512180-using-skills-in-claude), both **claude.ai (web interface)** and **Claude Desktop (native app)** require skills to be **uploaded as .zip files** through their Settings interface:

> "To add custom skills, click 'Upload skill' and upload a ZIP file containing your skill folder."

This applies to:
- **claude.ai**: Access via browser at claude.ai → Settings → Capabilities
- **Claude Desktop**: Native app → Settings → Capabilities

Both use the same .zip upload mechanism, which is completely different from Claude Code's directory-based approach.

### Creating Skills for claude.ai or Claude Desktop

1. **Create your skill directory structure:**
```
my-desktop-skill/
├── SKILL.md (required)
├── scripts/
│   └── helper.py
└── resources/
    └── template.txt
```

2. **Create the SKILL.md file** (same format as Claude Code):
```markdown
---
name: My Desktop Skill
description: A skill for Claude Desktop
---

# Instructions here...
```

3. **Package it as a .zip:**
```bash
# Create the .zip file (Desktop REQUIRES this)
zip -r my-desktop-skill.zip my-desktop-skill/
```

4. **Upload through either interface:**

**For claude.ai (web):**
- Go to claude.ai in your browser
- Settings → Capabilities → Skills
- Click "Upload skill"
- Select your .zip file

**For Claude Desktop (native app):**
- Open Claude Desktop application
- Settings → Capabilities → Skills
- Click "Upload skill"
- Select your .zip file

### Limitations of claude.ai and Claude Desktop Skills

- **User-specific installation:** Each user must upload skills to their own account
- **Manual sharing:** You can share .zip files with others, but they must manually upload them
- **No automatic distribution:** Can't push skills to team members automatically
- **No version control:** Can't track changes via git (unless you version control the source before zipping)
- **Manual updates:** Must re-upload .zip for changes
- **No marketplace:** No plugin system like Claude Code

## Why Everyone Is Confused {#why-everyone-is-confused}

### The Perfect Storm of Confusion

1. **Same name, different systems:** All products call them "Skills"
2. **Same file format internally:** All use `SKILL.md` files
3. **Mixed documentation:** The [support articles](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills) don't clearly distinguish between platforms
4. **Community confusion:** Many people don't realize Claude Desktop is a separate native app, not the web interface
5. **Documentation gaps:** The [Claude Code docs](https://docs.claude.com/en/docs/claude-code/skills) never explicitly say "we don't use .zip files"
6. **Similar .zip requirements:** Both claude.ai AND Claude Desktop use .zip files, making it seem universal

### What We Can Infer

Based on the available documentation:

- **Claude Code documentation** only describes directory-based skills, never mentions .zip files
- **Claude Support articles** describe .zip uploads for both claude.ai (web) and Claude Desktop (native app)
- **Practical testing confirms:**
  - Claude Code works with directories only
  - claude.ai requires .zip uploads
  - Claude Desktop requires .zip uploads
- **The internal skill format (SKILL.md)** is the same across all platforms, but the packaging differs

### Documentation References

- [Claude Code Skills](https://docs.claude.com/en/docs/claude-code/skills) - Describes directory-based storage only
- [Creating Custom Skills](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills) - Describes .zip packaging for web
- [Using Skills in Claude](https://support.claude.com/en/articles/12512180-using-skills-in-claude) - Focuses on web interface upload

## Practical Examples {#practical-examples}

### Example 1: Creating a Git Commit Skill (Like Yours!)

#### For Claude Code (No .zip!)
```bash
# Create the skill directory
mkdir -p skills/commit

# Create SKILL.md
cat > skills/commit/SKILL.md << 'EOF'
---
name: Git Commit with Changelog
description: Creates detailed changelog when committing
---

# Skill content here...
EOF

# If distributing via plugin, reference in marketplace.json:
# "source": "./skills/commit"

# That's it! No .zip needed!
```

#### For claude.ai or Claude Desktop (Requires .zip)
```bash
# Same skill, but now we need to package it
zip -r commit-skill.zip skills/commit/

# For claude.ai: Upload through browser at claude.ai → Settings
# For Claude Desktop: Upload through native app → Settings
```

### Example 2: Installing Skills

#### Claude Code Methods
```bash
# Method 1: Personal skill (manual)
cp -r downloaded-skill ~/.claude/skills/

# Method 2: Project skill (git)
git clone repo-with-skills
# .claude/skills/ automatically available

# Method 3: Plugin (marketplace)
/plugin marketplace add https://github.com/user/marketplace
/plugin install skill-name
```

#### claude.ai and Claude Desktop Method
```
For claude.ai (web):
1. Download skill.zip
2. Go to claude.ai in your browser
3. Settings → Capabilities → Skills → Upload skill
4. Select skill.zip

For Claude Desktop (native app):
1. Download skill.zip
2. Open Claude Desktop application
3. Settings → Capabilities → Skills → Upload skill
4. Select skill.zip

Note: Both require .zip files - that's the ONLY way for these platforms
```

## Sharing Skills via GitHub {#github-sharing}

### The Complete Guide to GitHub Skill Distribution

GitHub is the natural home for Claude Code skills since they're just directories. Here's everything you need to know about sharing skills through GitHub.

### Method 1: Project Skills (Team Sharing)

The simplest way - just commit skills to your project repository:

```bash
# Create skill in your project
mkdir -p .claude/skills/database-helper
echo '---
name: Database Helper
description: Helps with database operations
---

# Skill instructions...' > .claude/skills/database-helper/SKILL.md

# Commit and push
git add .claude/skills/
git commit -m "Add database helper skill"
git push

# Team members automatically get it
git pull  # Boom, they have the skill
```

**Pros:**
- Zero configuration needed
- Automatically versioned with your code
- Team gets updates through normal git workflow
- Can have project-specific skills

**Cons:**
- Only available within that specific project
- Can't easily share across different projects

### Method 2: Standalone Skill Repository

Create a dedicated repository just for your skills:

```bash
# Create a new repo for your skills collection
mkdir my-claude-skills
cd my-claude-skills

# Organize skills by category
mkdir -p skills/{git,database,testing,deployment}

# Add your skills
cat > skills/git/auto-commit/SKILL.md << 'EOF'
---
name: Auto Commit Helper
description: Intelligently creates commits with proper messages
---
# Content...
EOF

# Create a README for humans
cat > README.md << 'EOF'
# My Claude Code Skills Collection

## Installation

### Option 1: Clone entire collection
```bash
git clone https://github.com/username/my-claude-skills
cp -r my-claude-skills/skills/* ~/.claude/skills/
```

### Option 2: Install specific skill
```bash
curl -sL https://raw.githubusercontent.com/username/my-claude-skills/main/skills/git/auto-commit/SKILL.md \
  -o ~/.claude/skills/auto-commit/SKILL.md
```
EOF

# Push to GitHub
git init
git add .
git commit -m "Initial skills collection"
git remote add origin https://github.com/username/my-claude-skills
git push -u origin main
```

### Method 3: Plugin Distribution (The Professional Way)

Turn your skills into a Claude Code plugin for easy installation:

```bash
# Repository structure
my-skill-plugin/
├── .claude-plugin/
│   ├── plugin.json           # Plugin metadata
│   └── marketplace.json       # If creating a marketplace
├── skills/
│   ├── skill-one/
│   │   └── SKILL.md
│   └── skill-two/
│       ├── SKILL.md
│       └── helpers/
│           └── script.py
└── README.md

# Create marketplace.json
cat > .claude-plugin/marketplace.json << 'EOF'
{
  "name": "awesome-skills-marketplace",
  "owner": {
    "name": "Your Name",
    "email": "you@example.com"
  },
  "plugins": [
    {
      "name": "awesome-skills",
      "source": "./skills",
      "description": "Collection of awesome skills",
      "version": "1.0.0"
    }
  ]
}
EOF

# Users install with:
# /plugin marketplace add https://github.com/username/my-skill-plugin
# /plugin install awesome-skills
```

### Method 4: GitHub Releases (For Versioning)

Use GitHub releases for versioned skill distributions:

```bash
# Tag a version
git tag -a v1.0.0 -m "First stable release of skills"
git push origin v1.0.0

# Create a release on GitHub with:
# 1. Changelog of what's new
# 2. Installation instructions
# 3. Optional: .zip download for Desktop users

# Users can then install specific versions:
curl -sL https://github.com/username/skills/archive/v1.0.0.tar.gz | tar -xz
cp -r skills-1.0.0/skills/* ~/.claude/skills/
```

### GitHub Best Practices for Skills

#### 1. Repository Structure
```
your-skills-repo/
├── README.md                 # Human-readable docs
├── LICENSE                   # MIT, Apache, etc.
├── CHANGELOG.md             # Version history
├── skills/                  # All skills go here
│   ├── category-one/
│   │   └── skill-name/
│   │       └── SKILL.md
│   └── category-two/
│       └── another-skill/
│           ├── SKILL.md
│           └── resources/
└── examples/                # Usage examples
```

#### 2. README Template
```markdown
# [Your Name]'s Claude Code Skills

## Available Skills

- **git-wizard**: Advanced git operations helper
- **test-runner**: Intelligent test execution and debugging
- **doc-writer**: Automatic documentation generation

## Installation

### All Skills
\`\`\`bash
git clone https://github.com/[username]/[repo]
cp -r [repo]/skills/* ~/.claude/skills/
\`\`\`

### Individual Skill
\`\`\`bash
cp -r [repo]/skills/[skill-name] ~/.claude/skills/
\`\`\`

### As Plugin
\`\`\`
/plugin marketplace add https://github.com/[username]/[repo]
/plugin install [plugin-name]
\`\`\`

## Requirements
- Claude Code v0.1.22+
- Git (for cloning)

## Contributing
PRs welcome! Please test your skills before submitting.

## License
MIT - Use these however you want
```

#### 3. Licensing Considerations
```bash
# Add a LICENSE file
cat > LICENSE << 'EOF'
MIT License

Copyright (c) 2025 Your Name

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction...
EOF
```

#### 4. Testing Your Skills
```bash
# Before pushing, test locally
cp -r skills/my-new-skill ~/.claude/skills/
# Test in Claude Code
# If it works, push to GitHub
```

### Sharing Skills for claude.ai and Claude Desktop Users

Since claude.ai and Claude Desktop users need .zip files, you can share skills with them through GitHub:

```bash
# Create a script for Desktop users
cat > package-for-desktop.sh << 'EOF'
#!/bin/bash
# Package skills for Claude Desktop users

for skill_dir in skills/*/; do
  skill_name=$(basename "$skill_dir")
  zip -r "desktop-zips/${skill_name}.zip" "$skill_dir"
done
echo "Desktop .zip files created in desktop-zips/"
EOF

chmod +x package-for-desktop.sh
./package-for-desktop.sh

# Commit the zips (controversial, but convenient)
git add desktop-zips/
git commit -m "Add Desktop-compatible .zip files"
```

Or use GitHub Actions to automatically create .zip files:

```yaml
# .github/workflows/package-desktop.yml
name: Package for Desktop
on:
  push:
    branches: [main]

jobs:
  package:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Create Desktop ZIPs
        run: |
          mkdir desktop-zips
          for dir in skills/*/; do
            zip -r "desktop-zips/$(basename $dir).zip" "$dir"
          done
      - name: Upload artifacts
        uses: actions/upload-artifact@v2
        with:
          name: desktop-skills
          path: desktop-zips/*.zip
```

### Security and Trust

When sharing skills publicly:

1. **Be transparent:** Clearly document what your skills do
2. **No secrets:** Never put API keys or credentials in skills
3. **Test thoroughly:** Make sure skills work before publishing
4. **Version properly:** Use semantic versioning for releases
5. **Accept feedback:** Enable issues on your repository
6. **Security policy:** Consider adding a SECURITY.md file

### The GitHub Advantage

Why GitHub is perfect for Claude Code skills:

- **Version Control:** Track every change to your skills
- **Collaboration:** Others can contribute improvements
- **Discovery:** People can find your skills through search
- **Free hosting:** No need to pay for distribution
- **CI/CD:** Automate testing and packaging
- **Issues/PRs:** Get feedback and contributions
- **Stars:** Internet points that actually mean something

### Real-World Examples

Check out these actual skill repositories:

```bash
# Official Anthropic skills
https://github.com/anthropics/skills

# Community collections
https://github.com/travisvn/awesome-claude-skills
https://github.com/simonw/claude-skills

# Your changelog plugin (perfect example!)
https://github.com/justfinethanku/cc-changelog-plugin
```

## Quick Reference Cheat Sheet {#quick-reference}

### "I want to..." Decision Tree

| I want to... | Product | What to do |
|--------------|---------|------------|
| Use skills in my terminal | Claude Code | Create directories in `~/.claude/skills/` |
| Share skills with my team automatically | Claude Code | Put in `.claude/skills/`, commit to git |
| Distribute skills publicly | Claude Code | Create plugin with marketplace.json |
| Use skills on claude.ai (browser) | claude.ai | Create .zip, upload through Settings |
| Use skills in desktop app | Claude Desktop | Create .zip, upload through Settings |
| Share .zip skills with others | claude.ai/Desktop | Share .zip file, recipients upload manually |
| Build reusable automation | Claude Code | Create skill directory, no .zip needed |

### File Paths Quick Reference

```bash
# Claude Code (CLI)
~/.claude/skills/skill-name/         # Personal skills
./project/.claude/skills/skill-name/ # Project skills
./plugin/skills/skill-name/           # Plugin skills

# claude.ai (Web Browser)
# No filesystem access - must upload .zip through web UI at claude.ai

# Claude Desktop (Native App)
# No filesystem access - must upload .zip through app Settings
```

### The Golden Rules

1. **Claude Code = Directories** (no .zip)
2. **claude.ai = .zip files** (required)
3. **Claude Desktop = .zip files** (required)
4. **Same SKILL.md format** (but different packaging)
5. **Not interchangeable** (can't use .zip skills in Code without extraction)
6. **When in doubt:** Code is filesystem-based, claude.ai and Desktop are upload-based

## Final Words

Based on available documentation and practical testing:

- **Claude Code (CLI)** uses directory-based skills according to [official docs](https://docs.claude.com/en/docs/claude-code/skills)
- **claude.ai (Web)** requires .zip uploads per [support articles](https://support.claude.com/en/articles/12512180-using-skills-in-claude)
- **Claude Desktop (Native App)** also requires .zip uploads per the same support articles
- **The documentation is fragmented** and doesn't explicitly distinguish between these platforms

The confusion stems from:
1. People not realizing Claude Desktop is a separate native app, not the web interface
2. Both claude.ai AND Claude Desktop requiring .zip files, making it seem universal
3. Incomplete documentation that doesn't clearly distinguish platforms
4. Community assumptions spreading without platform context

If someone tells you Claude Code needs .zip files, ask them to show you where in the [Claude Code documentation](https://docs.claude.com/en/docs/claude-code/skills) it mentions .zip files (spoiler: it doesn't). They're likely thinking of claude.ai, Claude Desktop, or conflating all three products.

And yes, this approach is still way cooler than anything Mike Dion proposed.

---

*Created with frustration and citations by someone who dug through all the contradictory documentation*

## Additional Resources

- [Claude Code Documentation](https://docs.claude.com/en/docs/claude-code/overview)
- [Claude Support Center](https://support.claude.com/)
- [Official Skills Repository](https://github.com/anthropics/skills)
- [Claude Code GitHub](https://github.com/anthropics/claude-code)
- [Community Skills Collection](https://github.com/travisvn/awesome-claude-skills)