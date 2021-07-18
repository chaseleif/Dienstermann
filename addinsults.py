#! /usr/bin/env python

# https://docs.limnoria.net/index.html
# https://hoxu.github.io/supybook/devel/#_administrative_tasks
# https://github.com/ProgVal/Limnoria


import re

def getnumstr(numba):
  placenum=100000
  string=''
  while int(placenum)>0:
    string+=str(int(numba/placenum))
    numba=numba%placenum
    placenum/=10
  return string

addinsults = []
with open('insults','r') as infile:
  addinsults = infile.read().strip().split('\n')

for i, insult in enumerate(addinsults):
  if '\'' in insult:
    addinsults[i] = re.sub('\'','\\\'',insult)

contents = ''
with open('data/#txstcs/Dunno.flat.db','r') as infile:
  contents = infile.read().split('\n')

startnum=int(contents[0])
stopnum=startnum+len(addinsults)
string=getnumstr(stopnum)+'\n'
for line in contents[1:]:
  string+=line+'\n'
string = string[:-1]
pieces = contents[-2].split(',')
timepart = pieces[0].split(':')[1]
for i, line in enumerate(addinsults):
  string+=getnumstr(startnum)+':'+timepart+',1,\''+line+'\'\n'
  startnum+=1

with open('data/#txstcs/Dunno.flat.db','w') as outfile:
  outfile.write(string)
