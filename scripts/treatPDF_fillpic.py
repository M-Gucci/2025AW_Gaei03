import matplotlib.pyplot as plt
import sys
import os
import matplotlib.image as mpimg
from matplotlib.patches import Polygon, Circle

def parse_obj(filename):
    """
    .objファイルを解析して、頂点、線、面の情報を抽出し、孤立点も検出する。
    """
    vertices_raw = []
    lines = []
    faces = []
    total_vertices_count = 0
    referenced_indices_set = set()

    try:
        with open(filename, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if not parts:
                    continue
                
                if parts[0] == 'v':
                    vertices_raw.append([float(p) for p in parts[1:4]])
                    total_vertices_count += 1
                elif parts[0] == 'l':
                    line_indices = [int(p.split('/')[0]) - 1 for p in parts[1:]]
                    lines.append(line_indices)
                    for idx in line_indices:
                        referenced_indices_set.add(idx + 1)
                elif parts[0] == 'f':
                    face_indices = [int(p.split('/')[0]) - 1 for p in parts[1:]]
                    faces.append(face_indices)
                    for idx in face_indices:
                        referenced_indices_set.add(idx + 1)

    except FileNotFoundError:
        print(f"エラー: ファイルが見つかりません {filename}")
        sys.exit(1)
    except Exception as e:
        print(f"ファイルの解析中にエラーが発生しました: {e}")
        sys.exit(1)

    unreferenced_vertices_coords = []
    if total_vertices_count > 0:
        defined_indices_set = set(range(1, total_vertices_count + 1))
        unreferenced_1based_indices = defined_indices_set - referenced_indices_set
        
        for idx_1based in sorted(list(unreferenced_1based_indices)):
            idx_0based = idx_1based - 1
            if 0 <= idx_0based < len(vertices_raw):
                unreferenced_vertices_coords.append((vertices_raw[idx_0based][0], vertices_raw[idx_0based][1]))

    min_x_model, max_x_model = float('inf'), float('-inf')
    min_y_model, max_y_model = float('inf'), float('-inf')

    if vertices_raw:
        for v_coords in vertices_raw:
            x, y = v_coords[0], v_coords[1]
            min_x_model = min(min_x_model, x)
            max_x_model = max(max_x_model, x)
            min_y_model = min(min_y_model, y)
            max_y_model = max(max_y_model, y)
    else:
        min_x_model, max_x_model = -1, 1
        min_y_model, max_y_model = -1, 1

    return vertices_raw, lines, faces, unreferenced_vertices_coords, min_x_model, max_x_model, min_y_model, max_y_model

def plot_obj(vertices, lines, faces, unreferenced_vertices_coords, min_x_model, max_x_model, min_y_model, max_y_model):
    """
    .objファイルのデータを2Dでプロットし、A3サイズのPDFとして保存する。
    """
    if not vertices:
        print("プロットする頂点がありません。")
        return

    # --- ユーザー入力セクション ---

    # 処理モードの選択
    print("\n実行したい処理を選択してください:")
    print("1: 面全体を画像で埋める")
    print("2: 指定した位置にマーク（画像）を配置する")
    while True:
        mode = input("選択 (1 or 2): ").strip()
        if mode in ['1', '2']:
            break
        else:
            print("無効な選択です。1または2を入力してください。")

    # スケールの入力
    print("\n希望する出力スケールを入力してください（例: 1.0単位 = 1.0cm）。")
    while True:
        try:
            user_scale_cm_per_unit_str = input("スケールを入力 (cm/単位, 例: 1.0): ")
            user_scale_cm_per_unit = float(user_scale_cm_per_unit_str)
            if user_scale_cm_per_unit <= 0:
                print("スケールは正の数でなければなりません。")
                continue
            break
        except ValueError:
            print("無効な入力です。数値を入力してください。")

    # モードに応じた入力
    image_path = None
    mark_img = None
    center_x, center_y, mark_width = 0, 0, 0

    if mode == '1':
        # 貼り付ける画像のパスを入力
        print("\n面に貼り付ける画像ファイルのパスを入力してください。")
        while True:
            image_path = input("画像ファイルのパス: ").strip()
            if os.path.exists(image_path) and os.path.isfile(image_path):
                try:
                    img = mpimg.imread(image_path)
                    break
                except Exception as e:
                    print(f"画像を読み込めませんでした: {e}")
            else:
                print("無効なパスです。ファイルが存在しません。")
    
    elif mode == '2':
        # マーク配置のための入力
        print("\nマークとして使用する画像ファイルのパスを入力してください。")
        while True:
            mark_image_path = input("画像ファイルのパス: ").strip()
            if os.path.exists(mark_image_path) and os.path.isfile(mark_image_path):
                try:
                    mark_img = mpimg.imread(mark_image_path)
                    break
                except Exception as e:
                    print(f"画像を読み込めませんでした: {e}")
            else:
                print("無効なパスです。ファイルが存在しません。")

        print("\nマークを配置する中心座標 (X, Y) を入力してください。")
        while True:
            try:
                center_x_str = input("中心のX座標: ")
                center_x = float(center_x_str)
                break
            except ValueError:
                print("無効な入力です。数値を入力してください。")
        while True:
            try:
                center_y_str = input("中心のY座標: ")
                center_y = float(center_y_str)
                break
            except ValueError:
                print("無効な入力です。数値を入力してください。")

        print("\nマークの幅をモデル単位で入力してください。")
        while True:
            try:
                mark_width_str = input("マークの幅: ")
                mark_width = float(mark_width_str)
                if mark_width <= 0:
                    print("幅は正の数でなければなりません。")
                    continue
                break
            except ValueError:
                print("無効な入力です。数値を入力してください。")

    # --- 用紙と描画領域の準備 ---
    paper_width_cm = 29.7
    paper_height_cm = 42.0
    fig = plt.figure(figsize=(paper_width_cm / 2.54, paper_height_cm / 2.54))
    ax = fig.add_subplot(111)

    # --- スケール計算 ---
    data_width = max_x_model - min_x_model
    data_height = max_y_model - min_y_model
    required_physical_width_cm = data_width * user_scale_cm_per_unit
    required_physical_height_cm = data_height * user_scale_cm_per_unit
    effective_scale_cm_per_unit = user_scale_cm_per_unit

    if required_physical_width_cm > paper_width_cm or required_physical_height_cm > paper_height_cm:
        print(f"\n警告: スケール {user_scale_cm_per_unit} cm/単位 ({required_physical_width_cm:.2f}cm x {required_physical_height_cm:.2f}cm) は、A3用紙 ({paper_width_cm:.2f}cm x {paper_height_cm:.2f}cm) を超えます。")
        scale_factor_width = paper_width_cm / required_physical_width_cm
        scale_factor_height = paper_height_cm / required_physical_height_cm
        adjustment_factor = min(scale_factor_width, scale_factor_height)
        effective_scale_cm_per_unit = user_scale_cm_per_unit * adjustment_factor
        print(f"A3に収まるように、スケールを {effective_scale_cm_per_unit:.4f} cm/単位 に調整します。")
    
    # --- 描画範囲の設定 ---
    plot_data_width = paper_width_cm / effective_scale_cm_per_unit
    plot_data_height = paper_height_cm / effective_scale_cm_per_unit
    x_center_model = (min_x_model + max_x_model) / 2
    y_center_model = (min_y_model + max_y_model) / 2
    plot_min_x = x_center_model - plot_data_width / 2
    plot_max_x = x_center_model + plot_data_width / 2
    plot_min_y = y_center_model - plot_data_height / 2
    plot_max_y = y_center_model + plot_data_height / 2
    ax.set_xlim(plot_min_x, plot_max_x)
    ax.set_ylim(plot_min_y, plot_max_y)

    # --- 描画処理 ---
    # モード1: 面 (f) に画像を貼り付け
    if mode == '1' and faces and image_path:
        img = mpimg.imread(image_path)
        for face_indices in faces:
            face_verts = [vertices[idx][:2] for idx in face_indices]
            clip_poly = Polygon(face_verts, closed=True, facecolor='none', edgecolor='black')
            ax.add_patch(clip_poly)
            im_face = ax.imshow(img, extent=(min_x_model, max_x_model, min_y_model, max_y_model),
                                aspect='auto', origin='upper', interpolation='nearest')
            im_face.set_clip_path(clip_poly)

    # 線 (l) をプロット
    if lines:
        for line_indices in lines:
            for i in range(len(line_indices) - 1):
                v1_idx, v2_idx = line_indices[i], line_indices[i+1]
                if v1_idx < len(vertices) and v2_idx < len(vertices):
                    v1, v2 = vertices[v1_idx], vertices[v2_idx]
                    ax.plot([v1[0], v2[0]], [v1[1], v2[1]], 'b-')

    # 面 (f) の境界線をプロット
    if faces:
        for face_indices in faces:
            closed_face_indices = face_indices + [face_indices[0]]
            for i in range(len(closed_face_indices) - 1):
                v1_idx, v2_idx = closed_face_indices[i], closed_face_indices[i+1]
                if v1_idx < len(vertices) and v2_idx < len(vertices):
                    v1, v2 = vertices[v1_idx], vertices[v2_idx]
                    ax.plot([v1[0], v2[0]], [v1[1], v2[1]], 'r-')

    # 孤立点の周りに円を描画
    if unreferenced_vertices_coords:
        print("\n孤立点が検出されました。描画する円の直径を入力してください。")
        while True:
            try:
                diameter_str = input("円の直径を入力 (例: 0.1): ")
                diameter = float(diameter_str)
                if diameter <= 0:
                    print("直径は正の数でなければなりません。")
                    continue
                break
            except ValueError:
                print("無効な入力です。数値を入力してください。")

        for ux, uy in unreferenced_vertices_coords:
            circle = Circle((ux, uy), radius=diameter/2, color='black')
            ax.add_patch(circle)
        print(f"直径 {diameter} の円を孤立点の周りに描画しました。")

    # モード2: マークを配置
    if mode == '2' and mark_img is not None:
        img_height, img_width, _ = mark_img.shape
        aspect_ratio = img_height / img_width
        mark_height = mark_width * aspect_ratio

        x_min = center_x - mark_width / 2
        x_max = center_x + mark_width / 2
        y_min = center_y - mark_height / 2
        y_max = center_y + mark_height / 2

        ax.imshow(mark_img, extent=(x_min, x_max, y_min, y_max), aspect='auto', origin='upper', interpolation='nearest', zorder=10)
        print(f"座標 ({center_x}, {center_y}) に幅 {mark_width} のマークを配置しました。")


    # --- 出力設定 ---
    ax.axis('off')
    ax.set_aspect('equal', adjustable='box')

    print("\nPDFの出力ファイル名を入力してください（例: my_plot.pdf）：\n")
    while True:
        pdf_filename = input("ファイル名: ").strip()
        if not pdf_filename:
            print("ファイル名は空にできません。")
            continue
        if not pdf_filename.lower().endswith('.pdf'):
            pdf_filename += '.pdf'
        break
    
    plt.savefig(pdf_filename)
    print(f"グラフを {pdf_filename} に保存しました。有効スケール: 1単位 = {effective_scale_cm_per_unit:.4f} cm")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("使用法: python treatPDF_fillpic.py <.objファイルへのパス>")
        sys.exit(1)

    obj_file = sys.argv[1]
    verts, lns, fcs, unref_verts_coords, min_x, max_x, min_y, max_y = parse_obj(obj_file)
    plot_obj(verts, lns, fcs, unref_verts_coords, min_x, max_x, min_y, max_y)