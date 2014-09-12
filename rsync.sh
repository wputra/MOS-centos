#!/bin/sh

for i in 1 2 3 4 5 6 7 8 9
do
rsync -avz node-$i:/etc node-$i
#rsync -avz --max-size=100M node-$i:/root node-$i
rsync -avz node-$i:/usr/lib/python2.6/site-packages node-$i
done
