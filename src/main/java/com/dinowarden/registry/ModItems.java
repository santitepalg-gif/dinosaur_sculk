package com.dinowarden.registry;

import com.dinowarden.DinoWardenMod;
import net.minecraft.world.item.Item;
import net.minecraftforge.common.ForgeSpawnEggItem;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.ForgeRegistries;
import net.minecraftforge.registries.RegistryObject;

public final class ModItems {
    public static final DeferredRegister<Item> ITEMS =
            DeferredRegister.create(ForgeRegistries.ITEMS, DinoWardenMod.MODID);

    public static final RegistryObject<Item> DINO_WARDEN_SPAWN_EGG = ITEMS.register("dino_warden_spawn_egg",
            () -> new ForgeSpawnEggItem(ModEntities.DINO_WARDEN, 0x0E262C, 0x3CEBD7, new Item.Properties()));

    private ModItems() {}
}
