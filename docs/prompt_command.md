# Prompt Command

The `prompt` command allows you to change or display the shell prompt interactively.

## Usage

```
prompt                    # Display current prompt template
prompt "new_template"     # Set prompt to the given template
prompt -h, --help         # Show help with available prompt variables
prompt -l, --list         # List predefined prompt templates
prompt name               # Use a predefined prompt by name
```

## Prompt Variables

The prompt template supports the following variables:

| Variable | Description                            |
|----------|----------------------------------------|
| \u       | Username                               |
| \h       | Hostname (short)                       |
| \H       | Hostname (FQDN)                        |
| \w       | Current working directory              |
| \W       | Basename of current directory          |
| \$       | # for root, $ for regular user         |
| \?       | Exit status (colored)                  |
| \e       | Raw exit status                        |
| \t       | Current time (HH:MM:SS)                |
| \T       | Current time (12-hour)                 |
| \d       | Current date                           |
| \g       | Git branch                             |
| \j       | Number of jobs                         |
| \!       | History number                         |
| \v       | Python virtualenv                      |

## Color Support

You can add colors to your prompt using the `\[color]` syntax. To reset the color, use `\[reset]`.

Available colors:
- black
- red
- green
- yellow
- blue
- magenta
- cyan
- white
- bold
- italic
- underline

## Predefined Prompts

The `prompt` command includes several predefined prompts:

| Name     | Description                            |
|----------|----------------------------------------|
| default  | Blue username@hostname, cyan directory, green git branch |
| minimal  | Just the $ prompt character            |
| basic    | username@hostname:directory$           |
| path     | Just directory and $                   |
| full     | Time, username, hostname, directory, git branch, jobs |
| git      | Directory with green git branch        |
| status   | Exit status and directory              |

## Examples

```shell
# Set a simple minimal prompt
prompt "\\$ "

# Use a predefined prompt
prompt git

# Create a custom colored prompt showing date, directory, and exit status
prompt "\\[blue]\\d\\[reset] \\[cyan]\\w\\[reset] [\\?]\\$ "

# Create a prompt showing Python virtualenv and git branch
prompt "\\v \\w \\[green]\\g\\[reset]\\$ "
```

## Persistence

The prompt setting is valid for the current shell session only. To make it persistent, add the prompt command to your `~/.pshrc` file:

```
prompt_template=\[blue]\u@\h\[reset]:\[cyan]\w\[reset] \[green]\g\[reset]\$ 
```

Or alternatively, add the prompt command to your startup script:

```shell
# In ~/.pshrc
prompt git
```