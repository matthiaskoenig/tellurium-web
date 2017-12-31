# Script for generating thumbnails with imagemagicks
convert "mediatype/*.png[x16]" -set filename:base "%[base]" "mediatype/thumbnails/%[filename:base].png"
