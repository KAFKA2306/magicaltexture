# パステルカラーにグラデーション効果を追加
print("🎨 グラデーション効果付きパステルカラー作成開始!")
print("=" * 50)

gradient_files = []
center_x, center_y = 540, 540

# 人気の高そうなパステル4色を選んでグラデーション効果
gradient_colors = ['pink', 'lavender', 'mint', 'peach']

for color_key in gradient_colors:
    color_info = pastel_colors[color_key]
    print(f"グラデーション効果適用中: {color_info['name']}")
    
    # 結果配列を作成
    gradient_array = eye_array.copy()
    
    # グラデーション用の色のバリエーション
    base_hue = color_info['hue']
    colors_gradient = [
        # 内側（明るめ）
        colorsys.hsv_to_rgb(base_hue, max(0.1, color_info['sat'] - 0.1), min(1.0, color_info['val'] + 0.05)),
        # 中間（ベース色）
        colorsys.hsv_to_rgb(base_hue, color_info['sat'], color_info['val']),
        # 外側（少し深め）
        colorsys.hsv_to_rgb(base_hue, min(0.6, color_info['sat'] + 0.1), max(0.7, color_info['val'] - 0.1)),
        # ハイライト（とても明るい）
        colorsys.hsv_to_rgb(base_hue, max(0.05, color_info['sat'] - 0.15), min(1.0, color_info['val'] + 0.1))
    ]
    
    # RGBに変換
    colors_gradient = [tuple(int(c * 255) for c in rgb) for rgb in colors_gradient]
    
    for y in range(eye_array.shape[0]):
        for x in range(eye_array.shape[1]):
            if mask_array[y, x] > 50:  # マスクされた領域
                distance_from_center = np.sqrt((x - center_x)**2 + (y - center_y)**2)
                
                # 元の色の明度を取得
                original_color = eye_array[y, x][:3]
                original_brightness = np.mean(original_color) / 255.0
                alpha = eye_array[y, x][3]
                
                # 距離に基づく色のブレンディング
                if distance_from_center < 80:  # 内側 - 明るいパステル
                    base_color = colors_gradient[0]
                elif distance_from_center < 120:  # 中間 - ベース色
                    t = (distance_from_center - 80) / 40
                    base_color = [
                        int(colors_gradient[0][i] * (1-t) + colors_gradient[1][i] * t) 
                        for i in range(3)
                    ]
                elif distance_from_center < 160:  # 外側 - 深め
                    t = (distance_from_center - 120) / 40
                    base_color = [
                        int(colors_gradient[1][i] * (1-t) + colors_gradient[2][i] * t) 
                        for i in range(3)
                    ]
                else:  # 最外側
                    base_color = colors_gradient[2]
                    
                # ハイライト効果（上部）
                if y < center_y - 30 and distance_from_center < 120:
                    highlight_strength = max(0, (center_y - 30 - y) / 50) * 0.6
                    base_color = [
                        int(base_color[i] * (1 - highlight_strength) + colors_gradient[3][i] * highlight_strength)
                        for i in range(3)
                    ]
                
                # 元の明度を70%保持
                final_color = [
                    int(base_color[i] * (0.3 + original_brightness * 0.7))
                    for i in range(3)
                ]
                final_color = [max(0, min(255, c)) for c in final_color]
                
                gradient_array[y, x] = (*final_color, alpha)
    
    # グラデーション版を保存
    gradient_filename = f'eye_color_pastel_{color_key}_gradient.png'
    gradient_image = Image.fromarray(gradient_array, 'RGBA')
    gradient_image.save(gradient_filename)
    gradient_files.append(gradient_filename)
    
    print(f"✓ グラデーション版完了: {gradient_filename}")

print(f"\n✨ グラデーション効果付きパステル {len(gradient_files)}色完了!")