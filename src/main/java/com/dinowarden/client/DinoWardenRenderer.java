package com.dinowarden.client;

import com.dinowarden.entity.DinoWardenEntity;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import software.bernie.geckolib.renderer.GeoEntityRenderer;
import software.bernie.geckolib.renderer.layer.AutoGlowingGeoLayer;

public class DinoWardenRenderer extends GeoEntityRenderer<DinoWardenEntity> {
    public DinoWardenRenderer(EntityRendererProvider.Context context) {
        super(context, new DinoWardenModel());
        this.shadowRadius = 1.6F;
        // Brillo en la oscuridad: usa textures/entity/dinowarden_glowmask.png
        addRenderLayer(new AutoGlowingGeoLayer<>(this));
    }
}
