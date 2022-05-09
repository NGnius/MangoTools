import asyncio
import os

import logging

logging.basicConfig(
    filename = "/home/deck/.mangotools.log",
    format = '%(asctime)s %(levelname)s %(message)s',
    filemode = 'w',
    force = True)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

SLOW_LOOP_DIVISOR = 4
STANDARD_LOOP_SLEEP = 1 # seconds

class Plugin:
    mango_app_pid = None
    mangohud_config = None
    config = None
    
    # A normal method. It can be called from JavaScript using call_plugin_function("method_1", argument1, argument2)
    async def method_1(self, *args):
        pass

    # A normal method. It can be called from JavaScript using call_plugin_function("method_2", argument1, argument2)
    async def method_2(self, *args):
        pass

    # Asyncio-compatible long-running code, executed in a task when the plugin is loaded
    async def _main(self):
        logging.debug(f"getuid() -> {os.getuid()}, getenv(USER) -> {os.getenv('USER')}")
        counter = 0
        os.environ["USER"] = "deck"
        while True:
            if counter == 0:
                logging.debug("slow loop executing")
                # slow loop operations
                self.mango_app_pid = find_mangoapp_pid()
                logging.debug(f"mangoapp PID: {self.mango_app_pid}")
                if self.mango_app_pid is not None:
                    self.mangohud_config = find_mangoapp_config(self.mango_app_pid)
                    logging.debug(f"mangoapp config: {self.mangohud_config}")
                if self.mangohud_config is not None:
                    if self.config is None:
                        self.config = MangoConfig(self.mangohud_config)
                    else:
                        self.config.path = self.mangohud_config
            logging.debug("regular loop executing")
            # regular loop operations
            counter = (counter + 1) % SLOW_LOOP_DIVISOR
            logging.debug(f"getuid() -> {os.getuid()}, getenv(USER) -> {os.getenv('USER')}")
            if self.config is not None:
                self.config.write(force=True)
            await asyncio.sleep(STANDARD_LOOP_SLEEP)

def find_mangoapp_pid() -> int:
    for subdir in os.listdir("/proc"):
        if os.path.isdir("/proc/" + subdir):
            try:
                pid = int(subdir)
                cmdline = read_unix_file(proc_cmdline_path(pid))
                #logging.debug(f"checking subdir {subdir} cmdline: {cmdline}")
                if cmdline.startswith("mangoapp"):
                    return pid
            except ValueError:
                continue
    return None

def find_mangoapp_config(pid: int) -> str:
    environ = read_unix_file(proc_environ_path(pid))
    logging.debug(environ)
    for var in environ.split("\0"):
        if var.startswith("MANGOHUD_CONFIGFILE"):
            start_of_filepath = var.find("=") + 1
            logging.debug(var[start_of_filepath:])
            return var[start_of_filepath:].strip()
    return None

def proc_cmdline_path(pid: int) -> str:
    return f"/proc/{pid}/cmdline"

def proc_environ_path(pid: int) -> str:
    return f"/proc/{pid}/environ"

def read_unix_file(path: str) -> str:
    with open(path, "r") as f:
        return f.read().strip()

def write_unix_file(path: str, value):
    with open(path, "w") as f:
        f.write(str(value))


class MangoConfig:
    def __init__(self, filepath: str):
        self.path = filepath
        self.dirty = False
        self.read()
    
    def read(self):
        self.conf = list()
        with open(self.path, "r") as f:
            for line in f.readlines():
                equals_char = line.find("=")
                if equals_char != -1:
                    self.conf.append((line[:equals_char].strip(), line[equals_char+1:].strip()))
                else:
                    self.conf.append((line.strip(), None))
    
    def write(self, force=False):
        if not self.dirty and not force:
            return
        with open(self.path, "w") as f:
            for setting in self.conf:
                if setting[1] is None:
                    f.write(setting[0])
                    f.write("\n")
                else:
                    f.write(setting[0])
                    f.write("=")
                    f.write(setting[1])
                    f.write("\n")
        self.dirty = false
    
    def set(self, key, value=None):
        self.dirty = True
        for i in range(len(self.conf)):
            if self.conf[i][0] == key:
                self.conf[i] = (key, value)
                return
        self.conf.append((key, value))
        
                
    
