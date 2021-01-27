#!/usr/local/miniconda3/bin/python

import subprocess, os, sys, time

_cores = 0
def CountCores():
    global _cores
    if _cores == 0:
        if False:
            _cores = sum(1 for line in open("/proc/cpuinfo") if line.startswith("processor")) # linux only
        else:
            import multiprocessing
            _cores = multiprocessing.cpu_count()
    return _cores

def NiceTime(sec):
    s = ''
    if sec >= 3600:
        h = int(sec/3600)
        sec -= h*3600
        s += f'{h}h'
    if sec >= 60:
        m = int(sec/60)
        sec -= m*60
        s += f'{m}m'
    s += f'{int(sec)}s'
    return s

def RunByOne(cmd_list):
    pids = {}
    for cmd in cmd_list:
        proc = subprocess.Popen(cmd, shell=True)
        print(f'# START({proc.pid}):  {cmd}')
        try:
            pid, retval = os.wait()
        except os.error: # OSError: [Errno 10] No child processes
            continue

def Run(cmd_list, ncpu=0):
    """
    Run commands from list while loading specified number of cpus [CountCores()].
    The commands are run in sub-shells and can use '>' redirection and other shell features.
    Print START/END messages for the managed processes to stdout.  Some END messages can be missing due to a race condition.
    """
    if 0 == ncpu:
        ncpu = CountCores()
    cmd_to_pid = {}
    pid_to_cmd = {}
    pid_to_time = {}
    for cmd in cmd_list:
        assert cmd not in cmd_to_pid, f'duplicate cmd: {cmd}'
        cmd_to_pid[cmd] = 0 # 0 = not started, >0 = started
    assert len(cmd_list) == len(cmd_to_pid), f'detected {len(cmd_list)-len(cmd_to_pid)}/{len(cmd_list)} command duplicates'
    while True:
        for cmd in [cmd for cmd in cmd_list if cmd_to_pid[cmd] == 0]:
            if len(pid_to_cmd) >= ncpu:
                break
            proc = subprocess.Popen(cmd, shell=True)
            print(f'# [{len(pid_to_cmd)}] START({proc.pid}):  {cmd}')
            pid_to_cmd[proc.pid] = cmd
            cmd_to_pid[cmd] = proc.pid
            pid_to_time[proc.pid] = time.time()
        if 0 == len(pid_to_cmd):
            break
        try:
            pid, retval = os.wait()
        except os.error: # childProcessError: [Errno 10] No child processes
            # first few Popen processes can complete before we have a chance to wait()
            # the wait() can be enforced via a context manager like 'with Popen(...) as proc:', but that will defeat multitasking
            if False and len(pid_to_cmd):
                raise os.error(f'os.wait error with {len(pid_to_cmd)} not waited: {pid_to_cmd}')
            break
        elapsed = time.time() - pid_to_time[pid]
        cmd = pid_to_cmd[pid]
        del pid_to_cmd[pid]
        del pid_to_time[pid]
        print(f'# [{len(pid_to_cmd)}] END({pid}:{retval} time={NiceTime(elapsed)}):  {cmd}')

def PrintTestCmds():
    with os.scandir('/usr/bin') as dirlist:
        for idx, entry in enumerate(dirlist):
            if entry.name.startswith('.') or not entry.is_file():
                continue
            print(f'ls -l /usr/bin/{entry.name} > tmp.multicmd.test.out.{idx}')

if __name__ == '__main__':
    import argparse
    prog = sys.argv[0]
    class CustomFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawTextHelpFormatter):
        pass
    parser = argparse.ArgumentParser(description = 'Run commands in file or stdin in parallel on specified number of cores',
                                     formatter_class = CustomFormatter,
                                     epilog = 'Examples:\n'
                                     + f'  (for n in 8 7 6 5 4 3 2 1; do echo "sleep $n"; done) | {prog} -n 4 # run 8 processes on 4 cores\n'
                                     + f'  {prog} -t | {prog} # run some 1800 jobs with output redirection using all available cores'
                                     )
    parser.add_argument('-n', '--ncpu',  type=int,  default=CountCores(),  nargs='?', help='max number of parallel jobs')
    parser.add_argument('-t', '--test',  action='store_true',                         help='print a bunch of commands for testing')
    parser.add_argument('fname', nargs='*', help='')
    args = parser.parse_args()

    if args.test:
        PrintTestCmds()
    else:
        if args.fname:
            with open(args.fname[0]) as infile:
                lines = [line.rstrip() for line in infile]
        else:
            lines = [line.rstrip() for line in sys.stdin]
        if args.ncpu == 1:
            RunByOne(lines)
        else:
            Run(lines, args.ncpu)
