# treatPDF_sizing実行用シェルスクリプト
python treatPDF_sizing.py ../models/obj/bishop.obj << EOF
2.3
100 100 100
n
n
n
y
0.1
bishop_23_addPoint
EOF

python treatPDF_sizing.py ../models/obj/king.obj << EOF
2.3
100 100 100
n
n
n
y
0.1
king_23_addPoint
EOF

python treatPDF_sizing.py ../models/obj/knight.obj << EOF
2.3
100 100 100
n
n
n
y
0.1
knight_23_addPoint
EOF

python treatPDF_sizing.py ../models/obj/pawn.obj << EOF
2.3
100 100 100
n
n
n
y
0.1
pawn_23_addPoint
EOF

python treatPDF_sizing.py ../models/obj/qween_front.obj << EOF
2.3
100 100 100
n
n
n
y
0.1
qween_f_23_addPoint
EOF

python treatPDF_sizing.py ../models/obj/qween_back.obj << EOF
2.3
100 100 100
n
n
n
y
qween_b_23_addPoint
EOF

python treatPDF_sizing.py ../models/obj/rook.obj << EOF
2.3
100 100 100
n
n
n
y
0.1
rook_23_addPoint
EOF
