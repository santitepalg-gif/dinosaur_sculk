package com.dinowarden.client;

import com.dinowarden.DinoWardenMod;
import com.dinowarden.entity.DinoWardenEntity;
import net.minecraft.resources.ResourceLocation;
import software.bernie.geckolib.model.GeoModel;

public class DinoWardenModel extends GeoModel<DinoWardenEntity> {
    @Override
    public ResourceLocation getModelResource(DinoWardenEntity animatable) {
        return new ResourceLocation(DinoWardenMod.MODID, "geo/dinowarden.geo.json");
    }

    @Override
    public ResourceLocation getTextureResource(DinoWardenEntity animatable) {
        return new ResourceLocation(DinoWardenMod.MODID, "textures/entity/dinowarden.png");
    }

    @Override
    public ResourceLocation getAnimationResource(DinoWardenEntity animatable) {
        return new ResourceLocation(DinoWardenMod.MODID, "animations/dinowarden.animation.json");
    }
}
