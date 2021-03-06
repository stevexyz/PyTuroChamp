#!/usr/bin/env python3

# XBoard/UCI interface to PyTuroChamp

# Start with:
# xboard -fcp "python3 xboard.py"

#    Optional debug flags:  -debug -nameOfDebugFile debug.txt -engineDebugOutput 2

from __future__ import print_function

import sys, datetime
import chess as c
import chess.pgn

abc = "abcdefgh"
nn  = "12345678"

is_uci = False

if len(sys.argv) < 2 or sys.argv[1] == 'ptc':
	import pyturochamp as p
	lf = "PyTuroChamp-log.txt"
	mf = "PyTuroChamp.pgn"
	nm = "PyTuroChamp"
elif sys.argv[1] == 'bare':
	import bare as p
	lf = "Bare-log.txt"
	mf = "Bare.pgn"
	nm = "Bare"
else:
	import newt as p
	lf = "Newt-log.txt"
	mf = "Newt.pgn"
	nm = "Newt"

try:
	log = open(lf, 'w')
except:
	log = ''
	print("# Could not create log file")
d = ''
r = ''

def move(r):
	rm = r[0]
	d.push_uci(rm)
	if is_uci:
		print("bestmove", rm)
	else:
		print("move", rm)
	if log:
		log.write("move %s\n" % rm)
		log.flush()
	pgn()

def pgn():
	game = chess.pgn.Game.from_board(d)
	now = datetime.datetime.now()
	game.headers["Date"] = now.strftime("%Y.%m.%d")
	if p.pm() > 0:
		game.headers["White"] = nm
		game.headers["Black"] = "User"
	else:
		game.headers["Black"] = nm
		game.headers["White"] = "User"
	try:
		with open(mf, 'w') as f:
			f.write(str(game) + '\n\n\n')
	except:
		print("# Could not write PGN file")

def newgame():
	global d

	d = c.Board()

def fromfen(fen):
	global d

	try:
		d = c.Board(fen)
	except:
		print("Bad FEN")
	print(d)

while True:
	l = ''
	try:
		if sys.version < '3':
			l = raw_input()
		else:
			l = input()
	except KeyboardInterrupt:	# XBoard sends Control-C characters, so these must be caught
		if not is_uci:
			pass		#   Otherwise Python would quit.
	if l:
		if log:
			log.write(l + '\n')
			log.flush()
		if l == 'xboard':
			print('feature myname="%s" setboard=1 done=1' % nm)
		elif l == 'quit':
			sys.exit(0)
		elif l == 'new':
			newgame()
		elif l == 'uci':
			is_uci = True
			print("uciok")
		elif l == 'ucinewgame':
			newgame()
		elif 'position startpos moves' in l:
			mm = l.split()[3:]
			newgame()
			for mo in mm:
				d.push_uci(mo)
		elif l == 'isready':
			newgame()
			print("id name", nm)
			print("readyok")
		elif 'setboard' in l:
			fen = l.split(' ', 1)[1]
			fromfen(fen)
		elif l[:2] == 'go' or l == 'force':
			if not d:
				newgame()
			t, r = p.getmove(d, silent = True)
			if r:
				move(r)
		elif l == '?':
			print("move", r)
			if log:
				log.write("move %s\n" % r)
				log.flush()
		else:
			if not d:
				newgame()
			if l[0] in abc and l[2] in abc and l[1] in nn and l[3] in nn:
				if len(l) == 6:
					l = l[:4] + 'q'	# "Knights" outputs malformed UCI pawn promotion moves
				d.push_uci(l)
				pgn()
				t, r = p.getmove(d, silent = True)
				if r:
					move(r)


