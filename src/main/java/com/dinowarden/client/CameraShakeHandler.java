package com.dinowarden.client;

import com.dinowarden.DinoWardenMod;
import com.dinowarden.entity.DinoWardenEntity;
import net.minecraft.client.Camera;
import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.api.distmarker.Dist;
import net.minecraftforge.client.event.ViewportEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/** Agita la camara de los jugadores cercanos mientras un Dino Warden ruge. */
@Mod.EventBusSubscriber(modid = DinoWardenMod.MODID, bus = Mod.EventBusSubscriber.Bus.FORGE, value = Dist.CLIENT)
public final class CameraShakeHandler {
    private static final double RANGE = 40.0D;
    private static final float STRENGTH = 1.0F;   // sube/baja para mas o menos temblor

    private CameraShakeHandler() {}

    private static double envelope(float p) {
        double e;
        if (p < 0.10F) e = 0.0D;
        else if (p < 0.25F) e = (p - 0.10F) / 0.15F;
        else if (p < 0.75F) e = 1.0D;
        else if (p < 0.92F) e = (0.92F - p) / 0.17F;
        else e = 0.0D;
        // sacudida extra en el instante del sonic boom (~54 % del rugido)
        if (p > 0.53F && p < 0.62F) e += 0.7D;
        return e;
    }

    @SubscribeEvent
    public static void onCameraAngles(ViewportEvent.ComputeCameraAngles event) {
        ClientLevel level = Minecraft.getInstance().level;
        if (level == null) return;

        Camera camera = event.getCamera();
        Vec3 pos = camera.getPosition();
        float partial = (float) event.getPartialTick();

        double total = 0.0D;
        for (DinoWardenEntity dino : level.getEntitiesOfClass(DinoWardenEntity.class, new AABB(pos, pos).inflate(RANGE))) {
            if (!dino.isRoaring()) continue;
            double dist = dino.position().distanceTo(pos);
            if (dist > RANGE) continue;
            double falloff = 1.0D - dist / RANGE;
            total += envelope(dino.getRoarProgress(partial)) * falloff * falloff;
        }
        // temblor por pisadas (StepShake): se suma al del rugido
        float[] step = StepShake.sample();
        event.setPitch(event.getPitch() + step[0]);
        event.setRoll(event.getRoll() + step[1]);
        event.setYaw(event.getYaw() + step[2]);

        if (total < 0.002D) return;
        total = Math.min(total, 1.6D) * STRENGTH;

        double t = level.getGameTime() + partial;
        float pitch = (float) (total * (Math.sin(t * 3.1D) * 0.9D + Math.sin(t * 7.7D) * 0.5D));
        float yaw   = (float) (total * (Math.sin(t * 2.3D + 1.0D) * 0.9D + Math.sin(t * 6.1D) * 0.5D));
        float roll  = (float) (total * (Math.sin(t * 4.3D + 2.0D) * 1.6D + Math.sin(t * 9.1D) * 0.8D));

        event.setPitch(event.getPitch() + pitch);
        event.setYaw(event.getYaw() + yaw);
        event.setRoll(event.getRoll() + roll);
    }
}
