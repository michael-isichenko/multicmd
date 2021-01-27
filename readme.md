# `multicmd`

[multicmd](https://github.com/michael-isichenko/multicmd) is a process scheduler written in python.  `multicmd` can be used as a module you can `import` in a script or as a standalone program.

`muticmd` runs multiple processes (defined by their command lines) in parallel on a multi-core host so that a specified number of cores N (and no more) are fully loaded.  N defaults to the number or cores returned by multiprocessing.cpu_count().

`multicmd.Run()` takes a list of commands to be executed in subshells. `multicmd.py` reads a file or stdin with one command per line.  Then first N commands are started.  As each process ends, a new one is started to keep the cores loaded, and so on until all commands are executed.

## Usage

```
$ multicmd.py -h
usage: multicmd.py [-h] [-n [NCPU]] [-t] [fname [fname ...]]

Run commands in file or stdin in parallel on specified number of cores

positional arguments:
  fname

optional arguments:
  -h, --help            show this help message and exit
  -n [NCPU], --ncpu [NCPU]
                        max number of parallel jobs (default: 8)
  -t, --test            print a bunch of commands for testing (default: False)

Examples:
  (for n in 8 7 6 5 4 3 2 1; do echo "sleep $n"; done) | /home/mbi/coding/putil/multicmd.py -n 4 # run 8 processes on 4 cores
  /home/mbi/coding/putil/multicmd.py -t | /home/mbi/coding/putil/multicmd.py # run some 1800 jobs with redirection t files using all available cores
```

## TODO

* Maybe: support execution on remote hosts -- waiting for remote processes is trickier
