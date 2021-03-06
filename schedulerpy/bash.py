# Copyright (C) 2016 Henrique Pereira Coutada Miranda, Alejandro Molina-Sanchez
# All rights reserved.
#
# This file is part of yambopy
#
#
import subprocess
from schedulerpy import *

class Bash(Scheduler):
    """
    Class to submit jobs using BASH
    """
    _vardict = {"cores":"core",
                "nodes":"nodes"}
    def initialize(self):
        self.get_vardict()
        
    def __str__(self):
        return self.get_commands()

    def get_bash(self):
        return str(self)

    def get_script(self):
        return str(self)

    def add_mpirun_command(self, cmd):
        threads = 1
        if self.cores: threads*=self.cores
        mpirun = self.get_arg("mpirun")
        if mpirun is None: mpirun = "mpirun"
        self.add_command("%s -np %d %s"%(mpirun,threads,cmd))
        
    def run(self,dry=False):
        if dry:
            print str(self)
        else:
            p = subprocess.Popen(str(self),stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True,executable='/bin/bash')
            self.stdout, self.stderr = p.communicate()
            if self.stderr != "":
                raise ValueError("ERROR:\n%s"%self.stderr)
            print self.stdout
