"""Build custom_components/dengue_watch/frontend/mosquito-watch-card.js from frontend_src."""
import pathlib
root = pathlib.Path(__file__).resolve().parent
src = (root / "card.src.js").read_text(encoding="utf-8")
assert src.count("/*__ICON__*/") == 1 and src.count("/*__GEO__*/") == 1
out = src.replace("/*__ICON__*/", (root / "icon.txt").read_text().strip()).replace("/*__GEO__*/", (root / "provinces_geo.json").read_text().strip())
dst = root.parent / "custom_components" / "dengue_watch" / "frontend" / "mosquito-watch-card.js"
dst.write_text(out, encoding="utf-8")
print(dst.name, len(out), "bytes")
