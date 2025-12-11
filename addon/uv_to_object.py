# Blenderアドオンのメタデータ
# アドオンの名前、作者、バージョン、Blenderの互換性、説明などを定義します。
bl_info = {
    "name": "UV to Object",
    "author": "Your Name",
    "version": (1, 0),
    "blender": (2, 80, 0),  # このアドオンが動作するBlenderの最低バージョン
    "location": "View3D > Sidebar > UV to Object", # UIでの表示場所
    "description": "Creates a new mesh object from the active object's UV map.", # アドオンの説明
    "warning": "", # 警告メッセージ（任意）
    "doc_url": "", # ドキュメントURL（任意）
    "category": "Object", # アドオンのカテゴリ
}

import bpy # BlenderのPython APIをインポート

# オペレータークラスの定義
# ボタンが押されたときに実行される処理を定義します。
class OBJECT_OT_uv_to_object(bpy.types.Operator):
    """Creates a new mesh object from the active object's UV map""" # マウスオーバーで表示される説明
    bl_idname = "object.uv_to_object"  # オペレーターの一意なID (小文字とアンダースコアのみ)
    bl_label = "Create from UVs"  # UIに表示されるボタンのテキスト
    bl_options = {'REGISTER', 'UNDO'} # オペレーターのオプション: 登録可能、アンドゥ可能

    # オペレーターが実行されたときに呼び出されるメソッド
    def execute(self, context):
        # 現在アクティブなオブジェクトが存在し、かつ編集モードである場合、オブジェクトモードに切り替える
        # これにより、編集モードでの実行時に発生する可能性のあるエラーを防ぎ、安定したデータにアクセスします。
        if context.active_object and context.active_object.mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')

        source_obj = context.active_object # アクティブなオブジェクトを取得

        # 選択されたオブジェクトがメッシュではない、または何も選択されていない場合のバリデーション
        if source_obj is None or source_obj.type != 'MESH':
            self.report({'ERROR'}, "Please select a mesh object first.") # エラーメッセージを報告
            return {'CANCELLED'} # 処理を中断

        source_mesh = source_obj.data # オブジェクトのメッシュデータ（ジオメトリ情報）を取得

        # アクティブなUVレイヤーの存在を確認
        uv_layer = source_mesh.uv_layers.active
        if not uv_layer:
            self.report({'ERROR'}, "The selected object has no active UV map.")
            return {'CANCELLED'}

        # UVレイヤーにデータが存在するかを確認
        # UVレイヤーは存在するが、データが空の場合（例: UV展開されていないメッシュ）のエラーを防ぎます。
        if not uv_layer.data:
            self.report({'ERROR'}, "Active UV map has no data (is it empty?).")
            return {'CANCELLED'}
        
        uv_data = uv_layer.data # UVレイヤーのデータ（各ループのUV座標）を取得

        # 新しいメッシュを構築するためのリストを初期化
        new_verts = [] # 新しいメッシュの頂点座標リスト (x, y, z)
        new_faces = [] # 新しいメッシュの面リスト (頂点インデックスのリスト)
        
        # UV座標と新しい頂点インデックスのマッピングを保持する辞書
        # 同じUV座標を持つ点は、新しいメッシュでは同じ頂点として扱われるようにするため。
        uv_to_vert_map = {} 
        vert_index_counter = 0 # 新しい頂点に割り当てるインデックスのカウンター

        # 元のメッシュのすべての面（ポリゴン）をループ処理
        for poly in source_mesh.polygons:
            face_vert_indices = [] # 現在処理中の新しい面の頂点インデックスを一時的に保持するリスト
            
            # 面を構成する各頂点（ループ）をループ処理
            # Blenderのメッシュは、面を構成する頂点ごとにUV座標を持つことができます。
            for loop_index in poly.loop_indices:
                uv = uv_data[loop_index].uv # 現在のループのUV座標 (Vector型)
                # 浮動小数点数の比較誤差を避けるため、UV座標を丸めてタプルに変換
                uv_tuple = (round(uv.x, 6), round(uv.y, 6)) 

                # このUV座標がまだ新しい頂点として登録されていない場合
                if uv_tuple not in uv_to_vert_map:
                    # 新しい頂点としてリストに追加 (UVのX, Yを新しい頂点のX, Y座標とし、Zは0)
                    new_verts.append((uv.x, uv.y, 0.0))
                    # 辞書に「UV座標：新しい頂点番号」のマッピングを記録
                    uv_to_vert_map[uv_tuple] = vert_index_counter
                    # 現在の面の頂点リストに、新しい頂点番号を追加
                    face_vert_indices.append(vert_index_counter)
                    vert_index_counter += 1 # 次の新しい頂点のためにカウンターをインクリメント
                # このUV座標がすでに出現済みの場合
                else:
                    # 辞書から既存の頂点番号を取得し、現在の面の頂点リストに追加
                    existing_vert_index = uv_to_vert_map[uv_tuple]
                    face_vert_indices.append(existing_vert_index)
            
            # 現在の面を構成する頂点インデックスのリストを、全体の面リストに追加
            new_faces.append(face_vert_indices)

        # --- 新しいメッシュとオブジェクトをBlenderシーンに生成 ---
        
        # 1. 新しいメッシュデータブロックを作成
        # メッシュデータブロックは、ジオメトリ（頂点、辺、面）自体を保持します。
        mesh_name = f"{source_obj.name}_UV_Mesh" # 新しいメッシュの名前を生成
        new_mesh = bpy.data.meshes.new(name=mesh_name) # 新しい空のメッシュデータブロックを作成
        
        # 2. 作成した頂点と面のリストからメッシュを構築
        # from_pydata(vertices, edges, faces) - 辺は空リストで自動生成させます。
        new_mesh.from_pydata(new_verts, [], new_faces)
        
        # 3. メッシュデータを更新し、変更を適用
        new_mesh.update()

        # 4. 新しいオブジェクトデータブロックを作成し、上記で作成したメッシュデータを割り当てる
        # オブジェクトデータブロックは、シーン内の位置、回転、スケールなどの変換情報を保持します。
        obj_name = f"{source_obj.name}_UV_Object" # 新しいオブジェクトの名前を生成
        new_obj = bpy.data.objects.new(name=obj_name, object_data=new_mesh) # 新しいオブジェクトを作成
        
        # 5. 新しいオブジェクトを現在のシーンのコレクションにリンク（シーンに表示させる）
        context.collection.objects.link(new_obj)
        
        # 6. 生成された新しいオブジェクトをアクティブにし、選択状態にする（ユーザーの利便性のため）
        context.view_layer.objects.active = new_obj
        new_obj.select_set(True)

        self.report({'INFO'}, f"Created new object: {new_obj.name}") # 成功メッセージを報告
        return {'FINISHED'} # オペレーターの処理が完了したことをBlenderに通知


# UIパネルクラスの定義
# 3Dビューのサイドバーに表示されるパネルを定義します。
class VIEW3D_PT_uv_to_object(bpy.types.Panel):
    bl_label = "UV to Object" # パネルのヘッダーに表示されるタイトル
    bl_idname = "VIEW3D_PT_uv_to_object" # パネルの一意なID
    bl_space_type = 'VIEW_3D' # このパネルを表示するエディタの種類 (例: 3Dビューポート)
    bl_region_type = 'UI' # エディタ内のどの領域に表示するか (UI = サイドバー)
    bl_category = 'UV to Object' # サイドバーに表示されるタブの名前

    # パネルのUI要素を描画するメソッド
    def draw(self, context):
        layout = self.layout # UI要素を配置するためのレイアウトオブジェクト
        # 上記で定義したオペレーターをボタンとしてレイアウトに追加
        layout.operator(OBJECT_OT_uv_to_object.bl_idname)


# 登録するクラスのタプル
# register/unregister関数でループ処理するために、すべてのクラスをここにリストします。
classes = (
    OBJECT_OT_uv_to_object,
    VIEW3D_PT_uv_to_object,
)

# アドオンが有効化されたときに呼び出される関数
def register():
    # 定義したすべてのクラスをBlenderに登録
    for cls in classes:
        bpy.utils.register_class(cls)
    print("UV to Object Addon has been enabled.")

# アドオンが無効化されたときに呼び出される関数
def unregister():
    # 定義したすべてのクラスをBlenderから登録解除
    # 登録時と逆の順序で解除するのが安全です。
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    print("UV to Object Addon has been disabled.")

# このスクリプトがBlenderのテキストエディタから直接実行された場合に、register関数を呼び出す
if __name__ == "__main__":
    register()



class VIEW3D_PT_uv_to_object(bpy.types.Panel):
    bl_label = "UV to Object"
    bl_idname = "VIEW3D_PT_uv_to_object"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'UV to Object'

    def draw(self, context):
        layout = self.layout
        layout.operator(OBJECT_OT_uv_to_object.bl_idname)


classes = (
    OBJECT_OT_uv_to_object,
    VIEW3D_PT_uv_to_object,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()