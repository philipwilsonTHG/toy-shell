# Dynamic Prompt Formatting

The Python Shell now supports rich, dynamic prompt formatting with various substitution variables and color options. This feature allows you to customize your shell prompt to display information that's most relevant to your workflow.

## Basic Usage

To customize your prompt, edit the `prompt_template` setting in your `~/.pshrc` file:

```
prompt_template=\[blue]\u@\h\[reset]:\[cyan]\w\[reset] \[green]\g\[reset]\$
```

## Available Variables

The prompt formatter supports the following escape sequences:

| Variable | Description | Example |
|----------|-------------|---------|
| `\u` | Current username | `john` |
| `\h` | Short hostname | `macbook` |
| `\H` | Full hostname (FQDN) | `macbook.local` |
| `\w` | Current working directory (with ~ for $HOME) | `~/src/project` |
| `\W` | Basename of current directory | `project` |
| `\$` | `#` for root user, `$` for regular user | `$` |
| `\?` | Exit status of last command (colorized) | <span style="color:green">0</span> or <span style="color:red">1</span> |
| `\e` | Raw exit status without color | `0` |
| `\t` | Current time (24-hour format) | `15:42:07` |
| `\T` | Current time (12-hour format) | `03:42:07 PM` |
| `\d` | Current date | `2025-03-18` |
| `\g` | Git branch name (if in a repo) | `(main)` |
| `\j` | Number of background jobs | `2` |
| `\!` | History number of current command | `42` |
| `\v` | Python virtual environment name (if active) | `(venv)` |

## Color Formatting

You can apply colors to parts of your prompt using the following syntax:

```
\[color_name]text\[reset]
```

Available colors:

| Color Name | Effect |
|------------|--------|
| `reset` | Reset all formatting |
| `black` | Black text |
| `red` | Red text |
| `green` | Green text |
| `yellow` | Yellow text |
| `blue` | Blue text |
| `magenta` | Magenta text |
| `cyan` | Cyan text |
| `white` | White text |
| `bold` | Bold text |
| `italic` | Italic text (if terminal supports it) |
| `underline` | Underlined text |

## Example Prompts

1. Standard bash-like prompt:
   ```
   prompt_template=\u@\h:\w\$
   ```

2. Colorful prompt with exit status:
   ```
   prompt_template=\[green]\u@\h\[reset]:\[blue]\w\[reset] [\?] \$
   ```

3. Minimal prompt with git information:
   ```
   prompt_template=\W \[cyan]\g\[reset]\$
   ```

4. Full-featured prompt with time and virtualenv:
   ```
   prompt_template=[\[yellow]\t\[reset]] \[magenta]\v\[reset]\[green]\u@\h\[reset]:\[blue]\w\[reset] \[cyan]\g\[reset]\$
   ```

5. Show jobs and history number:
   ```
   prompt_template=[\!][\j] \[green]\u\[reset]:\[blue]\w\[reset]\$
   ```

## Configuration

The prompt template is defined in the `~/.pshrc` configuration file using the `prompt_template` setting:

```
prompt_template=your_preferred_template_here
```

If not set, the default template is used: `\[blue]\u@\h\[reset]:\[cyan]\w\[reset] \[green]\g\[reset]\$`

You can temporarily change your prompt by setting a new template in your shell session:
```
$ config set prompt_template "\[red][\t] \u\[reset]:\w\$ "
```

## Technical Implementation

The prompt formatting system uses a template parser that processes escape sequences and calls the appropriate handler functions. The system is designed to efficiently cache values and prevent repeated expensive operations (like git branch detection).

All colors are implemented using ANSI escape sequences and should work in most modern terminals that support color output.