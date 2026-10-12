#!/usr/bin/env python3
"""
Genera el modelo (geo.json), la textura (png + glowmask) y las animaciones (animation.json)
del Dino Warden v2 (mucho mas detalle, referencia: Warden-dragon de sculk).

Ejecuta:  python3 tools/generate_assets.py
Despues:  python3 tools/render_preview.py   (previews en /preview)

- Todas las cajas usan tamaños ENTEROS para que el UV de caja sea exacto.
- Los huesos "_r" se generan automaticamente como espejo de los "_l".
- La textura "dinowarden_glowmask.png" marca los pixeles cian que brillan en la oscuridad
  (GeckoLib AutoGlowingGeoLayer: ver DinoWardenRenderer).
- Las animaciones incluyen "sound_effects" (step_l, step_r, stomp_l, stomp_r, slam): el cliente los usa
  para el sonido de pisada, el polvo y el TEMBLOR DE CAMARA exactamente cuando la pata toca el suelo.
"""
import json, math, os, random
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RES = os.path.join(ROOT, "src/main/resources/assets/dinowarden")
for d in ("geo", "animations", "textures/entity"):
    os.makedirs(os.path.join(RES, d), exist_ok=True)


# =====================================================================================
#  MODELO
# =====================================================================================
def c(o, s, kind, rot=None, piv=None):
    """Una caja: origen, tamaño, tipo de pintura, rotacion opcional (grados) y pivote de la rotacion."""
    return (list(o), list(s), kind, rot, piv)


def mirror_cube(cb):
    o, s, kind, rot, piv = cb
    o2 = [-(o[0] + s[0]), o[1], o[2]]
    rot2 = None if rot is None else [rot[0], -rot[1], -rot[2]]
    piv2 = None if piv is None else [-piv[0], piv[1], piv[2]]
    return (o2, list(s), kind, rot2, piv2)


BONES = []          # (nombre, padre, pivote, [cajas])


def bone(name, parent, pivot, cubes):
    BONES.append((name, parent, list(pivot), cubes))


def pair(name, parent, pivot, cubes, parent_is_pair=False):
    """Crea name_l (tal cual) y name_r (espejo)."""
    bone(name + "_l", parent + ("_l" if parent_is_pair else ""), pivot, cubes)
    bone(name + "_r", parent + ("_r" if parent_is_pair else ""),
         [-pivot[0], pivot[1], pivot[2]], [mirror_cube(cb) for cb in cubes])


bone("root", None, [0, 0, 0], [])

# ----------------------------------------------------------------------- CUERPO
bone("body", "root", [0, 32, 0], [
    c([-10, 22, -13], [20, 22, 28], "skin"),                 # torso (cubo grande de sculk)
    c([-8, 44, -12], [16, 2, 26], "ridge"),                  # cresta dorsal elevada
    c([-9, 38, -16], [18, 9, 5], "skin_hi"),                 # joroba de los hombros
    c([-8, 19, -11], [16, 3, 22], "belly"),                  # vientre
    c([-7, 22, -14], [14, 13, 1], "ribglow"),                # pecho luminoso entre las barras
    c([-6, 23, -15], [12, 2, 1], "bone"),                    # barras de hueso del pecho (costillar frontal)
    c([-6, 26, -15], [12, 2, 1], "bone"),
    c([-5, 29, -15], [10, 2, 1], "bone"),
    c([-5, 32, -15], [10, 2, 1], "bone"),
    c([-7, 23, -15], [1, 11, 1], "bone"), c([6, 23, -15], [1, 11, 1], "bone"),
    c([-11, 21, -11], [1, 13, 23], "ribglow"),               # cavidad luminosa bajo las costillas
    c([10, 21, -11], [1, 13, 23], "ribglow"),
    c([-9, 40, 11], [18, 4, 5], "skin_hi"),                  # cadera (union con la cola)
])
for side, sx in (("l", 1), ("r", -1)):
    cubes = []
    for z in (-10, -5, 0, 5, 10):
        h = 14 if z in (-5, 0, 5) else 12
        if sx > 0:
            cubes.append(c([10, 34 - h, z], [2, h, 3], "bone"))
            cubes.append(c([8, 32 - h, z], [4, 2, 3], "bone"))       # curva inferior de la costilla
            cubes.append(c([10, 34, z], [1, 2, 2], "bone"))           # punta superior
        else:
            cubes.append(c([-12, 34 - h, z], [2, h, 3], "bone"))
            cubes.append(c([-12, 32 - h, z], [4, 2, 3], "bone"))
            cubes.append(c([-11, 34, z], [1, 2, 2], "bone"))
    bone("ribs_" + side, "body", [0, 32, 0], cubes)

# orbes cian que flotan en los costados
bone("orb_l", "body", [13, 37, -1], [c([11, 36, -3], [4, 4, 4], "orb"), c([13, 30, 4], [3, 3, 3], "orb"),
                                     c([12, 40, 6], [2, 2, 2], "orb"), c([14, 33, -8], [2, 2, 2], "orb")])
bone("orb_r", "body", [-13, 37, -1], [mirror_cube(cb) for cb in
                                      [c([11, 36, -3], [4, 4, 4], "orb"), c([13, 30, 4], [3, 3, 3], "orb"),
                                       c([12, 40, 6], [2, 2, 2], "orb"), c([14, 33, -8], [2, 2, 2], "orb")]])

# puas dorsales: 3 grupos (cada grupo se mueve con un poco de retraso)
SPINE_H = {-10: 5, -6: 7, -2: 8, 2: 9, 6: 8, 10: 6}
for name, zs in (("spines_a", (-10, -6)), ("spines_b", (-2, 2)), ("spines_c", (6, 10))):
    cubes = []
    for z in zs:
        h = SPINE_H[z]
        cubes.append(c([-3, 46, z - 1], [6, 2, 5], "spinebase"))
        cubes.append(c([-1, 48, z], [2, h - 3, 3], "bone", rot=[-12, 0, 0], piv=[0, 48, z + 1]))
        cubes.append(c([-1, 48 + h - 3, z + 1], [2, 3, 1], "bone", rot=[-12, 0, 0], piv=[0, 48, z + 1]))
        cubes.append(c([-1, 46, z - 2], [2, 2, 1], "glow"))
    bone(name, "body", [0, 46, zs[0]], cubes)

# brotes de sculk (tentaculos finos) sobre el lomo
bone("sprouts", "body", [0, 45, 0], [
    c([6, 44, -9], [1, 3, 1], "sprout"), c([-7, 44, -4], [1, 4, 1], "sprout"),
    c([7, 44, 4], [1, 3, 1], "sprout"), c([-6, 44, 9], [1, 3, 1], "sprout"),
    c([8, 44, 11], [1, 2, 1], "sprout"), c([-8, 44, -10], [1, 2, 1], "sprout"),
    c([3, 46, 1], [1, 2, 1], "sprout"), c([-4, 46, 5], [1, 2, 1], "sprout")])

# ----------------------------------------------------------------------- COLA (5 segmentos)
bone("tail1", "body", [0, 34, 13], [
    c([-7, 27, 13], [14, 14, 14], "skin"), c([-8, 26, 19], [16, 16, 2], "ring"),
    c([-1, 41, 16], [2, 4, 3], "bone"), c([-1, 41, 22], [2, 4, 3], "bone"),
    c([-6, 25, 15], [12, 2, 10], "belly")])
bone("tail2", "tail1", [0, 34, 27], [
    c([-5, 28, 27], [10, 11, 12], "skin"), c([-6, 27, 32], [12, 13, 2], "ring"),
    c([-1, 39, 30], [2, 4, 3], "bone"), c([-1, 39, 35], [2, 3, 3], "bone")])
bone("tail3", "tail2", [0, 33, 39], [
    c([-4, 29, 39], [8, 9, 11], "skin"), c([-5, 28, 43], [10, 11, 2], "ring"),
    c([-1, 38, 42], [2, 3, 3], "bone"), c([-1, 38, 47], [2, 3, 2], "bone")])
bone("tail4", "tail3", [0, 33, 50], [
    c([-3, 30, 50], [6, 7, 10], "skin"), c([-4, 29, 54], [8, 9, 2], "ring"),
    c([-1, 37, 54], [2, 3, 2], "bone")])
bone("tail5", "tail4", [0, 33, 60], [
    c([-2, 31, 60], [4, 5, 10], "skin"), c([-1, 36, 63], [2, 2, 2], "bone"),
    c([-1, 29, 69], [2, 7, 4], "bone"), c([-2, 31, 70], [4, 2, 3], "bone"),
    c([-1, 29, 73], [2, 3, 2], "bone")])

# ----------------------------------------------------------------------- CUELLO Y CABEZA
bone("neck", "body", [0, 38, -12], [
    c([-6, 33, -24], [12, 13, 12], "skin"),
    c([6, 35, -23], [2, 9, 9], "plate"), c([-8, 35, -23], [2, 9, 9], "plate"),
    c([-5, 31, -22], [10, 2, 2], "bone"), c([-5, 31, -18], [10, 2, 2], "bone"), c([-5, 31, -14], [10, 2, 2], "bone"),
    c([-1, 46, -22], [2, 4, 3], "bone"), c([-1, 46, -17], [2, 5, 3], "bone"), c([-1, 46, -12], [2, 4, 3], "bone")])

HEAD = [
    c([-8, 37, -32], [16, 12, 12], "cranium"),               # craneo ancho
    c([-6, 38, -42], [12, 9, 10], "snout"),                  # hocico, parte trasera (se angosta como T-rex)
    c([-5, 38, -54], [10, 8, 12], "snout"),                  # hocico, parte delantera mas angosta
    c([-4, 37, -56], [8, 9, 2], "glowwall"),                 # pared brillante tras los listones
    c([-3, 47, -47], [6, 2, 12], "snout_top"),               # puente nasal
    c([-4, 46, -55], [8, 3, 8], "snout_top"),                # NARIZ: bulto sobre la punta del hocico
    c([-3, 47, -56], [2, 2, 1], "nostril"), c([1, 47, -56], [2, 2, 1], "nostril"),   # fosas nasales
    c([-5, 49, -53], [2, 1, 2], "glow"), c([3, 49, -53], [2, 1, 2], "glow"),          # brillo sobre la nariz
    c([-9, 42, -22], [18, 8, 2], "skin_hi"),                 # gola trasera
    c([-1, 49, -30], [2, 3, 3], "crest"), c([-1, 49, -26], [2, 4, 3], "crest"), c([-1, 49, -22], [2, 3, 2], "crest"),
    c([6, 41, -42], [2, 4, 10], "plate"), c([-8, 41, -42], [2, 4, 10], "plate"),    # placas de la mejilla
    c([5, 41, -52], [1, 4, 8], "bone_plate"), c([-6, 41, -52], [1, 4, 8], "bone_plate"),
    c([8, 45, -34], [2, 4, 9], "plate"), c([-10, 45, -34], [2, 4, 9], "plate"),    # cejas
    c([8, 49, -33], [2, 2, 4], "bone", rot=[-18, 0, 0], piv=[9, 49, -31]),         # picos de la ceja
    c([-10, 49, -33], [2, 2, 4], "bone", rot=[-18, 0, 0], piv=[-9, 49, -31]),
    c([-5, 36, -52], [10, 2, 17], "palate"),                 # paladar oscuro
    c([-3, 35, -48], [6, 1, 10], "flesh"),
    c([-5, 44, -57], [10, 2, 2], "slat"),                    # barra superior de los listones
]
# listones frontales (crema) con huecos que dejan ver el brillo cian
for x, h in ((-4, 10), (-1, 12), (2, 10)):
    HEAD.append(c([x, 44 - h, -57], [2, h, 1], "slat"))
# dientes blancos a lo largo de ambos lados del hocico (como el T-rex de la referencia)
for i, z in enumerate(range(-53, -34, 2)):
    h = 4 if i % 2 == 0 else 3
    xr, xl = (5, -6) if z < -42 else (6, -7)
    HEAD.append(c([xr, 38 - h, z], [1, h, 1], "tooth"))
    HEAD.append(c([xl, 38 - h, z], [1, h, 1], "tooth"))
bone("head", "neck", [0, 42, -22], HEAD)


def horn_chain(start, angles, sizes, step=4.0):
    """Cuerno curvo (media luna) hecho de segmentos rotados. Devuelve cajas para el lado +X."""
    cubes, (x, y) = [], start
    for phi, w in zip(angles, sizes):
        a = math.radians(phi)
        cx, cy = x + math.sin(a) * step / 2, y + math.cos(a) * step / 2
        cubes.append(c([cx - w / 2, cy - step / 2, -26 - w / 2], [w, int(step), w], "crystal", rot=[0, 0, -phi],
                       piv=[cx, cy, -26]))
        x, y = x + math.sin(a) * step * 0.9, y + math.cos(a) * step * 0.9
    return cubes


# cuernos curvos de cristal cian (como los de la referencia: salen de la nuca, se abren y giran hacia arriba)
EAR = horn_chain((7, 48), [8, 35, 62, 52, 20, -15], [3, 3, 3, 2, 2, 2], 4.0)
EAR += [c([9, 47, -29], [1, 5, 6], "crystal_flat"), c([12, 52, -27], [1, 3, 1], "crystal")]
bone("horn_l", "head", [7, 49, -26], EAR)
bone("horn_r", "head", [-7, 49, -26], [mirror_cube(cb) for cb in EAR])

# mandibula inferior: larga y mas angosta, con lengua brillante de escalones
bone("jaw", "head", [0, 38, -29], [
    c([-5, 34, -50], [10, 4, 21], "jaw"),
    c([-5, 38, -50], [1, 3, 20], "bone"), c([4, 38, -50], [1, 3, 20], "bone"), c([-4, 38, -50], [8, 3, 1], "bone"),
    c([-4, 31, -49], [8, 3, 10], "jaw"),
    c([-3, 29, -48], [6, 2, 7], "bone_plate"),
    c([5, 35, -49], [1, 3, 16], "bone_plate"), c([-6, 35, -49], [1, 3, 16], "bone_plate"),
    c([-3, 26, -45], [1, 3, 1], "tooth"), c([2, 26, -44], [1, 3, 1], "tooth"),
    c([-1, 28, -41], [1, 3, 1], "tooth"),
    c([-4, 41, -50], [1, 4, 1], "tooth"), c([3, 41, -50], [1, 4, 1], "tooth"),
] + [c([4, 41, z], [1, 3 if i % 2 == 0 else 2, 1], "tooth") for i, z in enumerate(range(-47, -31, 3))]
  + [c([-5, 41, z], [1, 3 if i % 2 == 0 else 2, 1], "tooth") for i, z in enumerate(range(-47, -31, 3))])
bone("tongue", "jaw", [0, 38, -41], [
    c([-3, 38, -48], [6, 2, 12], "flesh"), c([-2, 40, -43], [4, 1, 8], "flesh"), c([-1, 41, -39], [2, 1, 5], "flesh")])

# ----------------------------------------------------------------------- BRAZOS (hombro -> codo -> mano con dedos)
pair("arm", "body", [11, 38, -13], [
    c([10, 34, -15], [4, 5, 4], "limb_top"),
    c([10, 27, -14], [3, 8, 3], "limb")])
pair("forearm", "arm", [11, 27, -13], [
    c([13, 26, -13], [2, 2, 2], "bone"),
    c([10, 19, -14], [3, 8, 3], "limb")], parent_is_pair=True)
pair("claw", "forearm", [11, 19, -13], [
    c([10, 16, -16], [3, 3, 4], "limb"),
    c([13, 15, -15], [1, 3, 1], "limb"),
    c([10, 12, -17], [1, 4, 1], "limb"), c([11, 12, -17], [1, 4, 1], "limb"), c([12, 12, -17], [1, 4, 1], "limb"),
    c([10, 10, -17], [1, 2, 1], "claw"), c([11, 10, -17], [1, 2, 1], "claw"), c([12, 10, -17], [1, 2, 1], "claw")],
     parent_is_pair=True)

# ----------------------------------------------------------------------- PATAS (cadera -> rodilla -> pie -> dedos)
pair("leg", "body", [8, 30, 6], [
    c([3, 16, 0], [9, 14, 12], "limb"),
    c([2, 26, -1], [11, 6, 14], "skin_hi"),
    c([12, 18, 1], [1, 9, 9], "bone_plate"),
    c([5, 15, -5], [5, 3, 5], "bone", rot=[22, 0, 0], piv=[7, 16, -2])])
pair("shin", "leg", [8, 17, 8], [
    c([4, 4, 4], [7, 13, 8], "limb"),
    c([5, 6, 2], [5, 9, 2], "bone"),
    c([6, 4, 12], [3, 3, 3], "bone")], parent_is_pair=True)
pair("foot", "shin", [8, 5, 8], [
    c([3, 0, -3], [9, 4, 14], "limb"),
    c([4, 4, -2], [7, 1, 10], "bone_plate"),
    c([6, 1, 11], [2, 2, 3], "claw")], parent_is_pair=True)
pair("toes", "foot", [7, 2, -3], [
    c([3, 0, -8], [3, 3, 5], "limb"), c([6, 0, -8], [3, 3, 5], "limb"), c([9, 0, -8], [3, 3, 5], "limb"),
    c([3, 3, -7], [3, 1, 3], "bone"), c([6, 3, -7], [3, 1, 3], "bone"), c([9, 3, -7], [3, 1, 3], "bone"),
    c([3, 0, -12], [3, 3, 4], "claw"), c([6, 0, -12], [3, 3, 4], "claw"), c([9, 0, -12], [3, 3, 4], "claw")],
     parent_is_pair=True)


# ---------------------------------------------------------------- empaquetado UV (estantes)
def region_size(size):
    sx, sy, sz = size
    return 2 * (sx + sz), sz + sy


def pack(tex):
    placements, x, y, shelf_h = [], 0, 0, 0
    items = []
    for name, parent, pivot, cubes in BONES:
        for cb in cubes:
            items.append((name, cb))
    # ordenar por alto descendente mejora el empaquetado, pero necesitamos mantener el orden por hueso:
    order = sorted(range(len(items)), key=lambda i: -region_size(items[i][1][1])[1])
    pos = {}
    for i in order:
        w, h = region_size(items[i][1][1])
        if x + w > tex:
            x = 0
            y += shelf_h
            shelf_h = 0
        if y + h > tex:
            return None
        pos[i] = (x, y)
        x += w
        shelf_h = max(shelf_h, h)
    return [(items[i][0], items[i][1], pos[i][0], pos[i][1]) for i in range(len(items))]


TEX = 256
placements = pack(TEX)
while placements is None:
    TEX *= 2
    placements = pack(TEX)
TEX_W = TEX_H = TEX
print("Textura %dx%d, %d cajas" % (TEX, TEX, len(placements)))

bones_json, pi = [], 0
for name, parent, pivot, cubes in BONES:
    b = {"name": name, "pivot": pivot}
    if parent:
        b["parent"] = parent
    if cubes:
        b["cubes"] = []
        for o, s, kind, rot, piv in cubes:
            _, _, u, v = placements[pi]
            pi += 1
            cj = {"origin": o, "size": s, "uv": [u, v]}
            if rot is not None:
                cj["pivot"] = piv
                cj["rotation"] = rot
            b["cubes"].append(cj)
    bones_json.append(b)

geo = {"format_version": "1.12.0",
       "minecraft:geometry": [{
           "description": {"identifier": "geometry.dinowarden", "texture_width": TEX_W, "texture_height": TEX_H,
                           "visible_bounds_width": 12, "visible_bounds_height": 6, "visible_bounds_offset": [0, 1.5, 0]},
           "bones": bones_json}]}
with open(os.path.join(RES, "geo/dinowarden.geo.json"), "w") as f:
    json.dump(geo, f, indent=1)

# =====================================================================================
#  TEXTURA (+ glowmask)
# =====================================================================================
img = Image.new("RGBA", (TEX_W, TEX_H), (0, 0, 0, 0))
glow_img = Image.new("RGBA", (TEX_W, TEX_H), (0, 0, 0, 0))
px, gpx = img.load(), glow_img.load()


def clamp(v): return max(0, min(255, int(v)))
def shade(c_, f): return (clamp(c_[0] * f), clamp(c_[1] * f), clamp(c_[2] * f))
def lerp(a, b, t): return tuple(a[k] + (b[k] - a[k]) * t for k in range(3))
def ss(t): t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)


def is_glow(c_):
    return c_[1] >= 205 and c_[2] >= 195 and c_[0] <= 205 and (c_[2] - c_[0]) >= 25


def put(x, y, c_):
    c_ = tuple(clamp(v) for v in c_[:3])
    px[x, y] = c_ + (255,)
    if is_glow(c_):
        gpx[x, y] = (255, 255, 255, 255)


SKIN_PAL = [(3, 15, 20), (6, 26, 33), (10, 40, 50), (15, 58, 70), (22, 82, 94), (30, 108, 120)]
HEAD_PAL = [(10, 42, 54), (16, 62, 76), (24, 88, 102), (34, 118, 132), (52, 150, 164)]
FLESH_PAL = [(14, 90, 102), (30, 150, 160), (60, 205, 205)]
BONE = (226, 226, 210)
BONE_D = (140, 160, 158)
BONE_L = (244, 244, 232)
VEIN = (50, 215, 210)
GLOW = (60, 235, 215)
WHITE_C = (190, 255, 250)
DIM_G = (28, 140, 148)


def ramp(pal, v):
    return pal[max(0, min(len(pal) - 1, int(v * len(pal))))]


class Noise:
    def __init__(self, rng, w, h, cell):
        self.cell = cell
        gw, gh = w // cell + 3, h // cell + 3
        self.g = [[rng.random() for _ in range(gw)] for _ in range(gh)]

    def __call__(self, i, j):
        x, y = i / self.cell, j / self.cell
        x0, y0 = int(x), int(y)
        fx, fy = x - x0, y - y0
        g = self.g
        a = g[y0][x0] * (1 - fx) + g[y0][x0 + 1] * fx
        b = g[y0 + 1][x0] * (1 - fx) + g[y0 + 1][x0 + 1] * fx
        return a * (1 - fy) + b * fy


def speckle(r, c_, p=0.04, glowc=VEIN):
    p *= 0.6
    """Pixeles cian brillantes sueltos como en el sculk."""
    if r < p:
        return glowc
    if r < p * 1.9:
        return DIM_G
    return c_


FACE_LIGHT = {"up": 0.14, "down": -0.24, "north": 0.0, "south": -0.04, "east": -0.02, "west": -0.02}


def paint_face(x0, y0, w, h, kind, face, rng, size):
    n1, n2 = Noise(rng, w, h, 4), Noise(rng, w, h, 2)
    fl = FACE_LIGHT[face]
    for j in range(h):
        for i in range(w):
            r = rng.random()
            t = j / max(1, h - 1)
            edge = (i == 0 or j == 0 or i == w - 1 or j == h - 1)
            v = 0.5 * n1(i, j) + 0.3 * n2(i, j) + 0.2 * r
            if kind in ("skin", "skin_hi", "ring", "ridge", "belly"):
                off = {"skin": 0.0, "skin_hi": 0.14, "ring": 0.2, "ridge": 0.12, "belly": -0.12}[kind]
                vv = v - 0.12 + off + fl
                if face in ("north", "south", "east", "west") and kind != "ridge":
                    vv += 0.12 * t * (1 if kind != "belly" else 0.3)       # mas claro hacia abajo (como la referencia)
                c_ = ramp(SKIN_PAL, max(0.0, vv))
                if edge and face == "up" and r > 0.35: c_ = SKIN_PAL[5]
                elif edge and r > 0.65: c_ = SKIN_PAL[4]
                if kind in ("skin", "skin_hi") and face != "down" and w >= 8 and h >= 8:
                    ox_, oy_ = (w * 7 + h * 3) % 5, (w * 3 + h * 5) % 4
                    if (i + ox_ + (j // 5) * 2) % 7 == 0 or (j + oy_) % 6 == 0:
                        c_ = tuple(min(255, int(v * 1.35) + 4) for v in c_)      # juntas de placas, como bloques de piedra
                if kind == "belly" and j % 3 == 0: c_ = shade((30, 120, 130), 0.8 + 0.4 * r)
                if kind == "ring" and r > 0.9: c_ = BONE_D
                if kind == "ridge" and face == "up" and (i + j * 2) % 5 == 0: c_ = (40, 150, 160)
                c_ = speckle(r, c_, 0.018 if kind != "belly" else 0.01)
            elif kind == "ribglow":
                c_ = (70, 225, 215) if (i % 3 == 1 and r > 0.35) else ((22, 96, 106) if r > 0.4 else (8, 36, 44))
            elif kind == "limb" or kind == "limb_top":
                tt = t if face in ("north", "south", "east", "west") else 0.3
                top = (236, 240, 232)
                bot = (96, 138, 144) if kind == "limb" else (236, 240, 232)
                c_ = lerp(top, bot, tt ** 1.25)
                if kind == "limb_top": c_ = lerp(SKIN_PAL[3], (236, 240, 232), ss(t * 1.6))
                c_ = shade(c_, 0.84 + 0.2 * v + fl * 0.5)
                if i % 3 == 0: c_ = shade(c_, 0.92)
                if r > 0.968: c_ = VEIN
                elif r > 0.95: c_ = (110, 200, 200)
            elif kind == "claw":
                c_ = (10, 18, 22) if r > 0.25 else (30, 44, 50)
                if i == 0 or j == 0: c_ = (44, 62, 70)
            elif kind == "bone":
                c_ = lerp(BONE_L, BONE_D, 0.25 + 0.5 * (i / max(1, w - 1)) * 0.5 + 0.2 * r)
                if j % 4 == 3: c_ = shade(c_, 0.85)
                if edge: c_ = shade(c_, 0.9)
            elif kind == "bone_plate":
                c_ = lerp(BONE, BONE_D, 0.15 + 0.5 * r)
                if (i % 4 == 0) or (j % 5 == 0): c_ = shade(c_, 0.78)
                if r > 0.93: c_ = VEIN
            elif kind == "plate":
                c_ = lerp(BONE, (22, 56, 62), ss(t * 1.1))
                c_ = shade(c_, 0.82 + 0.3 * r)
                if i % 2 == 0: c_ = shade(c_, 0.9)
                if t > 0.6 and r > 0.93: c_ = VEIN
            elif kind == "tooth":
                c_ = BONE_L if j < h - 1 else BONE_D
                if j == 0 and h > 2: c_ = (60, 110, 110)          # encia
                if r > 0.82: c_ = shade(c_, 0.86)
                if face in ("east", "west") and i % 2 == 0: c_ = shade(c_, 0.92)
            elif kind == "glow":
                c_ = GLOW if r > 0.3 else (34, 160, 160)
                if r > 0.85: c_ = WHITE_C
            elif kind == "spinebase":
                c_ = GLOW if r > 0.55 else (30, 150, 150)
                if edge: c_ = (22, 100, 110)
                if r > 0.9: c_ = WHITE_C
            elif kind == "sprout":
                c_ = (70, 235, 220) if j < h - 1 else (22, 110, 118)
                if r > 0.7: c_ = WHITE_C
            elif kind == "orb":
                cx, cy = (w - 1) / 2, (h - 1) / 2
                d = max(abs(i - cx) / max(0.5, cx + 0.5), abs(j - cy) / max(0.5, cy + 0.5))
                c_ = lerp(WHITE_C, (40, 190, 190), d ** 1.5)
                if r > 0.9: c_ = (150, 255, 245)
            elif kind in ("crystal", "crystal_flat"):
                tt = 1 - t
                c_ = lerp((24, 116, 128), (150, 255, 245), tt ** 1.2)
                c_ = shade(c_, 0.85 + 0.25 * r + fl * 0.4)
                if r > 0.88: c_ = (200, 255, 252)
                if (i + j) % 3 == 0: c_ = shade(c_, 0.88)
            elif kind == "crest":
                c_ = lerp((30, 130, 140), BONE_L, ss(t * 1.4))
                c_ = shade(c_, 0.85 + 0.25 * r)
                if r > 0.9: c_ = VEIN
            elif kind == "snout_top":
                vv = v + 0.1 + fl
                c_ = ramp(HEAD_PAL, vv)
                if (j % 3 == 1 and face == "up"): c_ = (40, 150, 160)       # cresta nasal estriada
                if edge and r > 0.4: c_ = HEAD_PAL[4]
                c_ = speckle(r, c_, 0.05)
            elif kind in ("cranium", "snout"):
                vv = v + fl + (0.1 if kind == "cranium" else 0.0)
                c_ = ramp(HEAD_PAL, vv)
                if face == "up":
                    c_ = ramp(HEAD_PAL, vv + 0.08)
                if face == "down" and kind == "snout":
                    c_ = ramp(FLESH_PAL, v)
                    if j % 3 == 0: c_ = (70, 225, 215)
                if edge and r > 0.4: c_ = HEAD_PAL[4]
                if kind == "snout" and face in ("east", "west") and 0.25 < t < 0.55 and size[2] >= 14:
                    c_ = lerp(c_, BONE, 0.55 * ss((t - 0.2) * 4) * (1 - ss((t - 0.5) * 5)))   # franja de hueso lateral
                c_ = speckle(r, c_, 0.06)
            elif kind == "jaw":
                if face == "up":
                    c_ = ramp(FLESH_PAL, v)
                    if j % 3 == 0: c_ = (70, 225, 215)
                else:
                    c_ = ramp(HEAD_PAL, v + fl)
                    if edge and r > 0.5: c_ = HEAD_PAL[4]
                    c_ = speckle(r, c_, 0.04)
            elif kind == "slat":
                c_ = lerp((244, 236, 208), (212, 190, 150), ss(t * 1.1))
                c_ = shade(c_, 0.88 + 0.2 * r)
                if i % 2 == 0: c_ = shade(c_, 0.93)
                if j == 0 and h > 3: c_ = (40, 120, 130)
                if t > 0.9: c_ = (150, 124, 92)
            elif kind == "palate":
                c_ = (6, 40, 52) if r > 0.3 else (12, 70, 84)
                if face == "down":
                    c_ = (70, 225, 215) if j % 2 == 0 else (24, 130, 140)
                    if r > 0.85: c_ = WHITE_C
            elif kind == "glowwall":
                c_ = lerp((40, 190, 190), (90, 240, 232), r)
                if face in ("north", "east", "west") and j % 4 == 0: c_ = (14, 70, 82)
                if r > 0.9: c_ = WHITE_C
            elif kind == "nostril":
                c_ = (2, 8, 10) if r > 0.3 else (10, 40, 50)
                if r > 0.9: c_ = VEIN
            elif kind == "mouth":
                c_ = (6, 16, 24) if r > 0.2 else (14, 30, 42)
                if face == "down" and j % 3 == 0: c_ = (40, 150, 160)
                if r > 0.96: c_ = VEIN
            elif kind == "flesh":
                c_ = ramp(FLESH_PAL, v)
                if j % 3 == 0: c_ = (80, 235, 225)
                if r > 0.95: c_ = WHITE_C
                if face in ("down",): c_ = shade(c_, 0.6)
            else:
                c_ = SKIN_PAL[2]
            put(x0 + i, y0 + j, c_)


rng = random.Random(7)
for name, (o, s, kind, rot, piv), u, v in placements:
    sx, sy, sz = s
    faces = {"up": (u + sz, v, sx, sz), "down": (u + sz + sx, v, sx, sz),
             "east": (u, v + sz, sz, sy), "north": (u + sz, v + sz, sx, sy),
             "west": (u + sz + sx, v + sz, sz, sy), "south": (u + 2 * sz + sx, v + sz, sx, sy)}
    for fname, (fx, fy, fw, fh) in faces.items():
        paint_face(fx, fy, fw, fh, kind, fname, rng, s)
    if name == "head" and kind == "cranium":
        # ojos: ranura oscura con pupila cian brillante, a ambos lados del craneo
        for side in ("east", "west"):
            fx, fy, fw, fh = faces[side]
            for j in range(4, 8):
                for i in range(1, 6):
                    ii = fw - 1 - i if side == "east" else i
                    put(fx + ii, fy + j, (2, 8, 10))
            for i in (2, 3, 4):
                ii = fw - 1 - i if side == "east" else i
                put(fx + ii, fy + 5, (90, 240, 230))
                put(fx + ii, fy + 6, (40, 190, 190))
            ii = fw - 3 if side == "east" else 2
            put(fx + ii, fy + 5, (230, 255, 252))
    if name == "head" and kind == "snout" and s == [12, 9, 10]:
        for side in ("east", "west"):                  # fosas / poros brillantes en el hocico
            fx, fy, fw, fh = faces[side]
            for (ii, jj) in ((3, 2), (6, 1), (9, 2), (12, 1)):
                put(fx + ii, fy + jj, (150, 250, 240))

img.save(os.path.join(RES, "textures/entity/dinowarden.png"))
glow_img.save(os.path.join(RES, "textures/entity/dinowarden_glowmask.png"))

# =====================================================================================
#  ANIMACIONES
# =====================================================================================
S = lambda p: math.sin(p * 2 * math.pi)
C = lambda p: math.cos(p * 2 * math.pi)


def r3(v): return round(v, 3)


def kf(d): return {str(k): [r3(x) for x in v] for k, v in sorted(d.items())}


def cyc(length, steps, fn):
    return {round(length * s / steps, 3): fn(s / steps) for s in range(steps + 1)}


class Anim:
    def __init__(self, length, loop=True):
        self.length, self.loop, self.bones, self.sounds = length, loop, {}, {}

    def chan(self, bone_, channel, keys):
        self.bones.setdefault(bone_, {})[channel] = kf(keys)

    def rot(self, bone_, fn, n=24):
        self.chan(bone_, "rotation", cyc(self.length, n, fn))

    def pos(self, bone_, fn, n=24):
        self.chan(bone_, "position", cyc(self.length, n, fn))

    def scl(self, bone_, fn, n=24):
        self.chan(bone_, "scale", cyc(self.length, n, fn))

    def sound(self, t, effect):
        self.sounds[str(r3(t))] = {"effect": effect}

    def json(self):
        d = {"loop": self.loop if self.loop is True else self.loop, "animation_length": self.length, "bones": self.bones}
        if self.sounds:
            d["sound_effects"] = dict(sorted(self.sounds.items(), key=lambda kv: float(kv[0])))
        return d


anims = {}
GROW = (1.0, 1.25, 1.6, 2.0, 2.5)


def tail(a, ay, ax=0.0, cycles=1, lag=0.09, base1=0.0, n=24, phase=0.0, rest=None):
    """Onda viajera en la cola: cada segmento va un poco atrasado y se mueve mas hacia la punta."""
    for k, g in enumerate(GROW):
        a.rot("tail%d" % (k + 1), lambda p, k=k, g=g: [
            (base1 if k == 0 else 0.0) + ax * g * S(cycles * p - lag * k + 0.25 + phase),
            ay * g * S(cycles * p - lag * k + phase), 0], n)


def spines_wave(a, amp, cycles=2, n=24):
    for k, nm in enumerate(("spines_a", "spines_b", "spines_c")):
        a.rot(nm, lambda p, k=k: [amp * S(cycles * p - 0.12 * k), 0, 0.4 * amp * S(p - 0.1 * k)], n)
    a.rot("sprouts", lambda p: [amp * 1.4 * S(cycles * p + 0.2), 0, amp * 1.6 * S(p)], n)


def orbs(a, amp=1.0, n=12):
    a.pos("orb_l", lambda p: [0, amp * S(p), 0], n)
    a.pos("orb_r", lambda p: [0, amp * S(p + .5), 0], n)


# ------------------------------------------------------------------------ IDLE (6 s): respira, olfatea, desplaza el peso
L = 6.0
a = Anim(L)
a.pos("body", lambda p: [0.5 * S(p), 0.35 * S(2 * p), 0], 24)
a.rot("body", lambda p: [0.6 * S(2 * p + 0.2), 0.8 * S(p), 0.9 * S(p + 0.25)], 24)
a.scl("body", lambda p: [1, 1 + 0.014 * S(2 * p), 1 + 0.006 * S(2 * p)], 24)
a.rot("neck", lambda p: [2 * S(2 * p + 0.1) - 1.5, 7 * S(p), 1.5 * S(p + 0.3)], 24)
a.rot("head", lambda p: [-2 * S(2 * p + 0.2) + 2.5 * max(0.0, S(3 * p)) ** 2, 8 * S(p + 0.12), 0], 24)
a.rot("jaw", lambda p: [2 + 2 * S(2 * p + 0.3) + 4 * max(0.0, S(3 * p)) ** 2, 0, 0], 24)
a.rot("tongue", lambda p: [3 * S(2 * p), 0, 0], 12)
for sd, ph in (("l", 0.0), ("r", 0.5)):
    a.rot("horn_" + sd, lambda p, ph=ph: [3 * S(p * 2 + 0.3 + ph), 0, (-1 if sd == "l" else 1) * (6 * S(p * 2 + ph) + 2)], 24)
    a.rot("arm_" + sd, lambda p, ph=ph: [-6 + 3 * S(2 * p + ph), 0, (-1 if sd == "l" else 1) * 2], 24)
    a.rot("forearm_" + sd, lambda p, ph=ph: [-24 + 5 * S(2 * p + ph + 0.2), 0, 0], 24)
    a.rot("claw_" + sd, lambda p, ph=ph: [10 + 8 * S(2 * p + ph + 0.4), 0, 0], 24)
    a.rot("leg_" + sd, lambda p, ph=ph: [(1.6 if sd == "l" else -1.6) * S(p + 0.25), 0, 0], 24)
    a.rot("shin_" + sd, lambda p, ph=ph: [4 + (1.5 if sd == "l" else -1.5) * S(p + 0.25), 0, 0], 24)
    a.rot("foot_" + sd, lambda p, ph=ph: [-4 - (1.6 if sd == "l" else -1.6) * S(p + 0.25), 0, 0], 24)
tail(a, 6, 2.5, cycles=1, lag=0.07, n=24)
spines_wave(a, 2.0, cycles=2)
orbs(a, 0.9)
anims["animation.dinowarden.idle"] = a


# ------------------------------------------------------------------------ CAMINAR / CORRER (ciclo de pasos completo)
def gait(L, A, K, st, bob, roll, sway, twist, lean, tail_amp, arm_amp, head_bob, jaw_open, strike=0.1, run=False, n=24):
    a = Anim(L)
    ssf = lambda u: ss(u)

    def theta(u):                                   # muslo: negativo = adelante
        if u < st:
            return -A + 2 * A * (u / st)
        s_ = (u - st) / (1 - st)
        return A - 2 * A * ssf(s_)

    def knee(u):
        if u < st:
            return 6 + 7 * math.sin(math.pi * u / st)
        s_ = (u - st) / (1 - st)
        return 6 + K * math.sin(math.pi * s_ ** 0.85)

    def foot_extra(u):
        if u < st:
            a_ = -12 * (1 - ssf(u / 0.15))
            b_ = 26 * ssf((u - 0.78 * st) / (0.22 * st))
            return a_ + b_
        s_ = (u - st) / (1 - st)
        return 26 * (1 - ssf(s_ / 0.4)) - 12 * ssf((s_ - 0.65) / 0.35)

    def lock(u):
        if u < st: return 1.0
        s_ = (u - st) / (1 - st)
        return 1 - 0.55 * math.sin(math.pi * s_)

    for sd, ph in (("l", 0.0), ("r", 0.5)):
        U = lambda p, ph=ph: (p - strike - ph) % 1.0
        a.rot("leg_" + sd, lambda p, U=U: [theta(U(p)), 0, 0], n)
        a.rot("shin_" + sd, lambda p, U=U: [knee(U(p)), 0, 0], n)
        a.rot("foot_" + sd, lambda p, U=U: [-(theta(U(p)) + knee(U(p))) * lock(U(p)) + foot_extra(U(p)), 0, 0], n)
        a.rot("toes_" + sd, lambda p, U=U: [foot_extra(U(p)) * 0.7 + (16 * math.sin(math.pi * (U(p) - st) / (1 - st)) if U(p) > st else 0), 0, 0], n)
        sgn = 1 if sd == "l" else -1
        a.rot("arm_" + sd, lambda p, sgn=sgn: [-14 - lean + arm_amp * C(p - strike) * sgn, 0, sgn * 3], n)
        a.rot("forearm_" + sd, lambda p, sgn=sgn: [-34 + 12 * C(p - strike + 0.1) * sgn, 0, 0], n)
        a.rot("claw_" + sd, lambda p, sgn=sgn: [12 + 10 * S(p - strike + 0.1) * sgn, 0, 0], n)
    q = lambda p: p - strike
    a.pos("body", lambda p: [sway * C(q(p) - 0.25), -0.5 * bob * C(2 * q(p)), 0], n)
    a.rot("body", lambda p: [lean + 1.0 * S(2 * q(p) + 0.25), twist * S(q(p)), roll * C(q(p) - 0.25)], n)
    a.rot("neck", lambda p: [-head_bob * C(2 * q(p)) - lean * 0.6, -twist * 1.6 * S(q(p)), 0], n)
    a.rot("head", lambda p: [head_bob * 0.8 * C(2 * q(p) + 0.1) - lean * 0.4, -twist * 0.6 * S(q(p)), 0], n)
    a.rot("jaw", lambda p: [jaw_open + 3 * C(2 * q(p) + 0.2), 0, 0], n)
    a.rot("tongue", lambda p: [4 * C(2 * q(p)), 0, 0], 12)
    for sd, sg in (("l", 1), ("r", -1)):
        a.rot("horn_" + sd, lambda p, sg=sg: [4 * C(2 * q(p) + 0.3), 0, -sg * (5 + 3 * C(2 * q(p)))], n)
    tail(a, tail_amp, tail_amp * 0.3, cycles=1, lag=0.1, base1=-lean * 0.8, n=n, phase=-0.1)
    spines_wave(a, 3.0 if not run else 4.5, cycles=2, n=n)
    orbs(a, 1.2)
    a.sound(L * (strike + 0.01), "step_l")
    a.sound(L * (strike + 0.01 + 0.5), "step_r")
    return a


anims["animation.dinowarden.walk"] = gait(1.1, 27, 46, 0.56, 1.6, 2.0, 0.9, 3.0, 2, 11, 9, 2.4, 5)
anims["animation.dinowarden.run"] = gait(0.66, 40, 62, 0.42, 3.2, 3.0, 1.2, 4.5, 8, 9, 12, 4.5, 14, run=True)
# la carrera usa "run_l/run_r" como efectos para dar mas temblor
anims["animation.dinowarden.run"].sounds = {k: {"effect": v["effect"].replace("step", "run")}
                                            for k, v in anims["animation.dinowarden.run"].sounds.items()}

# ------------------------------------------------------------------------ SWIM (patalea, cabeza arriba, cola ondulando)
L = 1.6
a = Anim(L)
a.pos("body", lambda p: [0, -4 + 1.2 * S(p), 0])
a.rot("body", lambda p: [-4 + 2 * S(p + .25), 0, 2 * S(p)])
a.rot("neck", lambda p: [-18 + 2 * S(2 * p), 4 * S(p), 0])
a.rot("head", lambda p: [-8, 0, 0])
a.rot("jaw", lambda p: [4 + 2 * S(2 * p), 0, 0])
for sd, ph, sg in (("l", 0.0, 1), ("r", 0.5, -1)):
    a.rot("leg_" + sd, lambda p, ph=ph, sg=sg: [-38 * S(p + ph), 0, -8 * sg])
    a.rot("shin_" + sd, lambda p, ph=ph: [28 + 22 * S(p + ph + .25), 0, 0])
    a.rot("foot_" + sd, lambda p, ph=ph: [-10 + 20 * S(p + ph + .5), 0, 0])
    a.rot("toes_" + sd, lambda p, ph=ph: [14 + 12 * S(p + ph + .75), 0, 0])
    a.rot("arm_" + sd, lambda p, ph=ph, sg=sg: [-40 + 14 * S(p + ph), 0, 10 * sg])
    a.rot("forearm_" + sd, lambda p, ph=ph: [-20 + 10 * S(p + ph + .25), 0, 0])
    a.rot("claw_" + sd, lambda p, ph=ph: [14 + 10 * S(p + ph + .5), 0, 0])
tail(a, 16, 4, cycles=1, lag=0.12, base1=-6)
spines_wave(a, 3, cycles=2)
orbs(a, 1.5)
anims["animation.dinowarden.swim"] = a

# ------------------------------------------------------------------------ BITE (0.9 s). Dano en el tick 8 (0.4 s)
a = Anim(0.9, loop="hold_on_last_frame")
a.chan("body", "position", {0: [0, 0, 0], 0.25: [0, 0, 3], 0.4: [0, -1, -8], 0.6: [0, 0, -4], 0.9: [0, 0, 0]})
a.chan("body", "rotation", {0: [0, 0, 0], 0.25: [-6, 0, 0], 0.4: [10, 0, 0], 0.9: [0, 0, 0]})
a.chan("neck", "rotation", {0: [0, 0, 0], 0.25: [-22, 0, 0], 0.4: [28, 0, 0], 0.6: [14, 0, 0], 0.9: [0, 0, 0]})
a.chan("head", "rotation", {0: [0, 0, 0], 0.25: [-14, 0, 0], 0.4: [14, 0, 0], 0.9: [0, 0, 0]})
a.chan("jaw", "rotation", {0: [2, 0, 0], 0.25: [46, 0, 0], 0.38: [50, 0, 0], 0.46: [0, 0, 0], 0.9: [2, 0, 0]})
# zancada de ataque: la pata izquierda se adelanta y pisa en el instante de la mordida, la derecha empuja
a.chan("leg_l", "rotation", {0: [0, 0, 0], 0.15: [14, 0, 0], 0.3: [-34, 0, 0], 0.4: [-24, 0, 0], 0.9: [0, 0, 0]})
a.chan("shin_l", "rotation", {0: [4, 0, 0], 0.15: [10, 0, 0], 0.3: [36, 0, 0], 0.4: [10, 0, 0], 0.9: [4, 0, 0]})
a.chan("foot_l", "rotation", {0: [-4, 0, 0], 0.3: [-10, 0, 0], 0.4: [14, 0, 0], 0.9: [-4, 0, 0]})
a.chan("leg_r", "rotation", {0: [0, 0, 0], 0.3: [14, 0, 0], 0.5: [22, 0, 0], 0.9: [0, 0, 0]})
a.chan("shin_r", "rotation", {0: [4, 0, 0], 0.3: [14, 0, 0], 0.5: [10, 0, 0], 0.9: [4, 0, 0]})
a.chan("toes_r", "rotation", {0: [0, 0, 0], 0.4: [28, 0, 0], 0.9: [0, 0, 0]})
for sd, sg in (("l", 1), ("r", -1)):
    a.chan("arm_" + sd, "rotation", {0: [-6, 0, 0], 0.4: [-48, 0, 12 * sg], 0.9: [-6, 0, 0]})
    a.chan("forearm_" + sd, "rotation", {0: [-24, 0, 0], 0.4: [-50, 0, 0], 0.9: [-24, 0, 0]})
    a.chan("claw_" + sd, "rotation", {0: [10, 0, 0], 0.4: [-10, 0, 0], 0.9: [10, 0, 0]})
a.chan("tail1", "rotation", {0: [0, 0, 0], 0.4: [-12, 0, 0], 0.9: [0, 0, 0]})
for k, ang in zip((2, 3, 4, 5), (14, 22, 32, 42)):
    a.chan("tail%d" % k, "rotation", {0: [0, 0, 0], 0.4: [0, ang, 0], 0.9: [0, 0, 0]})
a.sound(0.4, "slam")
anims["animation.dinowarden.bite"] = a

# ------------------------------------------------------------------------ ROAR (3.5 s). Sonic boom en el tick 38 (1.9 s)
random.seed(11)


def jitter(t0, t1, step, amp):
    out, t = {}, t0
    while t <= t1 + 1e-6:
        out[round(t, 3)] = [random.uniform(-amp, amp) for _ in range(3)]
        t += step
    return out


def lash(t0, t1, step, amp):
    out, t, i = {}, t0, 0
    while t <= t1 + 1e-6:
        out[round(t, 3)] = [0, amp * (1 if i % 2 == 0 else -1), 0]
        t += step
        i += 1
    return out


a = Anim(3.5, loop="hold_on_last_frame")
head_rot = {0: [0, 0, 0], 0.5: [-20, 0, 0], 0.8: [-34, 0, 0]}
head_rot.update({k: [v[0] - 34, v[1], v[2]] for k, v in jitter(0.9, 2.6, 0.1, 2.2).items()})
head_rot.update({3.0: [-10, 0, 0], 3.5: [0, 0, 0]})
body_pos = {0: [0, 0, 0], 0.35: [0, -1.5, 1], 0.62: [0, -2.5, 3]}
body_pos.update({k: [v[0] * 0.15, v[1] * 0.15 + 0.5, 2] for k, v in jitter(0.9, 2.6, 0.1, 2.0).items()})
body_pos.update({3.0: [0, 0, 1], 3.5: [0, 0, 0]})
a.chan("body", "position", body_pos)
a.chan("body", "rotation", {0: [0, 0, 0], 0.35: [2, 0, 3], 0.62: [-3, 0, -3], 0.8: [-10, 0, 0], 2.6: [-10, 0, 0], 3.5: [0, 0, 0]})
a.chan("body", "scale", {0: [1, 1, 1], 0.7: [1.05, 1.07, 1.05], 2.6: [1.05, 1.07, 1.05], 3.5: [1, 1, 1]})
a.chan("neck", "rotation", {0: [0, 0, 0], 0.6: [-26, 0, 0], 2.6: [-26, 0, 0], 3.5: [0, 0, 0]})
a.chan("head", "rotation", head_rot)
a.chan("jaw", "rotation", {0: [2, 0, 0], 0.5: [10, 0, 0], 0.9: [52, 0, 0], 1.9: [56, 0, 0], 2.6: [52, 0, 0], 3.0: [10, 0, 0], 3.5: [2, 0, 0]})
a.chan("tongue", "rotation", {0: [0, 0, 0], 0.9: [10, 0, 0], 1.9: [14, 0, 0], 3.0: [0, 0, 0]})
a.chan("tail1", "rotation", {0: [0, 0, 0], 0.7: [-14, 0, 0], 2.6: [-14, 0, 0], 3.5: [0, 0, 0]})
a.chan("tail2", "rotation", {0: [0, 0, 0], 0.7: [-8, 0, 0], 2.6: [-8, 0, 0], 3.5: [0, 0, 0]})
for k, amp in ((3, 12), (4, 18), (5, 26)):
    a.chan("tail%d" % k, "rotation", {0: [0, 0, 0], **lash(0.7, 2.6, 0.19, amp), 3.5: [0, 0, 0]})
for sd, sg in (("l", 1), ("r", -1)):
    a.chan("arm_" + sd, "rotation", {0: [-6, 0, 0], 0.7: [-52, 0, 25 * sg], 2.6: [-52, 0, 25 * sg], 3.5: [-6, 0, 0]})
    a.chan("forearm_" + sd, "rotation", {0: [-24, 0, 0], 0.7: [-30, 0, 0], 1.9: [-44, 0, 0], 2.6: [-30, 0, 0], 3.5: [-24, 0, 0]})
    a.chan("claw_" + sd, "rotation", {0: [10, 0, 0], 0.7: [-18, 0, 0], 2.6: [-18, 0, 0], 3.5: [10, 0, 0]})
# pisoton izquierdo (0.35 s) y derecho, mas fuerte (0.62 s), luego patas bien plantadas
a.chan("leg_l", "rotation", {0: [0, 0, 0], 0.08: [8, 0, 0], 0.26: [-38, 0, 0], 0.35: [-10, 0, 0], 0.7: [-8, 0, 0], 2.6: [-8, 0, 0], 3.5: [0, 0, 0]})
a.chan("shin_l", "rotation", {0: [4, 0, 0], 0.26: [48, 0, 0], 0.35: [10, 0, 0], 3.5: [4, 0, 0]})
a.chan("foot_l", "rotation", {0: [-4, 0, 0], 0.26: [-30, 0, 0], 0.35: [4, 0, 0], 3.5: [-4, 0, 0]})
a.chan("toes_l", "rotation", {0: [0, 0, 0], 0.26: [34, 0, 0], 0.35: [-8, 0, 0], 0.5: [0, 0, 0]})
a.chan("leg_r", "rotation", {0: [0, 0, 0], 0.3: [8, 0, 0], 0.5: [-46, 0, 0], 0.62: [-8, 0, 0], 0.7: [8, 0, 0], 2.6: [8, 0, 0], 3.5: [0, 0, 0]})
a.chan("shin_r", "rotation", {0: [4, 0, 0], 0.5: [58, 0, 0], 0.62: [8, 0, 0], 3.5: [4, 0, 0]})
a.chan("foot_r", "rotation", {0: [-4, 0, 0], 0.5: [-36, 0, 0], 0.62: [6, 0, 0], 3.5: [-4, 0, 0]})
a.chan("toes_r", "rotation", {0: [0, 0, 0], 0.5: [38, 0, 0], 0.62: [-10, 0, 0], 0.8: [0, 0, 0]})
a.sound(0.36, "stomp_l")
a.sound(0.63, "stomp_r")
anims["animation.dinowarden.roar"] = a

# ------------------------------------------------------------------------ BELLOW (bramido en el agua, 3 s)
random.seed(5)
vib, t = {}, 0.5
while t <= 2.5 + 1e-6:
    vib[round(t, 3)] = [0, random.choice([-0.7, 0.7]) - 4, 0]
    t += 0.05
vib[0] = [0, -4, 0]
vib[3.0] = [0, -4, 0]
a = Anim(3.0, loop="hold_on_last_frame")
a.chan("body", "position", vib)
a.chan("body", "rotation", {0: [-4, 0, 0], 0.5: [-12, 0, 0], 2.5: [-12, 0, 0], 3.0: [-4, 0, 0]})
a.chan("neck", "rotation", {0: [-18, 0, 0], 0.5: [-30, 0, 0], 2.5: [-30, 0, 0], 3.0: [-18, 0, 0]})
a.chan("neck", "scale", {0: [1, 1, 1], 0.5: [1.18, 1.18, 1.1], 1.5: [1.25, 1.25, 1.12], 2.5: [1.18, 1.18, 1.1], 3.0: [1, 1, 1]})
a.chan("head", "rotation", {0: [-8, 0, 0], 0.5: [-24, 0, 0], 2.5: [-24, 0, 0], 3.0: [-8, 0, 0]})
a.chan("jaw", "rotation", {0: [4, 0, 0], 0.5: [16, 0, 0], 1.5: [20, 0, 0], 2.5: [16, 0, 0], 3.0: [4, 0, 0]})
a.chan("tail1", "rotation", {0: [-6, 0, 0], 0.5: [-14, 0, 0], 2.5: [-14, 0, 0], 3.0: [-6, 0, 0]})
a.rot("leg_l", lambda p: [-12 * S(p * 3), 0, -8], 12)
a.rot("leg_r", lambda p: [-12 * S(p * 3 + .5), 0, 8], 12)
a.rot("shin_l", lambda p: [26 + 8 * S(p * 3 + .25), 0, 0], 12)
a.rot("shin_r", lambda p: [26 + 8 * S(p * 3 + .75), 0, 0], 12)
tail(a, 9, 2, cycles=3, lag=0.1, n=24)
a.bones["tail1"]["rotation"] = kf({0: [-6, 0, 0], 0.5: [-14, 0, 0], 2.5: [-14, 0, 0], 3.0: [-6, 0, 0]})   # el tail1 conserva su pose
anims["animation.dinowarden.bellow"] = a

with open(os.path.join(RES, "animations/dinowarden.animation.json"), "w") as f:
    json.dump({"format_version": "1.8.0", "animations": {k: v.json() for k, v in anims.items()}}, f, indent=1)

print("OK: geo, textura, glowmask y animaciones generados en", RES)
