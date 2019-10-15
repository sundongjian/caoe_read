# -*- coding: utf-8 -*-
import os
from multiprocessing import Process
import time
from signal import SIGKILL
from glob import glob
import sys
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# import pytest
import caoe
# import caoe


def is_process_alive(pid):
    try:
        # 0表示测试时否存在
        os.kill(pid, 0)
    except OSError as e:
        if e.errno == 3:  # process is dead
            return False
        elif e.errno == 1:  # no permission
            return True
        else:
            raise
    else:
        return True


def parent(path, pause=False, fork=True):
    caoe.install(fork=fork)
    # 将caoe进行注销，当父进程在外面被kill掉而不是正常结束进程，子进程不会被干掉。
    # 如果主进程正常退出/异常退出/ctrl-c，子进程也会同时被干掉
    # 将fork设置为True,当父进程被kill掉的时候，会同时干掉子进程，False时不会干掉子进程
    open(os.path.join(path, 'parent-%d' % os.getpid()), 'w').close()
    for i in range(3):
        p = Process(target=child, args=(path,))
        p.daemon = True
        p.start()
    p = Process(target=child_1, args=())
    p.daemon = True
    p.start()
    if pause:
        pid = os.getpid()
        print("parent:",pid)
        time.sleep(90)
    else:
        time.sleep(0.1)


def child(path):
    pid = os.getpid()
    open(os.path.join(path, 'child-%d' % pid), 'w').close()
    print("child process:", pid)
    for i in range(100):
        time.sleep(1)
        # print("child process:",pid)

def child_1():
    pid = os.getpid()
    print("child process 1:", pid)
    for i in range(5):
        time.sleep(1)

@pytest.mark.parametrize('fork', [False])
def test_all_child_processes_should_be_killed_if_parent_quit_normally(tmpdir, fork):
    tmpdir = str(tmpdir)
    p = Process(target=parent, args=(tmpdir,), kwargs={'fork': fork})
    p.start()
    p.join(10)
    assert not p.is_alive()
    cpids = [int(x.split('-')[1])
             for x in os.listdir(tmpdir) if x.startswith('child-')]
    assert len(cpids) == 3
    for i in range(caoe.PARENT_POLL_INTERVAL + 1):
        if not any(is_process_alive(pid) for pid in cpids):
            break
        time.sleep(1)
    else:
        assert False, "child processes still alive"
    # ensure the parent logic is executed only once
    assert len(glob(os.path.join(tmpdir, 'parent-*'))) == 1
#
#
# @pytest.mark.parametrize('fork', [True, False])
# def test_all_child_processes_should_be_killed_if_parent_is_killed(tmpdir, fork):
#     tmpdir = str(tmpdir)
#     p = Process(target=parent, args=(tmpdir,),
#                 kwargs={'pause': True, 'fork': fork})
#     p.start()
#
#     for i in range(100):
#         time.sleep(0.1)
#         if glob(os.path.join(tmpdir, 'child-*')):
#             break
#     else:
#         raise Exception("no child process spawned")
#
#     p.terminate()
#     p.join()
#     cpids = [int(x.split('-')[1])
#              for x in os.listdir(tmpdir) if x.startswith('child-')]
#     assert len(cpids) == 3
#
#     for i in range(100):
#         time.sleep(0.1)
#         if not any(is_process_alive(pid) for pid in cpids):
#             break
#     else:
#         assert False, "child processes are not killed"
#
#     # ensure the parent logic is executed only once
#     assert len(glob(os.path.join(tmpdir, 'parent-*'))) == 1


def test_all_child_processes_should_be_killed_if_parent_is_killed_by_SIGKILL_in_fork_mode(tmpdir):
    tmpdir = str(tmpdir)
    p = Process(target=parent, args=(tmpdir,), kwargs={'pause': True})
    p.start()
    time.sleep(1)  # wait for child processes spawned
    os.kill(p.pid, SIGKILL)
    p.join()
    time.sleep(5)  # wait for the parent status checking interval
    cpids = [int(x.split('-')[1])
             for x in os.listdir(tmpdir) if x.startswith('child-')]
    assert len(cpids) == 3
    assert all(not is_process_alive(pid) for pid in cpids)
    # ensure the parent logic is executed only once
    assert len(glob(os.path.join(tmpdir, 'parent-*'))) == 1


if __name__== "__main__":
    # print(is_process_alive(19756))
    parent("/home/sunjian/kaiyuan/caoe/CaoE/pidfile",True)

