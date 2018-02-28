#!/usr/bin/env python

import matplotlib.pyplot as plt
import sys

FILENAME="/home/litvinenko/data/t.tme"

if len(sys.argv) == 2:
    fname = sys.argv[1]
elif len(sys.argv) < 2:
    fname = FILENAME
else:
    exit(1)
   
with open(fname) as fi:
    v_list = fi.readlines()

# x_list = [i, float(v.rsplit()) for i, v in enumerate(v_list, start=1)]

y_list = [float(v.rsplit()[0]) for v in v_list]

plt.plot(y_list)

plt.show()
