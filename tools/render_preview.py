#!/usr/bin/env python3
"""
Renderiza previews del modelo (sin necesidad de Minecraft): rotaciones de caja, jerarquia de huesos con
posicion/rotacion/escala de la animacion, sombreado tipo Minecraft y capa brillante (glowmask).

Ejecuta desde la carpeta del mod:  python3 tools/render_preview.py
"""
import json, math, os
from PIL import Image, ImageDraw, ImageFilter

R = "src/main/resources/assets/dinowarden"
geo = json.load(open(f"{R}/geo/dinowarden.geo.json"))["minecraft:geometry"][0]["bones"]
anims = json.load(open(f"{R}/animations/dinowarden.animation.json"))["animations"]
tex = Image.open(f"{R}/textures/entity/dinowarden.png").convert("RGBA")
glow = Image.open(f"{R}/textures/entity/dinowarden_glowmask.png").convert("RGBA")
TW = tex.size[0]
bones = {b["name"]: b for b in geo}


def sample(track, t):
    ks = sorted((float(k), v) for k, v in track.items())
    if t <= ks[0][0]: return ks[0][1]
    for (t0, a), (t1, b) in zip(ks, ks[1:]):
        if t0 <= t <= t1:
            f = (t - t0) / (t1 - t0) if t1 > t0 else 0
            return [a[i] + (b[i] - a[i]) * f for i in range(3)]
    return ks[-1][1]


def pose_at(anim, t):
    pose = {}
    if not anim: return pose
    for name, ch in anims[anim]["bones"].items():
        pose[name] = {k: sample(v, t) for k, v in ch.items()}
    return pose


def rot(p, ang, pivot):
    x, y, z = p[0] - pivot[0], p[1] - pivot[1], p[2] - pivot[2]
    ax, ay, az = [math.radians(-ang[0]), math.radians(-ang[1]), math.radians(ang[2])]   # convencion GeckoLib
    y, z = y * math.cos(ax) - z * math.sin(ax), y * math.sin(ax) + z * math.cos(ax)
    x, z = x * math.cos(ay) + z * math.sin(ay), -x * math.sin(ay) + z * math.cos(ay)
    x, y = x * math.cos(az) - y * math.sin(az), x * math.sin(az) + y * math.cos(az)
    return (x + pivot[0], y + pivot[1], z + pivot[2])


def chain(name):
    out = []
    while name:
        out.append(name)
        name = bones[name].get("parent")
    return out


def transform(name, p, pose):
    for n in chain(name):                    # hueso propio primero, luego sus padres
        pz = pose.get(n, {})
        pv = bones[n]["pivot"]
        sc = pz.get("scale")
        if sc:
            p = (pv[0] + (p[0] - pv[0]) * sc[0], pv[1] + (p[1] - pv[1]) * sc[1], pv[2] + (p[2] - pv[2]) * sc[2])
        r = pz.get("rotation")
        if r: p = rot(p, r, pv)
        ps = pz.get("position")
        if ps: p = (p[0] + ps[0], p[1] + ps[1], p[2] + ps[2])
    return p


def sub(a, b): return (a[0] - b[0], a[1] - b[1], a[2] - b[2])
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
def norm(a):
    l = math.sqrt(dot(a, a)) or 1.0
    return (a[0] / l, a[1] / l, a[2] / l)


L1 = norm((0.2, 1.0, -0.7))
L2 = norm((-0.2, 1.0, 0.7))


def quads(pose):
    """Lista de (puntos3D, color, brilla, brillo) por texel."""
    out = []
    for name, b in bones.items():
        for cb in b.get("cubes", []):
            ox, oy, oz = cb["origin"]; sx, sy, sz = cb["size"]; u, v = cb["uv"]
            crot, cpiv = cb.get("rotation"), cb.get("pivot")

            def P(fx, fy, fz, ox=ox, oy=oy, oz=oz, sx=sx, sy=sy, sz=sz, crot=crot, cpiv=cpiv):
                p = (ox + sx * fx, oy + sy * fy, oz + sz * fz)
                if crot: p = rot(p, crot, cpiv)
                return p
            center = transform(name, P(.5, .5, .5), pose)
            ix, iy, iz = sx, sy, sz
            faces = [(u + iz, v + iz, ix, iy, lambda a, b_, ix=ix, iy=iy: P(1 - a / ix, 1 - b_ / iy, 0)),
                     (u + 2 * iz + ix, v + iz, ix, iy, lambda a, b_, ix=ix, iy=iy: P(a / ix, 1 - b_ / iy, 1)),
                     (u, v + iz, iz, iy, lambda a, b_, iz=iz, iy=iy: P(1, 1 - b_ / iy, 1 - a / iz)),
                     (u + iz + ix, v + iz, iz, iy, lambda a, b_, iz=iz, iy=iy: P(0, 1 - b_ / iy, a / iz)),
                     (u + iz, v, ix, iz, lambda a, b_, ix=ix, iz=iz: P(a / ix, 1, b_ / iz)),
                     (u + iz + ix, v, ix, iz, lambda a, b_, ix=ix, iz=iz: P(a / ix, 0, 1 - b_ / iz))]
            for (tu, tv, w, h, fn) in faces:
                p00 = transform(name, fn(0, 0), pose)
                p10 = transform(name, fn(w, 0), pose)
                p01 = transform(name, fn(0, h), pose)
                n = norm(cross(sub(p10, p00), sub(p01, p00)))
                mid = transform(name, fn(w / 2, h / 2), pose)
                if dot(n, sub(mid, center)) < 0: n = (-n[0], -n[1], -n[2])
                light = min(1.0, 0.4 + 0.6 * (max(0.0, dot(n, L1)) + max(0.0, dot(n, L2))))
                for j in range(h):
                    for i in range(w):
                        col = tex.getpixel((tu + i, tv + j))
                        if col[3] == 0 and glow.getpixel((tu + i, tv + j))[3] == 0:
                            continue
                        g = glow.getpixel((tu + i, tv + j))[3] > 0
                        if g: col = tex.getpixel((tu + i, tv + j))
                        pts = [transform(name, fn(a_, b_), pose) for a_, b_ in ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))]
                        out.append((pts, col, g, light))
    return out


# hitboxes (bloques): (nombre, adelante(+)/atras(-), y_base, ancho, alto)  -> deben coincidir con DinoWardenEntity
HITBOXES = [("cuerpo", 0.0, 0.0, 1.9, 3.1), ("cabeza", 2.35, 1.95, 1.5, 1.7), ("cuello", 1.3, 1.9, 1.0, 1.2),
            ("cola A", -1.4, 1.65, 1.2, 1.0), ("cola B", -2.6, 1.7, 1.1, 0.85), ("cola C", -3.85, 1.8, 1.4, 0.7)]


def render(pose, yaw, pitch=-14, size=(760, 640), scale=6.2, ss=2, center=(0, 28, 4), boxes=False, yoff=0.66,
           bg=(46, 52, 58), ambient=1.0, bloom=False, ground=None):
    W, H = size[0] * ss, size[1] * ss
    img = Image.new("RGBA", (W, H), bg + (255,))
    d = ImageDraw.Draw(img)
    cy, sy_ = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))

    def proj(p):
        x, y, z = p[0] - center[0], p[1] - center[1], p[2] - center[2]
        x, z = x * cy + z * sy_, -x * sy_ + z * cy
        y, z = y * cp - z * sp, y * sp + z * cp
        return (W / 2 + x * scale * ss, H * yoff - y * scale * ss), z

    if ground is not None:          # linea de suelo para ver los pies
        a, _ = proj((-200, ground, 0)); b, _ = proj((200, ground, 0))
        d.line([a, b], fill=(90, 100, 110, 255), width=2 * ss)
    items = []
    for pts, col, g, light in quads(pose):
        pr = [proj(p) for p in pts]
        depth = sum(z for _, z in pr) / 4
        items.append((depth, [q for q, _ in pr], col, g, light))
    items.sort(key=lambda t: t[0])
    glows = []
    for depth, poly, col, g, light in items:
        if g:
            c_ = col[:3]
            glows.append((poly, c_))
        else:
            f = light * ambient
            c_ = tuple(min(255, int(v * f)) for v in col[:3])
        d.polygon(poly, fill=c_ + (255,), outline=c_ + (255,))
    if bloom and glows:
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        for poly, c_ in glows:
            ld.polygon(poly, fill=c_ + (255,))
        blur = layer.filter(ImageFilter.GaussianBlur(5 * ss))
        img = Image.alpha_composite(img, Image.merge("RGBA", (blur.split()[0], blur.split()[1], blur.split()[2],
                                                                blur.split()[3].point(lambda v: int(v * 0.55)))))
        d = ImageDraw.Draw(img)
        for poly, c_ in glows:                       # los pixeles brillantes quedan nitidos encima
            d.polygon(poly, fill=c_ + (255,), outline=c_ + (255,))
    if boxes:
        for nm, fwd, y0, w, h in HITBOXES:
            cz = -fwd * 16; hw = w * 8
            c = [(x, y, z) for x in (-hw, hw) for y in (y0 * 16, (y0 + h) * 16) for z in (cz - hw, cz + hw)]
            P = [proj(p)[0] for p in c]
            for i in range(8):
                for j in range(i + 1, 8):
                    if bin(i ^ j).count("1") == 1:
                        d.line([P[i], P[j]], fill=(255, 210, 60, 255), width=2 * ss // 2 + 1)
    return img.resize(size, Image.LANCZOS)


def label(im, text):
    ImageDraw.Draw(im).text((12, 10), text, fill=(230, 240, 240, 255))
    return im


def sheet(images, cols, w, h):
    rows = (len(images) + cols - 1) // cols
    s = Image.new("RGBA", (w * cols, h * rows))
    for i, im in enumerate(images):
        s.paste(im, ((i % cols) * w, (i // cols) * h))
    return s


if __name__ == "__main__":
    os.makedirs("preview", exist_ok=True)
    idle = pose_at("animation.dinowarden.idle", 1.0)
    roar = pose_at("animation.dinowarden.roar", 1.9)
    swim = pose_at("animation.dinowarden.swim", 0.4)
    walk = pose_at("animation.dinowarden.walk", 0.35)
    bite = pose_at("animation.dinowarden.bite", 0.4)
    sw, sh = 760, 600
    P = [label(render(idle, 145, size=(sw, sh), scale=5.4, center=(0, 28, 10), yoff=0.62), "REPOSO - 3/4 frontal"),
         label(render(idle, 90, size=(sw, sh), scale=5.2, center=(0, 28, 10), boxes=True, yoff=0.62), "REPOSO - lateral + HITBOX (amarillo)"),
         label(render(roar, 90, size=(sw, sh), scale=5.0, center=(0, 30, 10), yoff=0.62), "RUGIDO (sonic boom)"),
         label(render(swim, 90, size=(sw, sh), scale=5.2, center=(0, 22, 10), yoff=0.62), "NADANDO"),
         label(render(walk, 0, pitch=-75, size=(sw, sh), scale=5.0, center=(0, 28, 20), yoff=0.5), "COLA ONDULANDO - vista superior"),
         label(render(idle, 0, pitch=-75, size=(sw, sh), scale=5.0, center=(0, 28, 20), boxes=True, yoff=0.5), "HITBOX - vista superior")]
    sheet(P, 2, sw, sh).save("preview/modelo_preview.png")

    hp = [label(render(idle, 145, size=(600, 520), scale=11, center=(0, 44, -34), yoff=0.6), "CABEZA cerrada 3/4"),
          label(render(idle, 90, size=(600, 520), scale=11, center=(0, 44, -34), yoff=0.6), "CABEZA lateral"),
          label(render(roar, 145, size=(600, 520), scale=9, center=(0, 40, -34), yoff=0.7), "CABEZA rugiendo 3/4")]
    sheet(hp, 3, 600, 520).save("preview/cabeza_preview.png")

    # ciclo de pasos (caminar y correr): 4 instantes de cada uno, lateral con linea de suelo
    def gait_row(anim, L, strike, tag):
        ims = []
        for k, (ph, nm) in enumerate(((0.0, "apoyo"), (0.2, "medio"), (0.45, "empuje"), (0.7, "vuelo"))):
            t = L * (strike + ph) % L
            ims.append(label(render(pose_at(anim, t), 90, pitch=-4, size=(560, 420), scale=4.2, center=(0, 26, 8),
                                    yoff=0.62, ground=0), "%s: %s (t=%.2fs)" % (tag, nm, t)))
        return ims
    g = gait_row("animation.dinowarden.walk", anims["animation.dinowarden.walk"]["animation_length"], 0.1, "CAMINAR") + \
        gait_row("animation.dinowarden.run", anims["animation.dinowarden.run"]["animation_length"], 0.1, "CORRER")
    sheet(g, 4, 560, 420).save("preview/ciclo_pasos_preview.png")

    # vista tipo referencia: 3/4 en cueva oscura con brillo (emisivo) y la mandibula abierta
    dark = [label(render(roar, 125, pitch=-10, size=(760, 760), scale=6.4, center=(0, 30, 6), yoff=0.6, bg=(10, 14, 18),
                         ambient=0.5, bloom=True), "VISTA CUEVA (emisivo) - rugido"),
            label(render(bite, 140, pitch=-10, size=(760, 760), scale=6.4, center=(0, 28, 0), yoff=0.6, bg=(10, 14, 18),
                         ambient=0.5, bloom=True), "VISTA CUEVA (emisivo) - mordida")]
    sheet(dark, 2, 760, 760).save("preview/cueva_preview.png")
    print("ok")
