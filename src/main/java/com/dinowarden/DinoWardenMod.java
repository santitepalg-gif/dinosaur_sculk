package com.dinowarden;

import com.dinowarden.entity.DinoWardenEntity;
import com.dinowarden.registry.ModEntities;
import com.dinowarden.registry.ModItems;
import com.dinowarden.registry.ModSounds;
import com.mojang.logging.LogUtils;
import net.minecraft.world.item.CreativeModeTabs;
import net.minecraftforge.event.BuildCreativeModeTabContentsEvent;
import net.minecraftforge.event.entity.EntityAttributeCreationEvent;
import net.minecraftforge.eventbus.api.IEventBus;
import net.minecraftforge.fml.common.Mod;
import net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext;
import org.slf4j.Logger;

@Mod(DinoWardenMod.MODID)
public class DinoWardenMod {
    public static final String MODID = "dinowarden";
    public static final Logger LOGGER = LogUtils.getLogger();

    public DinoWardenMod() {
        IEventBus modBus = FMLJavaModLoadingContext.get().getModEventBus();
        ModEntities.ENTITIES.register(modBus);
        ModItems.ITEMS.register(modBus);
        ModSounds.SOUNDS.register(modBus);
        modBus.addListener(DinoWardenMod::onAttributes);
        modBus.addListener(DinoWardenMod::onCreativeTab);
    }

    private static void onAttributes(EntityAttributeCreationEvent event) {
        event.put(ModEntities.DINO_WARDEN.get(), DinoWardenEntity.createAttributes().build());
    }

    private static void onCreativeTab(BuildCreativeModeTabContentsEvent event) {
        if (event.getTabKey() == CreativeModeTabs.SPAWN_EGGS) {
            event.accept(ModItems.DINO_WARDEN_SPAWN_EGG);
        }
    }
}
