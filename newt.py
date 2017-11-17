#!/usr/bin/env python3

# A Python chess engine

from pst import pst

import chess as c
import sys, math, time

# computer plays as Black by default

COMPC = c.BLACK
PLAYC = c.WHITE

DEPTH  = 3	# maximum search depth
QPLIES = 8	# additional maximum quiescence search plies
PSTAB  = .1	# influence of piece-square table on moves, 0 = none

b = c.Board()
PV = []		# array for primary variation

def getpos(b):
	"Get positional-play value for a board for both players"
	ppv = 0
	if not moves and b.is_checkmate():
		if b.turn == c.WHITE:
			ppv = -1000
		else:
			ppv =  1000
	pm = b.piece_map()
	for i in pm.keys():
		mm = pm[i].piece_type
		if mm == c.KING and (
		  len(b.pieces(c.PAWN, COMPC)) + len(b.pieces(c.PAWN, PLAYC)) ) <= 8:	# endgame is different
			mm = 8								#   for the King
		if pm[i].color == c.WHITE:
			j, k = i // 8, i % 8
			ppv += PSTAB * pst[mm][8 * (7 - j) + k] / 100
		else:
			ppv -= PSTAB * pst[mm][i]               / 100
	return ppv

def getval(b):
	"Get total piece value of board"
	return (
		len(b.pieces(c.PAWN, c.WHITE))          - len(b.pieces(c.PAWN, c.BLACK))
	+	3 * (len(b.pieces(c.KNIGHT, c.WHITE))   - len(b.pieces(c.KNIGHT, c.BLACK)))
	+	3 * (len(b.pieces(c.BISHOP, c.WHITE))   - len(b.pieces(c.BISHOP, c.BLACK)))
	+	5 * (len(b.pieces(c.ROOK, c.WHITE))     - len(b.pieces(c.ROOK, c.BLACK)))
	+	9 * (len(b.pieces(c.QUEEN, c.WHITE))    - len(b.pieces(c.QUEEN, c.BLACK)))
	)

def isdead(b, p):
	"Is the position dead? (quiescence) E.g., can the capturing piece be recaptured? Is there a check on this or the last move?"
	if p <= -QPLIES or not moves:	# when too many plies or checkmate
		return True
	if b.is_check():
		return False
	x = b.pop()
	if (b.is_capture(x) and len(b.attackers(not b.turn, x.to_square))) or b.is_check():
		b.push(x)
		return False
	else:
		b.push(x)
		return True

# https://chessprogramming.wikispaces.com/Alpha-Beta
def searchmax(b, ply, alpha, beta):
	"Search moves and evaluate positions for White"
	global moves

	# This way is quite a bit faster than a simple "list(b.legal_moves)",
	# because the LegalMoveGenerator's __len__ is not called, which would
	# generate the moves *twice*. Thanks, SnakeViz team!
	moves = [q for q in b.legal_moves]

	if ply <= 0 and isdead(b, ply):
		return getval(b) + getpos(b), [str(q) for q in b.move_stack]
	o = order(b, ply)
	if ply <= 0:
		if not o:
			return getval(b) + getpos(b), [str(q) for q in b.move_stack]
	v = PV
	for x in o:
		b.push(x)
		t, vv = searchmin(b, ply - 1, alpha, beta)
		b.pop()
		if t >= beta:
			return beta, vv
		if t > alpha:
			alpha = t
			v = vv
	return alpha, v

def searchmin(b, ply, alpha, beta):
	"Search moves and evaluate positions for Black"
	global moves

	moves = [q for q in b.legal_moves]

	if ply <= 0 and isdead(b, ply):
		return getval(b) + getpos(b), [str(q) for q in b.move_stack]
	o = order(b, ply)
	if ply <= 0:
		if not o:
			return getval(b) + getpos(b), [str(q) for q in b.move_stack]
	v = PV
	for x in o:
		b.push(x)
		t, vv = searchmax(b, ply - 1, alpha, beta)
		b.pop()
		if t <= alpha:
			return alpha, vv
		if t < beta:
			beta = t
			v = vv
	return beta, v

def order(b, ply):
	"Move ordering"
	if ply >= 0:		# try moves from PV before others
		am, bm = [], []
		for x in moves:
			if str(x) in PV:
				am.append(x)
			else:
				bm.append(x)
		return am + bm

	# quiescence search (ply < 0), sort captures by MVV/LVA value
	am, bm = [], []
	for x in moves:
		if b.is_capture(x):
			if b.piece_at(x.to_square):
				# MVV/LVA sorting (http://home.hccnet.nl/h.g.muller/mvv.html)
				am.append((x, 10 * b.piece_at(x.to_square).piece_type
							- b.piece_at(x.from_square).piece_type))
			else:	# to square is empty during en passant capture
				am.append((x, 10 - b.piece_at(x.from_square).piece_type))
	am.sort(key = lambda m: m[1])
	am.reverse()
	bm = [q[0] for q in am]
	return bm

def pm():
	if COMPC == c.WHITE:
		return 1
	else:
		return -1

def getmove(b, silent = False):
	"Get value and primary variation for board"
	global COMPC, PLAYC, MAXPLIES, PV

	if b.turn == c.WHITE:
		COMPC = c.WHITE
		PLAYC = c.BLACK
	else:
		COMPC = c.BLACK
		PLAYC = c.WHITE

	if not silent:
		print("FEN:", b.fen())

	for MAXPLIES in range(1, DEPTH + 1):
		if COMPC == c.WHITE:
			t, PV = searchmax(b, MAXPLIES, -1e6, 1e6)
		else:
			t, PV = searchmin(b, MAXPLIES, -1e6, 1e6)

		PV = PV[len(b.move_stack):]	# separate principal variation from moves already played
		print('# %u %.2f %s' % (MAXPLIES, t, str(PV)), flush = True)
		if t < -500 or t > 500:	# found a checkmate
			break
	return t, PV

if __name__ == '__main__':
	while True:	# game loop
		while True:
			print(b)
			print()
			move = input("Your move? ")
			if move == "quit":
				sys.exit(0)
			try:
				try:
					b.push_san(move)
				except ValueError:
					b.push_uci(move)
				print(b)
			except:
				print("Sorry? Try again. (Or type quit to quit.)")
			else:
				break

		if b.result() != '*':
			print("Game result:", b.result())
			break

		tt = time.time()
		t, ppp = getmove(b)

		print("My move: %u. %s" % (b.fullmove_number, ppp[0]))
		print("  ( calculation time spent: %u m %u s )" % ((time.time() - tt) // 60, (time.time() - tt) % 60))
		b.push(c.Move.from_uci(ppp[0]))

		if b.result() != '*':
			print("Game result:", b.result())
			break


