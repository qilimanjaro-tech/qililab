# How to set a global gitignore

> Extracted from https://gist.github.com/subfuzion/db7f57fff2fb6998a16c

There are certain files created by particular editors, IDEs, operating systems, etc., that do not belong in a repository. But adding system-specific files to the repo's `.gitignore` is considered a poor practice. This file should only exclude files and directories that are a part of the package that should not be versioned as well as files that are generated (and regenerated) as artifacts of a build process.

All other files should be in your own global gitignore file:

- Create a file called `.gitignore` in your home directory and add any filepath patterns you want to ignore.
- Tell git where your global gitignore file is.

> Note: The specific name and path you choose aren't important as long as you configure git to find it, as shown below.
> You could substitute `.config/git/ignore` for `.gitignore` in your home directory, if you prefer.

## Configuration

### Mac

    git config --global core.excludesfile ~/.gitignore

### Windows

    git config --global core.excludesfile "%USERPROFILE%\.gitignore"

If using Powershell (credit: @kupmanj):

    git config --global core.excludesFile "$Env:USERPROFILE\.gitignore"

This will result in an entry in your .gitconfig that looks like this:

    [core]
        excludesfile = {path-to-home-dir}/.gitignore

#### Confirm location

Particularly for Windows users, verify any filename was correctly parsed for quotes and expansion:

    git config --global core.excludesFile

#### Isn't there already a default global ignore?

Depending on your system, and whether the `XDG_CONFIG_HOME` environment variable is set, there might be a default location and
there might actually be a file at that location. The best practice is to ensure the file exists where you want and explicitly
tell git about it using `git config --global core.excludesFile`.

## Global .gitignore contents

Depending on your OS and tools, the following contains sample of what you might want to include. When you run `git status` before adding any files to your local repo, check to see if any files don't belong. Add them to your global gitignore as appropriate.

```text
# Node
npm-debug.log

# Mac
.DS_Store

# Windows
Thumbs.db

# WebStorm
.idea/

# vi
*~

# General
log/
*.log

# etc...
```

## Visual Studio Code

If you want search to ignore files that you've set in your local `.gitignore`, you must check:

- Search: Use Ignore Files

If you want search to ignore files that you've set in your global ignore, you must **also** check this:

- Search: Use Global Ignore Files

Or edit settings directly:

```text
"search.useIgnoreFiles": true,
"search.useGlobalIgnoreFiles": true
```

## Final notes

If you want to exclude files on a per-repo basis without modifying `.gitignore`, you can directly edit
`.git/info/exclude` in the repo. Nothing under the local `.git` directory is committed.

I find myself often creating "scratch" code that I don't want to commit. I do this enough that I found
it useful to add `scratch/` to my global ignore. I've personally never worked on a project where this is
an issue because a directory called `scratch` should not be a ignored, but if this is a concern, try
using `__scratch__` or something similar.

You might find useful ignore patterns for your projects here on [GitHub](https://github.com/github/gitignore).
