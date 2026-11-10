"""Known11-ply Greek-Gift rules fixture; no search/model/playing-strength claim."""
import sys
assert sys.stdin.readline().strip()=='fow'
side=sys.stdin.readline().split()[0]
moves=iter(['d2d4','c1d2','d4c5','e2e4','g1f3','e1f2'] if side=='w' else ['e7e6','c7c5','f8c5','d8b6','c5f2'])
print('ready',flush=True)
for line in sys.stdin:
 try:float(line.strip())
 except ValueError:continue
 print('move '+next(moves),flush=True)
