package com.dinowarden.event;

import com.dinowarden.DinoWardenMod;
import com.dinowarden.entity.DinoWardenEntity;
import net.minecraft.world.entity.ai.Brain;
import net.minecraft.world.entity.ai.memory.MemoryModuleType;
import net.minecraft.world.entity.monster.warden.Warden;
import net.minecraftforge.event.entity.living.LivingChangeTargetEvent;
import net.minecraftforge.event.entity.living.LivingEvent;
import net.minecraftforge.eventbus.api.SubscribeEvent;
import net.minecraftforge.fml.common.Mod;

/** El Warden nunca ataca al Dino Warden: se le borra enojo y objetivo cada pocos ticks. */
@Mod.EventBusSubscriber(modid = DinoWardenMod.MODID)
public final class WardenPeaceHandler {
    private WardenPeaceHandler() {}

    @SubscribeEvent
    public static void onWardenTick(LivingEvent.LivingTickEvent event) {
        if (!(event.getEntity() instanceof Warden warden)) return;
        if (warden.level().isClientSide || warden.tickCount % 4 != 0) return;

        for (DinoWardenEntity dino : warden.level().getEntitiesOfClass(DinoWardenEntity.class, warden.getBoundingBox().inflate(48.0D))) {
            warden.clearAnger(dino);
            Brain<Warden> brain = warden.getBrain();
            brain.getMemory(MemoryModuleType.ATTACK_TARGET)
                    .filter(t -> t == dino)
                    .ifPresent(t -> brain.eraseMemory(MemoryModuleType.ATTACK_TARGET));
            brain.getMemory(MemoryModuleType.ROAR_TARGET)
                    .filter(t -> t == dino)
                    .ifPresent(t -> brain.eraseMemory(MemoryModuleType.ROAR_TARGET));
        }
    }

    @SubscribeEvent
    public static void onChangeTarget(LivingChangeTargetEvent event) {
        if (event.getEntity() instanceof Warden && event.getNewTarget() instanceof DinoWardenEntity) {
            event.setCanceled(true);
        }
    }
}
