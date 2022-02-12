def read_file(filename):
    with open(filename, 'r') as f:
        return f.read()


def _run(command, timeout_s=False, shell=False):
    ### run a process, capture the output and wait for it to finish. if timeout is specified then Kill the subprocess and its childrens when the timeout is reached (if parent did not detach)
    ## usage: _run(arg1, arg2, arg3)
        # arg1: command+args. always pass a string, the function will split it when needed
        # arg2: (optional) timeout in seconds before force killing  
        # arg3: (optional) shell usage. default shell=False
    ## return: a list containing: exit code, output, and if timeout was reached or not
    
    # - tested on python 2 and 3 in windows xp, 7, cygwin and linux. 
    # - preexec_fn=os.setsid (py2) is equivalent to start_new_session (py3) (works in linux only), in windows and cygwin we use TASKKILL
    # - we use stderr=subprocess.STDOUT to merge stderr and stdout
    import sys, subprocess, os, signal, shlex, time
    
    def _runPY3(command, timeout_s=None, shell=False):
        # py3.3+ coz : timeout was added to communicate() in py3.3.
        new_session=False
        if sys.platform.startswith('linux'): new_session=True
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=new_session, shell=shell)
        
        try:
            out = p.communicate(timeout=timeout_s)[0].decode('utf-8')
            is_timeout_reached = False
        except subprocess.TimeoutExpired:
            print('Timeout reached: Killing the whole process group...')
            killAll(p.pid)
            out = p.communicate()[0].decode('utf-8')
            is_timeout_reached = True
        return p.returncode, out, is_timeout_reached
    
    def _runPY2(command, timeout_s=0, shell=False):
        preexec=None
        if sys.platform.startswith('linux'): preexec=os.setsid
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, preexec_fn=preexec, shell=shell)
        
        start_time = time.time()
        is_timeout_reached = False
        while timeout_s and p.poll() == None:
            if time.time()-start_time >= timeout_s:
                print('Timeout reached: Killing the whole process group...')
                killAll(p.pid)
                is_timeout_reached = True
                break
            time.sleep(1)
        out = p.communicate()[0].decode('utf-8')
        return p.returncode, out, is_timeout_reached
    
    def killAll(ParentPid):
        if sys.platform.startswith('linux'):
            os.killpg(os.getpgid(ParentPid), signal.SIGTERM)
        elif sys.platform.startswith('cygwin'):
            # subprocess.Popen(shlex.split('bash -c "TASKKILL /F /PID $(</proc/{pid}/winpid) /T"'.format(pid=ParentPid)))
            winpid=int(open("/proc/{pid}/winpid".format(pid=ParentPid)).read())
            subprocess.Popen(['TASKKILL', '/F', '/PID', str(winpid), '/T'])
        elif sys.platform.startswith('win32'):
            subprocess.Popen(['TASKKILL', '/F', '/PID', str(ParentPid), '/T'])
    
    # - in windows we never need to split the command, but in cygwin and linux we need to split if shell=False (default), shlex will split the command for us
    if shell==False and (sys.platform.startswith('cygwin') or sys.platform.startswith('linux')):
        command=shlex.split(command)
    
    if sys.version_info >= (3, 3): # py3.3+
        if timeout_s==False:
            returnCode, output, is_timeout_reached = _runPY3(command, timeout_s=None, shell=shell)
        else:
            returnCode, output, is_timeout_reached = _runPY3(command, timeout_s=timeout_s, shell=shell)
    else:  # py2 up to 3.2
        if timeout_s==False:
            returnCode, output, is_timeout_reached = _runPY2(command, timeout_s=0, shell=shell)
        else:
            returnCode, output, is_timeout_reached = _runPY2(command, timeout_s=timeout_s, shell=shell)
    
    return returnCode, output, is_timeout_reached

