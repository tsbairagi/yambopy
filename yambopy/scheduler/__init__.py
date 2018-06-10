# Copyright (C) 2016 Henrique Pereira Coutada Miranda
# All rights reserved.
#
# This file is part of yambopy
#
#
"""
Schedulerpy is a simple set of python modules to run 
commands on different environments (clusters, local computers, etc..)

 **Currently available schedulers are:**

 * bash: Execute the job in the bash
 * oar : Use the OAR scheduler
 * pbs : Use the PBS scheduler

"""
from .scheduler import *
from .oar import *
from .pbs import *
from .bash import *