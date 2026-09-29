#!/usr/bin/env python3
import pathlib,re,unittest

ROOT=pathlib.Path(__file__).parents[1]
PS=(ROOT/"app"/"FreeNetHub.ps1").read_text(encoding="utf-8-sig")

def rgb(h):
    h=h.lstrip("#")
    return tuple(int(h[i:i+2],16)/255.0 for i in (0,2,4))
def lum(h):
    vals=[]
    for c in rgb(h):
        vals.append(c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4)
    return .2126*vals[0]+.7152*vals[1]+.0722*vals[2]
def contrast(a,b):
    x,y=sorted((lum(a),lum(b)),reverse=True)
    return (x+.05)/(y+.05)
def theme_block(name):
    if name=="light":
        m=re.search(r"if\(\$name -eq 'light'\)\{\s*@\{([^}]*)\}",PS,re.S)
    else:
        m=re.search(r"\}else\{\s*@\{([^}]*)\}",PS,re.S)
    if not m: raise AssertionError("theme block missing: "+name)
    return dict(re.findall(r"([A-Za-z]+)='(#[0-9A-Fa-f]{6})'",m.group(1)))

class Contrast(unittest.TestCase):
    def test_theme_text_contrast(self):
        for theme in ("light","dark"):
            c=theme_block(theme)
            for bg in ("Soft","SelectedFill","PillFill","TableHeader","UpdatePanel","Panel"):
                for fg in ("Ink","Muted"):
                    with self.subTest(theme=theme,fg=fg,bg=bg):
                        self.assertGreaterEqual(contrast(c[fg],c[bg]),4.5)
    def test_light_accent_contrast(self):
        c=theme_block("light")
        self.assertGreaterEqual(contrast(c["Accent"],c["UpdatePanel"]),4.5)
        self.assertGreaterEqual(contrast(c["Accent"],c["Panel"]),4.5)
        self.assertGreaterEqual(contrast("#FFFFFF",c["Accent"]),4.5)
    def test_no_old_hardcoded_method_card_fill(self):
        self.assertNotIn("ConvertFromString('#102238')",PS)
        self.assertNotIn("ConvertFromString('#164D58')",PS)

if __name__=="__main__":
    unittest.main()
