import os
from PIL import Image, ImageDraw, ImageFilter

def create_clover_icon():
    size = 1024
    center = size // 2

    # 1. Create base leaf canvas (leaf pointing UP, tip at center)
    # To get high quality anti-aliasing, we draw at 2x size (2048x2048) and scale down later
    canvas_size = size * 2
    c_center = canvas_size // 2
    
    # We want a glow layer and a solid layer
    # Draw hollow leaf outlines: a circular arc and two lines meeting at the tip
    def draw_leaf_outline(radius, circle_y, tip_y, thickness, color):
        img = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        cx = c_center
        cy = circle_y
        
        # Bounding box for the circle
        bbox = [cx - radius, cy - radius, cx + radius, cy + radius]
        
        # 1. Draw top arc of the circle (from 180 degrees to 360/0 degrees)
        draw.arc(bbox, start=180, end=360, fill=color, width=thickness)
        
        # 2. Draw two lines from the ends of the arc to the tip
        left_end = (cx - radius, cy)
        right_end = (cx + radius, cy)
        tip = (c_center, tip_y)
        
        draw.line([left_end, tip], fill=color, width=thickness)
        draw.line([right_end, tip], fill=color, width=thickness)
        
        return img

    # --- SHARP OUTLINE LEAF PARAMS (at 2x scale) ---
    radius = 230
    circle_y = c_center - 270
    tip_y = c_center
    sharp_thickness = 34
    sharp_color = (0, 212, 255, 255)
    
    solid_leaf_base = draw_leaf_outline(radius, circle_y, tip_y, sharp_thickness, sharp_color)
    
    # --- GLOW OUTLINE LEAF PARAMS (at 2x scale) ---
    glow_thickness = 70
    glow_color = (0, 212, 255, 255)
    
    glow_leaf_base = draw_leaf_outline(radius, circle_y, tip_y, glow_thickness, glow_color)

    # 2. Rotate and composite 4 leaves for both solid and glow layers
    solid_clover = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    glow_clover = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    
    angles = [0, 90, 180, 270]  # Pointing straight (UP, DOWN, LEFT, RIGHT)
    
    for angle in angles:
        # Rotate around center
        r_solid = solid_leaf_base.rotate(angle, resample=Image.Resampling.BICUBIC)
        solid_clover = Image.alpha_composite(solid_clover, r_solid)
        
        r_glow = glow_leaf_base.rotate(angle, resample=Image.Resampling.BICUBIC)
        glow_clover = Image.alpha_composite(glow_clover, r_glow)

    # Apply blur to the glow layer to create the bloom effect
    # Since we are at 2x scale, we use a larger blur radius (e.g., 40)
    glow_clover = glow_clover.filter(ImageFilter.GaussianBlur(35))
    
    # Make the glow semi-transparent (e.g. 50% opacity)
    # We can do this by splitting channels and multiplying alpha
    r, g, b, a = glow_clover.split()
    a = a.point(lambda p: int(p * 0.45))
    glow_clover = Image.merge("RGBA", (r, g, b, a))

    # 3. Composite Solid over Glow
    final_canvas = Image.alpha_composite(glow_clover, solid_clover)
    
    # 4. Scale down to target size (1024x1024)
    final_img = final_canvas.resize((size, size), Image.Resampling.LANCZOS)
    
    # 5. Crop transparent padding so the clover fills the icon space
    bbox = final_img.getbbox()
    if bbox:
        cropped = final_img.crop(bbox)
        # Make the clover fill 92% of the canvas
        target_size = int(size * 0.92)
        w, h = cropped.size
        max_dim = max(w, h)
        
        new_w = int(w * target_size / max_dim)
        new_h = int(h * target_size / max_dim)
        
        resized_cropped = cropped.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # Paste centered back on a square transparent canvas
        maximized_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        paste_x = (size - new_w) // 2
        paste_y = (size - new_h) // 2
        maximized_img.paste(resized_cropped, (paste_x, paste_y), resized_cropped)
        final_img = maximized_img

    # Save the PNG (transparent background!)
    assets_dir = r"C:\Projects\LuckyHelper\assets"
    os.makedirs(assets_dir, exist_ok=True)
    
    png_path = os.path.join(assets_dir, "icon.png")
    final_img.save(png_path, "PNG")
    print(f"PNG saved to: {png_path}")
    
    # Save as ICO with multiple standard Windows sizes
    ico_path = os.path.join(assets_dir, "icon.ico")
    sizes = [256, 128, 64, 48, 32, 16]
    icons = [final_img.resize((s, s), Image.Resampling.LANCZOS) for s in sizes]
    icons[0].save(
        ico_path,
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=icons[1:]
    )
    print(f"ICO saved to: {ico_path}")

if __name__ == "__main__":
    create_clover_icon()
