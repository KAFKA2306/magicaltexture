# Frequently Asked Questions

## General Usage

### Q: What image formats are supported?
**A:** We support most common formats including PNG, JPG, JPEG, and WebP. PNG is recommended for best quality, especially if your texture has transparency.

### Q: My generated image looks wrong - what happened?
**A:** This is usually a mask issue. Make sure your mask has:
- **White areas** where you want color applied (the iris)
- **Black areas** that should stay unchanged (pupil, whites of eyes, eyelashes)
- Clean, clear boundaries between white and black regions

### Q: The colors look too bright/dim - how do I fix this?
**A:** Use the Advanced Settings:
- Reduce **Color Intensity** (below 1.0) for more subtle colors
- Adjust **Original Brightness** to blend more/less with the original texture
- Try different effect modes - Gradient tends to look most natural

### Q: Can I use this for commercial projects?
**A:** Yes! The generated textures are yours to use however you like. The tool itself is designed for professional game development, VTubing, and digital art workflows.

## Technical Issues

### Q: The app is loading slowly or crashing
**A:** Try these solutions:
1. **Reduce image size** - Very large images (over 2048x2048) can be slow
2. **Check your internet** - The app runs in your browser and needs a stable connection
3. **Clear browser cache** - Sometimes old data can cause issues
4. **Try a different browser** - Chrome and Firefox work best

### Q: My batch generation is taking forever
**A:** Batch processing time depends on:
- **Number of combinations** - Each color × each effect = one generation
- **Image size** - Larger images take longer
- **Server load** - Try again during off-peak hours

To speed things up:
- Select fewer colors and effects
- Resize your images before uploading
- Use smaller batch sizes

### Q: The ZIP download isn't working
**A:** This can happen if:
- Your browser blocks pop-ups (allow downloads from the site)
- The batch generation didn't complete successfully
- Try right-clicking the download link and "Save as..."

## Creating Masks

### Q: How do I make a mask from my eye texture?
**A:** You can use any image editor:

1. **In Photoshop/GIMP:**
   - Open your eye texture
   - Create a new layer
   - Paint white over the iris (colored part of the eye)
   - Fill the background with black
   - Save as PNG

2. **Quick method:**
   - Use the magic wand tool to select the iris
   - Fill selection with white
   - Invert selection and fill with black

### Q: My mask isn't working properly
**A:** Common mask problems:
- **Too much white** - Only color the iris, not the entire eye
- **Soft edges** - Use hard brushes for clean boundaries
- **Gray areas** - Make sure it's pure black (0,0,0) and white (255,255,255)
- **Wrong size** - The mask will be automatically resized, but matching sizes work best

### Q: Can I use selection tools to create masks?
**A:** Absolutely! Selection tools are often the easiest way:
1. Select the iris area with lasso, magic wand, or other selection tools
2. Create a new image/layer  
3. Fill the selection with white
4. Fill the rest with black

## Colors & Effects

### Q: Why don't the colors match exactly what I see in the preview?
**A:** The final colors depend on:
- Your original texture's colors and lighting
- The **Original Brightness** setting (how much original texture shows through)
- Your monitor's color calibration
- The effect mode you've chosen

### Q: Can I create custom colors?
**A:** Currently, we provide 9 carefully selected pastel colors that work well for eye textures. These were chosen to create natural-looking results while maintaining the artistic "pastel" aesthetic.

### Q: What's the difference between Basic, Gradient, and Aurora modes?

- **Basic** - Uniform color replacement. Good for clean, consistent looks
- **Gradient** - Smooth transitions from center to edge with highlights. Most natural-looking
- **Aurora** - Color shimmer effects. Great for fantasy/magical characters

### Q: When should I use emission masks?
**A:** Emission masks are for 3D applications (games, VRChat, etc.) that support glowing effects. They create a ring around the pupil that can emit light. Skip this unless you're working with 3D software that supports emission mapping.

## Troubleshooting

### Q: My results don't look like the examples
**A:** Make sure:
1. Your mask properly isolates just the iris
2. Your original texture has good contrast and detail
3. You're using appropriate settings for your image
4. Try the Gradient mode first - it works best for most textures

### Q: The app seems broken or won't load
**A:** Try:
1. Refreshing the page (F5 or Ctrl+R)
2. Clearing browser cache and cookies
3. Using a different browser or incognito mode  
4. Checking your internet connection
5. Waiting a few minutes - the service might be restarting

### Q: Can I process multiple images at once?
**A:** The batch feature processes one base image with multiple colors and effects. To process completely different images, you'll need to run them separately. Each image needs its own mask.

## Still Need Help?

If you can't find the answer here:

1. **Check the documentation** - Detailed guides are available for every feature
2. **Try the examples** - Sometimes seeing it in action helps
3. **Start simple** - Use Basic mode with default settings first
4. **Check your mask** - 90% of issues are mask-related

Remember: Great results come from good masks and appropriate settings for your specific texture! ✨