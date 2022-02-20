#!/bin/bash
python3 venLoader.py & 
echo "Continue, please wait..."
sleep 30
python3 whenLambo.py -sx BLZ -lx 20 -bx 1 -sbx 2 -stx 500 & 
sleep 0.2
python3 whenLambo.py -sx GRT -lx 20 -bx 1 -sbx 2 -stx 500 & 
sleep 0.7
python3 whenLambo.py -sx RVN -lx 20 -bx 1 -sbx 2 -stx 500 & 
sleep 1.2
python3 whenLambo.py -sx QTUM -lx 20 -bx 1 -sbx 2 -stx 500 & 
sleep 1.7
python3 whenLambo.py -sx REEF -lx 20 -bx 1 -sbx 2 -stx 500 & 
sleep 2.2
python3 whenLambo.py -sx RUNE -lx 20 -bx 1 -sbx 2 -stx 500 & 
sleep 2.7
python3 whenLambo.py -sx SAND -lx 20 -bx 1 -sbx 2 -stx 500 & 
sleep 3.2
python3 whenLambo.py -sx VET -lx 20 -bx 1 -sbx 2 -stx 500