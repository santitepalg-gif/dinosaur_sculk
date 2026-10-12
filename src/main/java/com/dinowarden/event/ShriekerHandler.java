package com.dinowarden.event;

import com.dinowarden.DinoWardenMod;
import com.dinowarden.entity.DinoWardenEntity;
import com.dinowarden.registry.ModEntities;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.EntitySelector;
import net.minecraft.world.entity.MobSpawnType;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.gameevent.GameEvent;
import net.minecraft.world.phys.AABB;
import net.minecraftforge.event.VanillaGameEvent;
import net.minecraftforge.event.server.ServerStoppedEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

import java.util.HashMap;
import java.util.Map;

/**
 * Cuenta los gritos de cada Sculk Shrieker. Al 2.o grito (dentro de WINDOW_TICKS) aparece el Dino Warden.
 */
@Mod.EventBusSubscriber(modid = DinoWardenMod.MODID)
public final class ShriekerHandler {
    /** Ventana para encadenar los 2 gritos (60 s). */
    private static final int WINDOW_TICKS = 1200;
    /** Enfriamiento por shrieker tras invocar (5 min). */
    private static final long COOLDOWN_TICKS = 6000L;

    private static final Map<String, long[]> TRACK = new HashMap<>();       // {gritos, ultimoTick}
    private static final Map<String, Long> LAST_SPAWN = new HashMap<>();

    private ShriekerHandler() {}

    @SubscribeEvent
    public static void onGameEvent(VanillaGameEvent event) {
        if (event.getVanillaEvent() != GameEvent.SHRIEK) return;
        if (!(event.getLevel() instanceof ServerLevel level)) return;

        BlockPos pos = BlockPos.containing(event.getEventPosition());
        if (!level.getBlockState(pos).is(Blocks.SCULK_SHRIEKER)) return;

        long now = level.getGameTime();
        String key = level.dimension().location() + "|" + pos.asLong();

        Long lastSpawn = LAST_SPAWN.get(key);
        if (lastSpawn != null && now - lastSpawn < COOLDOWN_TICKS) return;

        // limpieza de entradas viejas
        TRACK.values().removeIf(v -> now - v[1] > WINDOW_TICKS * 2L);

        long[] rec = TRACK.get(key);
        if (rec == null || now - rec[1] > WINDOW_TICKS) {
            rec = new long[]{1, now};
        } else {
            rec[0]++;
            rec[1] = now;
        }
        TRACK.put(key, rec);
        DinoWardenMod.LOGGER.info("[DinoWarden] Grito #{} del shrieker en {}", rec[0], pos);

        if (rec[0] >= 2) {
            TRACK.remove(key);
            if (spawnDino(level, pos)) LAST_SPAWN.put(key, now);
        }
    }

    @SubscribeEvent
    public static void onServerStopped(ServerStoppedEvent event) {
        TRACK.clear();
        LAST_SPAWN.clear();
    }

    private static boolean spawnDino(ServerLevel level, BlockPos origin) {
        DinoWardenEntity dino = ModEntities.DINO_WARDEN.get().create(level);
        if (dino == null) return false;

        RandomSource rnd = level.random;
        boolean placed = false;
        for (int i = 0; i < 48 && !placed; i++) {
            double angle = rnd.nextDouble() * Math.PI * 2.0D;
            double dist = 4.0D + rnd.nextDouble() * 5.0D;
            double x = origin.getX() + 0.5D + Math.cos(angle) * dist;
            double z = origin.getZ() + 0.5D + Math.sin(angle) * dist;
            for (int dy = 3; dy >= -3 && !placed; dy--) {
                double y = origin.getY() + dy;
                dino.moveTo(x, y, z, rnd.nextFloat() * 360.0F, 0.0F);
                BlockPos below = BlockPos.containing(x, y - 0.5D, z);
                boolean solidFloor = !level.getBlockState(below).getCollisionShape(level, below).isEmpty();
                AABB box = dino.getBoundingBox();
                if (solidFloor && level.noCollision(dino) && !level.containsAnyLiquid(box)) placed = true;
            }
        }
        if (!placed) dino.moveTo(origin.getX() + 0.5D, origin.getY() + 1.0D, origin.getZ() + 0.5D, rnd.nextFloat() * 360.0F, 0.0F);

        dino.finalizeSpawn(level, level.getCurrentDifficultyAt(dino.blockPosition()), MobSpawnType.EVENT, null, null);
        dino.setPersistenceRequired();
        level.addFreshEntityWithPassengers(dino);

        Player nearest = level.getNearestPlayer(dino.getX(), dino.getY(), dino.getZ(), 40.0D, EntitySelector.NO_CREATIVE_OR_SPECTATOR);
        if (nearest != null) dino.setTarget(nearest);
        return true;
    }
}
