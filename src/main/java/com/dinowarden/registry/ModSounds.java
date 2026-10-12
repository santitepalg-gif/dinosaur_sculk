package com.dinowarden.registry;

import com.dinowarden.DinoWardenMod;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvent;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

public final class ModSounds {
    public static final DeferredRegister<SoundEvent> SOUNDS =
            DeferredRegister.create(ForgeRegistries.SOUND_EVENTS, DinoWardenMod.MODID);

    public static final RegistryObject<SoundEvent> ROAR    = register("entity.dino_warden.roar");
    public static final RegistryObject<SoundEvent> BELLOW  = register("entity.dino_warden.bellow");
    public static final RegistryObject<SoundEvent> STEP    = register("entity.dino_warden.step");
    public static final RegistryObject<SoundEvent> HURT    = register("entity.dino_warden.hurt");
    public static final RegistryObject<SoundEvent> DEATH   = register("entity.dino_warden.death");
    public static final RegistryObject<SoundEvent> AMBIENT = register("entity.dino_warden.ambient");
    public static final RegistryObject<SoundEvent> BITE    = register("entity.dino_warden.bite");

    private static RegistryObject<SoundEvent> register(String name) {
        return SOUNDS.register(name,
                () -> SoundEvent.createVariableRangeEvent(new ResourceLocation(DinoWardenMod.MODID, name)));
    }

    private ModSounds() {}
}
