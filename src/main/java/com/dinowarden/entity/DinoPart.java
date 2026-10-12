package com.dinowarden.entity;

import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityDimensions;
import net.minecraft.world.entity.Pose;
import net.minecraftforge.entity.PartEntity;

/**
 * Pieza de hitbox del Dino Warden (como las partes del Ender Dragon): cabeza, cuello y 3 tramos de cola.
 * Cualquier golpe, flecha o ataque que toque una pieza se redirige al Dino Warden.
 */
public class DinoPart extends PartEntity<DinoWardenEntity> {
    public final String name;
    private final EntityDimensions size;

    public DinoPart(DinoWardenEntity parent, String name, float width, float height) {
        super(parent);
        this.name = name;
        this.size = EntityDimensions.scalable(width, height);
        this.refreshDimensions();
    }

    @Override protected void defineSynchedData() { }
    @Override protected void readAdditionalSaveData(CompoundTag tag) { }
    @Override protected void addAdditionalSaveData(CompoundTag tag) { }

    @Override public boolean isPickable() { return true; }

    @Override
    public boolean hurt(DamageSource source, float amount) {
        return !this.isInvulnerableTo(source) && this.getParent().hurt(source, amount);
    }

    @Override public boolean is(Entity other) { return this == other || this.getParent() == other; }
    @Override public EntityDimensions getDimensions(Pose pose) { return this.size; }
    @Override public boolean shouldBeSaved() { return false; }
}
