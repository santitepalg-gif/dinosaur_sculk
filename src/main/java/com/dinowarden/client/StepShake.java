package com.dinowarden.client;

import com.dinowarden.entity.DinoWardenEntity;
import com.dinowarden.registry.ModSounds;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.BlockParticleOption;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;

/**
 * Pisadas del Dino Warden (solo cliente). Las llama la animacion de GeckoLib (sound_effects del JSON:
 * step_l/step_r, run_l/run_r, stomp_l/stomp_r, slam) justo cuando la pata toca el suelo:
 * sonido + polvo + impulso de temblor de camara que CameraShakeHandler aplica y amortigua.
 */
public final class StepShake {
    /** Multiplicador general del temblor por pisada (0 = sin temblor). */
    public static final float STRENGTH = 1.0F;
    /** Distancia maxima (bloques) a la que se siente. */
    public static final double RANGE = 40.0D;

    private static final class Impulse {
        final long startNanos = System.nanoTime();
        final float power;     // grados de cabeceo en el pico
        final float rollSign;
        Impulse(float power, float rollSign) { this.power = power; this.rollSign = rollSign; }
    }

    private static final List<Impulse> IMPULSES = new ArrayList<>();
    private static final double LIFE = 0.9D;   // segundos

    private StepShake() {}

    /** @param key nombre del keyframe de sonido de la animacion */
    public static void onKeyframe(DinoWardenEntity dino, String key) {
        Minecraft mc = Minecraft.getInstance();
        ClientLevel level = mc.level;
        if (level == null || mc.player == null) return;

        boolean left = key.endsWith("_l");
        float power;       // 1 = pisada normal
        float volume;
        float pitch;
        switch (key.split("_")[0]) {
            case "run" -> { power = 1.7F; volume = 3.2F; pitch = 0.85F; }
            case "stomp" -> { power = 2.6F; volume = 4.0F; pitch = 0.7F; }
            case "slam" -> { power = 1.4F; volume = 0.0F; pitch = 1.0F; }
            default -> { power = 1.0F; volume = 2.6F; pitch = 0.95F; }
        }

        // posicion del pie (el modelo +X es el costado "l"; lado derecho de la entidad)
        double yaw = Math.toRadians(dino.yBodyRot);
        double fx = -Math.sin(yaw), fz = Math.cos(yaw);          // adelante
        double rx = -Math.cos(yaw), rz = -Math.sin(yaw);         // derecha
        double side = key.equals("slam") ? 0.0D : (left ? 0.55D : -0.55D);
        double fwd = key.equals("slam") ? 1.6D : 0.1D;
        double x = dino.getX() + rx * side + fx * fwd;
        double z = dino.getZ() + rz * side + fz * fwd;
        double y = dino.getY();

        if (volume > 0.0F) {
            level.playLocalSound(x, y, z, ModSounds.STEP.get(), SoundSource.HOSTILE, volume,
                    pitch + (level.random.nextFloat() - 0.5F) * 0.12F, false);
        }

        // polvo / fragmentos del bloque bajo la pata
        BlockPos below = BlockPos.containing(x, y - 0.2D, z);
        BlockState state = level.getBlockState(below);
        if (!state.isAir()) {
            int n = (int) (6 + 6 * power);
            for (int i = 0; i < n; i++) {
                double a = level.random.nextDouble() * Math.PI * 2.0D;
                double r = 0.2D + level.random.nextDouble() * 0.5D * power;
                level.addParticle(new BlockParticleOption(ParticleTypes.BLOCK, state),
                        x + Math.cos(a) * r, y + 0.1D, z + Math.sin(a) * r,
                        Math.cos(a) * 0.08D * power, 0.12D + level.random.nextDouble() * 0.1D, Math.sin(a) * 0.08D * power);
            }
        }

        // temblor de camara segun la distancia al jugador
        double dist = mc.player.position().distanceTo(new Vec3(x, y, z));
        if (dist >= RANGE) return;
        double f = 1.0D - dist / RANGE;
        float p = (float) (power * f * f * 6.0D * STRENGTH);
        if (p < 0.05F) return;
        synchronized (IMPULSES) {
            IMPULSES.add(new Impulse(p, left ? 1.0F : -1.0F));
            if (IMPULSES.size() > 24) IMPULSES.remove(0);
        }
    }

    /** Devuelve {pitch, roll, yaw} en grados con todos los impulsos activos sumados. */
    public static float[] sample() {
        float pitch = 0.0F, roll = 0.0F, yaw = 0.0F;
        long now = System.nanoTime();
        synchronized (IMPULSES) {
            IMPULSES.removeIf(i -> (now - i.startNanos) / 1.0e9D > LIFE);
            for (Impulse i : IMPULSES) {
                double t = (now - i.startNanos) / 1.0e9D;
                double env = Math.exp(-6.5D * t);
                pitch += (float) (i.power * env * Math.sin(2.0D * Math.PI * 5.0D * t));          // golpe hacia abajo y rebote
                roll += (float) (i.power * 0.55D * i.rollSign * env * Math.sin(2.0D * Math.PI * 3.2D * t));
                yaw += (float) (i.power * 0.2D * i.rollSign * env * Math.sin(2.0D * Math.PI * 4.1D * t + 1.0D));
            }
        }
        float max = 14.0F;
        return new float[]{Math.max(-max, Math.min(max, pitch)), Math.max(-max, Math.min(max, roll)), Math.max(-max, Math.min(max, yaw))};
    }
}
