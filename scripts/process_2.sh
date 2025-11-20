#盤面印刷用treatPDF_sizing.shのシェルスクリプト
python treatPDF_sizing.py ../models/obj/board_left_front.obj << EOF
3.9
100 100 100
n
board_lf
EOF

python treatPDF_sizing.py ../models/obj/board_left_back.obj << EOF
3.9
100 100 100
n
board_lb
EOF

python treatPDF_sizing.py ../models/obj/board_right_front.obj << EOF
3.9
100 100 100
n
board_rf
EOF

python treatPDF_sizing.py ../models/obj/board_right_back.obj << EOF
3.9
100 100 100
n
board_rb
EOF