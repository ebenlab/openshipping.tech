"""Build site/explorer.html: a standalone HTML document of the industry map (the artifact source is site/industry-map.html)."""
import pathlib
root = pathlib.Path(__file__).resolve().parent.parent
src = (root / "site" / "industry-map.html").read_text()
title_end = src.index("</title>") + len("</title>")
style_end = src.index("</style>") + len("</style>")
head = src[:style_end]
body = src[style_end:]
out = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
       '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
       '<style>html,body{margin:0}[hidden]{display:none!important}</style>\n'
       + head + "\n</head>\n<body>\n" + body + "\n</body>\n</html>\n")
(root / "site" / "explorer.html").write_text(out)
print("wrote site/explorer.html", len(out))
