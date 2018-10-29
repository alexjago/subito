# Snippets

The following shell snippets might be useful. 

## Renaming 

First get the `rename` Perl script (`apt get rename` worked for me on Ubuntu). 

```sh
rename "s/*find_str*/*replace_str*/" /path/to/directory
```

Pass the `-n` flag before the substitution pattern to do a dry run.

## Collating

Subito outputs are collated by piece, but you might want to collate by part.

This gets all the files matching a pattern from a directory and its subdirectories, and copies them to a destination directory.

This one is probably Linux only, because GNU extensions.

I ran this one 10 times (D|S|A|T|B x MIDI|MP3), which is about as many as I would want to do before meta-automating it.

```sh
find /path/to/sourcedir/ -type f -name "base.ext" -print0 | xargs -0 cp -t /path/to/destdir/
```
