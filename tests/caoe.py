# -*- coding: utf-8 -*-
import errno
import os
import sys
import time
from signal import signal, SIGINT, SIGQUIT, SIGTERM, SIGCHLD, SIGHUP, pause, SIG_DFL

__all__ = ['install']

PARENT_POLL_INTERVAL = 5  # only used if no prctl available


def install(fork=True, sig=SIGTERM):
    def _reg(gid):
        handler = make_quit_signal_handler(gid, sig)
        signal(SIGINT, handler)
        signal(SIGQUIT, handler)
        signal(SIGTERM, handler)
        signal(SIGCHLD, make_child_die_signal_handler(gid, sig))

    if not fork:
        _reg(os.getpid())
        return

    pid = os.fork()
    if pid == 0:
        # child process
        # 切断和父进程的信号联系
        # 逻辑：当父进程被kill掉的时候，这个子进程因为任务已经完成了，所以也会被kill掉，这个子进程的子进程是一个无限循环，所以
        # 不会被kill掉，所以子进程的子进程开始自检，检查到自己的父进程被kill掉之后就杀掉父父进程的进程组，然后自杀
        os.setpgrp()
        pid = os.fork()
        if pid != 0:
            # still in child process
            exit_when_parent_or_child_dies(sig)
            # grand child process continues...
    else:
        # parent process
        gid = pid
        _reg(gid)
        # 暂停进程，把当前进程置成就绪态，让出CPU，直到收到任意一个信号后终止，并且当处理完该信号之后，直接执行pause()函数下面的语句
        # 上面是官网，但是好像并不是这回事
        # 确实是这么回事，在pause之前和之后，进程号都变了。。。。。
        print("parent process 0:", pid)
        while True:
            pause()


def make_quit_signal_handler(gid, sig=SIGTERM):
    def handler(signum, frame):
        # print('********')
        # 默认信号处理
        signal(SIGTERM, SIG_DFL)
        try:
            # killpg(0,SIGKILL) 杀掉所有的父进程和其子进程
            # print("killpg",gid,sig)
            os.killpg(gid, sig)
        except os.error as ex:
            if ex.errno != errno.ESRCH:
                raise
    return handler


def make_child_die_signal_handler(gid, sig=SIGTERM):
    def handler(signum, frame):
        try:
            pid, status = os.wait()
        except OSError:
            # sometimes there is no child processes already
            status = 0
        try:
            # sig=9
            signal(SIGTERM, SIG_DFL)
            os.killpg(gid, sig)
        finally:
            sys.exit((status & 0xff00) >> 8)
    return handler


def exit_when_parent_or_child_dies(sig):
    # 当前进程组的ID
    gid = os.getpgrp()
    signal(SIGCHLD, make_child_die_signal_handler(gid))
    # print("gid_c:",gid)
    try:
        import prctl
        signal(SIGHUP, make_quit_signal_handler(gid))
        # give me SIGHUP if my parent dies
        # 如果父进程挂掉了，给自己SIGHUP信号？
        prctl.set_pdeathsig(SIGHUP)
        while True:
            pause()

    except ImportError:
        # fallback to polling status of parent
        while True:
            # print("os.getppid()", os.getppid())
            # print("os.getpid",os.getpid())
            if os.getppid() == 1:
                # parent died, suicide
                signal(SIGTERM, SIG_DFL)
                os.killpg(gid, sig)
                sys.exit()
            time.sleep(20)
