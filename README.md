# Dino Warden (Forge 1.20.1 + GeckoLib 4.4.9)

## Compilar
1. Copia `src/`, `build.gradle`, `settings.gradle`, `gradle.properties` dentro de un MDK de Forge 1.20.1 (47.3.0)
   (necesitas su `gradlew`, `gradle/wrapper`). Java 17.
2. `./gradlew build`  ->  `build/libs/dinowarden-1.0.0.jar`
3. En el juego instala tambien GeckoLib 1.20.1 (4.4.9 o compatible).

## Probar
- Huevo generador: pestana "Spawn Eggs".
- Natural: ve a una Deep Dark, haz sonar un Sculk Shrieker, espera a que termine (~4 s) y hazlo sonar OTRA VEZ
  en menos de 60 s -> aparece el Dino Warden. En `logs/latest.log` veras "[DinoWarden] Grito #1/#2".

## Lo que es PLACEHOLDER (reemplazar)
- `assets/dinowarden/geo/dinowarden.geo.json`, `textures/entity/dinowarden.png`,
  `animations/dinowarden.animation.json`: generados por `tools/generate_assets.py`. Abre el geo y la
  animacion en Blockbench (plugin GeckoLib) para igualarlos al video: conserva los nombres de huesos.
- `assets/dinowarden/sounds/*.ogg`: ruido sintetico. Pon tus audios .ogg (mono) con el mismo nombre:
  roar, bellow, step, hurt, death, ambient, bite.

## Ajustes rapidos
- Hitbox: `ModEntities` -> `.sized(2.4F, 3.3F)`; altura de ojos en `DinoWardenEntity#getStandingEyeHeight`.
- Duracion rugido/boom/mordida/bramido: constantes `*_TICKS` en `DinoWardenEntity` (deben coincidir con
  `animation_length * 20` del JSON).
- Temblor de camara: `STRENGTH` y `RANGE` en `CameraShakeHandler`.
- Vida/dano/velocidad: `DinoWardenEntity#createAttributes`.
- Ventana de los 2 gritos: `ShriekerHandler.WINDOW_TICKS`.

## Hitbox por piezas, nado y sentidos (v1.1)
- **Hitbox**: cuerpo 1.9 x 3.1 + 5 piezas (`DinoPart`): cabeza, cuello y 3 tramos de cola. Cualquier golpe, flecha o
  ataque a una pieza hiere al Dino Warden. Las posiciones/medidas estan en `DinoWardenEntity#updateParts` y en el
  constructor; el dibujo amarillo de `preview/modelo_preview.png` muestra las cajas (F3+B en el juego las muestra).
- **Nado**: con el agua cubriendole mas de ~1.2 bloques nada en 3D (`isSwimmingMode`), sigue al objetivo y reproduce
  `swim`. En aguas poco profundas camina.
- **Sentidos** (como el Warden):
  - Olfato: jugadores a menos de `SMELL_RANGE` (12 bloques) aunque no los vea, tambien si van agachados.
  - Oido: `SoundSenseHandler` (pasos 20 bloques, bloques/saltos 24, golpes/explosiones/proyectiles 32). Agachado no
    hace ruido de pasos. Si el ruido no es de un jugador, va a investigar el lugar.
  - Contacto: tocar cualquier pieza (con `TOUCH_MARGIN` 0.8) lo alerta al instante.
- **Cola**: 5 segmentos con onda viajera en idle / caminar / correr / nadar, y latigazo al rugir y morder.
- Regenerar modelo/textura/animaciones: `python3 tools/generate_assets.py`; previews: `python3 tools/render_preview.py`.

## v1.2: modelo detallado, brillo, patas y temblor por pisada
- Modelo ~250 cajas (costillas, espinas, dedos con garras, colmillos, cristales, anillos de cola). Regenera con `tools/generate_assets.py`.
- `textures/entity/dinowarden_glowmask.png`: los pixeles cian brillan en la oscuridad (`AutoGlowingGeoLayer`).
- Caminar/correr: ciclo completo (muslo, rodilla, pie, dedos), balanceo de cuerpo, cola, brazos y espinas.
- Cada pisada (keyframes `sound_effects` de la animacion: step/run/stomp/slam) dispara sonido, polvo y temblor de camara
  (`client/StepShake`). Ajusta `STRENGTH` y `RANGE` en `StepShake`. El rugido tiene 2 pisotones fuertes.
- Previews: `python3 tools/render_preview.py` (incluye ciclo_pasos_preview.png y cueva_preview.png).
