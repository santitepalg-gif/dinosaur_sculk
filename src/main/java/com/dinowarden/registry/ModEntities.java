package com.dinowarden.registry;

import com.dinowarden.DinoWardenMod;
import com.dinowarden.entity.DinoWardenEntity;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.MobCategory;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

public final class ModEntities {
    public static final DeferredRegister<EntityType<?>> ENTITIES =
            DeferredRegister.create(ForgeRegistries.ENTITY_TYPES, DinoWardenMod.MODID);

    /** Hitbox del cuerpo (1.9 x 3.1). Cabeza, cuello y cola tienen sus propias piezas (DinoPart). */
    public static final RegistryObject<EntityType<DinoWardenEntity>> DINO_WARDEN = ENTITIES.register("dino_warden",
            () -> EntityType.Builder.of(DinoWardenEntity::new, MobCategory.MONSTER)
                    .sized(1.9F, 3.1F)
                    .clientTrackingRange(10)
                    .build(new ResourceLocation(DinoWardenMod.MODID, "dino_warden").toString()));

    private ModEntities() {}
}
