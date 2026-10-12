package com.dinowarden.event;

import com.dinowarden.DinoWardenMod;
import com.dinowarden.entity.DinoWardenEntity;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.level.gameevent.GameEvent;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.event.VanillaGameEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import java.util.HashMap;
import java.util.Map;

/**
 * Oido del Dino Warden: escucha las mismas "vibraciones" que el Warden (pasos, bloques, golpes, explosiones...).
 * Los jugadores agachados no hacen ruido de pasos (igual que con el Warden).
 */
@Mod.EventBusSubscriber(modid = DinoWardenMod.MODID)
public final class SoundSenseHandler {
    /** Alcance (bloques) de cada tipo de vibracion. */
    private static final Map<GameEvent, Double> RANGE = new HashMap<>();

    private static void put(double range, GameEvent... events) {
        for (GameEvent e : events) RANGE.put(e, range);
    }

    static {
        put(20.0D, GameEvent.STEP, GameEvent.SWIM, GameEvent.BLOCK_OPEN, GameEvent.BLOCK_CLOSE,
                GameEvent.CONTAINER_OPEN, GameEvent.CONTAINER_CLOSE);
        put(24.0D, GameEvent.HIT_GROUND, GameEvent.SPLASH, GameEvent.BLOCK_PLACE, GameEvent.BLOCK_DESTROY);
        put(32.0D, GameEvent.ENTITY_DAMAGE, GameEvent.ENTITY_DIE, GameEvent.EXPLODE,
                GameEvent.PROJECTILE_SHOOT, GameEvent.PROJECTILE_LAND, GameEvent.ENTITY_ROAR);
    }

    private SoundSenseHandler() {}

    @SubscribeEvent
    public static void onGameEvent(VanillaGameEvent event) {
        if (!(event.getLevel() instanceof ServerLevel level)) return;
        Double range = RANGE.get(event.getVanillaEvent());
        if (range == null) return;

        Vec3 pos = event.getEventPosition();
        Entity cause = event.getCause();
        AABB box = new AABB(pos, pos).inflate(range);
        for (DinoWardenEntity dino : level.getEntitiesOfClass(DinoWardenEntity.class, box)) {
            if (dino.distanceToSqr(pos) <= range * range) dino.hearVibration(pos, cause);
        }
    }
}
