package com.dinowarden.entity;

import com.dinowarden.entity.goal.DinoBellowGoal;
import com.dinowarden.entity.goal.DinoBiteGoal;
import com.dinowarden.entity.goal.DinoInvestigateGoal;
import com.dinowarden.entity.goal.DinoRoarGoal;
import com.dinowarden.registry.ModSounds;
import net.minecraft.core.BlockPos;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.network.syncher.EntityDataSerializers;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.tags.FluidTags;
import net.minecraft.util.Mth;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityDimensions;
import net.minecraft.world.entity.EntitySelector;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.entity.Pose;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.ai.goal.FloatGoal;
import net.minecraft.world.entity.ai.goal.LookAtPlayerGoal;
import net.minecraft.world.entity.ai.goal.RandomLookAroundGoal;
import net.minecraft.world.entity.ai.goal.RandomStrollGoal;
import net.minecraft.world.entity.ai.goal.RandomSwimmingGoal;
import net.minecraft.world.entity.ai.control.MoveControl;
import net.minecraft.world.entity.ai.navigation.PathNavigation;
import net.minecraft.world.entity.ai.navigation.WaterBoundPathNavigation;
import net.minecraftforge.entity.PartEntity;
import net.minecraft.world.entity.ai.goal.target.HurtByTargetGoal;
import net.minecraft.world.entity.ai.goal.target.NearestAttackableTargetGoal;
import net.minecraft.world.entity.ai.attributes.Attribute;
import net.minecraft.world.entity.monster.Monster;
import net.minecraft.world.entity.monster.warden.Warden;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.pathfinder.BlockPathTypes;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.BlockHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.common.ForgeMod;
import org.jetbrains.annotations.Nullable;
import software.bernie.geckolib.animatable.GeoEntity;
import software.bernie.geckolib.core.animatable.instance.AnimatableInstanceCache;
import software.bernie.geckolib.core.animation.AnimatableManager;
import software.bernie.geckolib.core.animation.AnimationController;
import software.bernie.geckolib.core.animation.AnimationState;
import software.bernie.geckolib.core.animation.RawAnimation;
import software.bernie.geckolib.core.object.PlayState;
import software.bernie.geckolib.util.GeckoLibUtil;

/**
 * Dino Warden: dinosaurio de sculk estilo T-Rex.
 *  - Acciones sincronizadas (ACTION) que el cliente usa para elegir la animacion.
 *  - Rugido (70 ticks) -> en el tick 38 dispara el sonic boom; el cliente agita la camara.
 *  - Bramido en el agua (60 ticks), mordida (18 ticks).
 */
public class DinoWardenEntity extends Monster implements GeoEntity {

    // ---- acciones
    public static final int ACT_NONE = 0;
    public static final int ACT_ROAR = 1;
    public static final int ACT_BITE = 2;
    public static final int ACT_BELLOW = 3;

    // ---- duraciones (ticks). Deben coincidir con animation_length * 20 del JSON de animaciones.
    public static final int ROAR_TICKS = 70;      // roar: 3.5 s
    public static final int ROAR_BOOM_TICK = 38;  // 1.9 s: mandibula abierta al maximo
    public static final int BITE_TICKS = 18;      // bite: 0.9 s
    public static final int BITE_HIT_TICK = 8;    // 0.4 s: el hocico llega al objetivo
    public static final int BELLOW_TICKS = 60;    // bellow: 3.0 s

    // ---- sentidos (estilo Warden)
    /** Olfato: detecta jugadores cercanos aunque no los vea ni los oiga (no depende de agacharse). */
    public static final double SMELL_RANGE = 12.0D;
    /** Contacto directo: tocar cualquier parte del cuerpo (cabeza, cola...) lo alerta. */
    public static final double TOUCH_MARGIN = 0.8D;

    public static final double BOOM_RANGE = 28.0D;
    public static final float BOOM_DAMAGE = 14.0F;

    private static final EntityDataAccessor<Integer> ACTION =
            SynchedEntityData.defineId(DinoWardenEntity.class, EntityDataSerializers.INT);

    private static final RawAnimation ANIM_IDLE   = RawAnimation.begin().thenLoop("animation.dinowarden.idle");
    private static final RawAnimation ANIM_WALK   = RawAnimation.begin().thenLoop("animation.dinowarden.walk");
    private static final RawAnimation ANIM_RUN    = RawAnimation.begin().thenLoop("animation.dinowarden.run");
    private static final RawAnimation ANIM_SWIM   = RawAnimation.begin().thenLoop("animation.dinowarden.swim");
    private static final RawAnimation ANIM_ROAR   = RawAnimation.begin().thenPlayAndHold("animation.dinowarden.roar");
    private static final RawAnimation ANIM_BITE   = RawAnimation.begin().thenPlayAndHold("animation.dinowarden.bite");
    private static final RawAnimation ANIM_BELLOW = RawAnimation.begin().thenPlayAndHold("animation.dinowarden.bellow");

    private final AnimatableInstanceCache cache = GeckoLibUtil.createInstanceCache(this);

    private int lastAction = ACT_NONE;
    private int actionElapsed = 0;   // ticks transcurridos de la accion actual (server y cliente)
    private int roarCooldown = 120;
    private int bellowCooldown = 200;

    // ---- hitbox por piezas (cabeza, cuello, cola) -> ver updateParts()
    private final DinoPart partHead;
    private final DinoPart partNeck;
    private final DinoPart partTailA;
    private final DinoPart partTailB;
    private final DinoPart partTailC;
    private final DinoPart[] parts;

    // ---- nado
    private final PathNavigation groundNavigation;
    private final PathNavigation waterNavigation;

    // ---- oido
    @Nullable private Vec3 heardPos;
    private int heardTicks;

    public DinoWardenEntity(EntityType<? extends Monster> type, Level level) {
        super(type, level);
        this.xpReward = 60;
        this.setMaxUpStep(1.25F);
        this.setPathfindingMalus(BlockPathTypes.WATER, 0.0F);   // puede caminar/nadar por el agua
        AttributeInstance swim = this.getAttribute(ForgeMod.SWIM_SPEED.get());
        if (swim != null) swim.setBaseValue(2.5D);

        this.groundNavigation = this.navigation;
        this.waterNavigation = new WaterBoundPathNavigation(this, level);
        this.moveControl = new DinoMoveControl(this);

        // medidas en bloques: (ancho, alto). Posiciones en updateParts().
        this.partHead = new DinoPart(this, "head", 1.5F, 1.7F);
        this.partNeck = new DinoPart(this, "neck", 1.0F, 1.2F);
        this.partTailA = new DinoPart(this, "tail_a", 1.2F, 1.0F);
        this.partTailB = new DinoPart(this, "tail_b", 1.1F, 0.85F);
        this.partTailC = new DinoPart(this, "tail_c", 1.4F, 0.7F);
        this.parts = new DinoPart[]{partHead, partNeck, partTailA, partTailB, partTailC};
    }

    public static AttributeSupplier.Builder createAttributes() {
        return Monster.createMonsterAttributes()
                .add(Attributes.MAX_HEALTH, 260.0D)
                .add(Attributes.MOVEMENT_SPEED, 0.30D)
                .add(Attributes.ATTACK_DAMAGE, 20.0D)
                .add(Attributes.ATTACK_KNOCKBACK, 1.5D)
                .add(Attributes.KNOCKBACK_RESISTANCE, 1.0D)
                .add(Attributes.FOLLOW_RANGE, 40.0D)
                .add(Attributes.ARMOR, 8.0D);
    }

    // ------------------------------------------------------------------ IA
    @Override
    protected void registerGoals() {
        // flota solo cuando esta en aguas poco profundas; en aguas hondas nada de verdad
        this.goalSelector.addGoal(0, new FloatGoal(this) {
            @Override public boolean canUse() { return !DinoWardenEntity.this.isSwimmingMode() && super.canUse(); }
        });
        this.goalSelector.addGoal(1, new DinoRoarGoal(this));
        this.goalSelector.addGoal(2, new DinoBellowGoal(this));
        this.goalSelector.addGoal(3, new DinoBiteGoal(this, 1.15D, true));
        this.goalSelector.addGoal(4, new DinoInvestigateGoal(this));
        this.goalSelector.addGoal(5, new RandomStrollGoal(this, 0.7D) {
            @Override public boolean canUse() { return !DinoWardenEntity.this.isSwimmingMode() && super.canUse(); }
        });
        this.goalSelector.addGoal(5, new RandomSwimmingGoal(this, 0.8D, 40) {
            @Override public boolean canUse() { return DinoWardenEntity.this.isSwimmingMode() && super.canUse(); }
        });
        this.goalSelector.addGoal(6, new LookAtPlayerGoal(this, Player.class, 16.0F));
        this.goalSelector.addGoal(7, new RandomLookAroundGoal(this));

        // Ignora el dano del Warden y de otros Dino Warden al elegir objetivo
        this.targetSelector.addGoal(1, new HurtByTargetGoal(this, Warden.class, DinoWardenEntity.class));
        this.targetSelector.addGoal(2, new NearestAttackableTargetGoal<>(this, Player.class, true));
    }

    // ------------------------------------------------------------------ datos
    @Override
    protected void defineSynchedData() {
        super.defineSynchedData();
        this.entityData.define(ACTION, ACT_NONE);
    }

    public int getAction() { return this.entityData.get(ACTION); }
    private void setAction(int action) { this.entityData.set(ACTION, action); }

    public boolean isRoaring() { return getAction() == ACT_ROAR; }

    /** Progreso 0..1 del rugido (para el temblor de camara en el cliente). */
    public float getRoarProgress(float partialTick) {
        return Mth.clamp((this.actionElapsed + partialTick) / (float) ROAR_TICKS, 0.0F, 1.0F);
    }

    // ------------------------------------------------------------------ acciones (servidor)
    public boolean canStartRoar() { return getAction() == ACT_NONE && this.roarCooldown <= 0; }
    public boolean canStartBellow() { return getAction() == ACT_NONE && this.bellowCooldown <= 0 && this.isInWater(); }

    public void beginRoar() {
        setAction(ACT_ROAR);
        this.roarCooldown = 260 + this.random.nextInt(140);
        this.playSound(ModSounds.ROAR.get(), 5.0F, 0.95F + this.random.nextFloat() * 0.1F);
    }

    public void beginBite() {
        setAction(ACT_BITE);
    }

    public void beginBellow() {
        setAction(ACT_BELLOW);
        this.bellowCooldown = 400 + this.random.nextInt(400);
        this.playSound(ModSounds.BELLOW.get(), 4.0F, 0.95F + this.random.nextFloat() * 0.1F);
    }

    @Override
    public void tick() {
        super.tick();
        int act = getAction();
        if (act != this.lastAction) {
            this.lastAction = act;
            this.actionElapsed = 0;
        }
        if (act != ACT_NONE) this.actionElapsed++;
        if (!this.level().isClientSide) {
            serverTickActions(act);
            tickSenses();
        }
        updateParts();
    }

    private void serverTickActions(int act) {
        if (this.roarCooldown > 0) this.roarCooldown--;
        if (this.bellowCooldown > 0) this.bellowCooldown--;
        LivingEntity target = this.getTarget();

        switch (act) {
            case ACT_ROAR -> {
                this.getNavigation().stop();
                if (target != null) faceTarget(target, 12.0F);
                if (this.actionElapsed == ROAR_BOOM_TICK) fireSonicBoom(target);
                if (this.actionElapsed >= ROAR_TICKS) setAction(ACT_NONE);
            }
            case ACT_BITE -> {
                if (target != null) faceTarget(target, 25.0F);
                if (this.actionElapsed == BITE_HIT_TICK && target != null) {
                    double reach = this.getBbWidth() * 2.2D + target.getBbWidth();
                    if (this.distanceToSqr(target) <= reach * reach) {
                        this.playSound(ModSounds.BITE.get(), 2.0F, 1.0F);
                        this.doHurtTarget(target);
                    }
                }
                if (this.actionElapsed >= BITE_TICKS) setAction(ACT_NONE);
            }
            case ACT_BELLOW -> {
                this.getNavigation().stop();
                if (!this.isInWater()) {           // si sale del agua, se cancela
                    setAction(ACT_NONE);
                } else {
                    if (this.actionElapsed >= 10 && this.actionElapsed <= 50 && this.actionElapsed % 3 == 0
                            && this.level() instanceof ServerLevel server) {
                        double y = this.getY() + Math.min(this.getFluidHeight(FluidTags.WATER), 2.5D) + 0.1D;
                        server.sendParticles(ParticleTypes.SPLASH, this.getX(), y, this.getZ(), 14, 0.9D, 0.1D, 1.2D, 0.25D);
                        server.sendParticles(ParticleTypes.BUBBLE, this.getX(), y - 0.5D, this.getZ(), 6, 0.9D, 0.2D, 1.2D, 0.05D);
                    }
                    if (target != null || this.actionElapsed >= BELLOW_TICKS) setAction(ACT_NONE);
                }
            }
            default -> { }
        }
    }

    private void faceTarget(LivingEntity target, float maxStep) {
        double dx = target.getX() - this.getX();
        double dz = target.getZ() - this.getZ();
        float want = (float) (Mth.atan2(dz, dx) * (180.0D / Math.PI)) - 90.0F;
        float yaw = Mth.approachDegrees(this.getYRot(), want, maxStep);
        this.setYRot(yaw);
        this.setYBodyRot(yaw);
        this.setYHeadRot(yaw);
    }

    // ------------------------------------------------------------------ hitbox por piezas
    @Override public boolean isMultipartEntity() { return true; }
    @Override public PartEntity<?>[] getParts() { return this.parts; }

    @Override
    public void setId(int id) {
        super.setId(id);
        if (this.parts != null) {
            for (int i = 0; i < this.parts.length; i++) this.parts[i].setId(id + i + 1);
        }
    }

    /** Coloca cada pieza detras/delante del cuerpo segun hacia donde mira (misma matematica en cliente y servidor). */
    private void updateParts() {
        float yaw = this.yBodyRot * ((float) Math.PI / 180.0F);
        float sin = Mth.sin(yaw);
        float cos = Mth.cos(yaw);
        placePart(this.partHead, 2.35D, 1.95D, sin, cos);
        placePart(this.partNeck, 1.3D, 1.9D, sin, cos);
        placePart(this.partTailA, -1.4D, 1.65D, sin, cos);
        placePart(this.partTailB, -2.6D, 1.7D, sin, cos);
        placePart(this.partTailC, -3.85D, 1.8D, sin, cos);
    }

    private void placePart(DinoPart part, double forward, double up, float sin, float cos) {
        part.setPos(this.getX() - sin * forward, this.getY() + up, this.getZ() + cos * forward);
    }

    // ------------------------------------------------------------------ sentidos: olfato, oido y contacto
    private boolean isValidPrey(Player p) {
        return p.isAlive() && EntitySelector.NO_CREATIVE_OR_SPECTATOR.test(p);
    }

    /** Contacto directo: el cuerpo o cualquier pieza (cabeza, cola) toca al jugador. */
    private boolean isTouching(Entity e) {
        AABB box = e.getBoundingBox();
        if (this.getBoundingBox().inflate(TOUCH_MARGIN).intersects(box)) return true;
        for (DinoPart part : this.parts) {
            if (part.getBoundingBox().inflate(TOUCH_MARGIN).intersects(box)) return true;
        }
        return false;
    }

    private void tickSenses() {
        if (this.heardTicks > 0 && --this.heardTicks == 0) this.heardPos = null;
        if (this.tickCount % 5 != 0) return;

        LivingEntity current = this.getTarget();
        if (current != null) {
            if (!current.isAlive() || this.distanceToSqr(current) > 60.0D * 60.0D) this.setTarget(null);
            return;
        }

        Player best = null;
        double bestDist = Double.MAX_VALUE;
        AABB area = this.getBoundingBox().inflate(SMELL_RANGE + 4.0D);
        for (Player p : this.level().getEntitiesOfClass(Player.class, area, this::isValidPrey)) {
            double d = this.distanceToSqr(p);
            boolean smelled = d <= SMELL_RANGE * SMELL_RANGE;
            if ((smelled || isTouching(p)) && d < bestDist) {
                best = p;
                bestDist = d;
            }
        }
        if (best != null) {
            this.setTarget(best);
            this.heardPos = null;
            this.playSound(SoundEvents.WARDEN_SNIFF, 2.0F, 0.7F);
        }
    }

    /** Llamado por SoundSenseHandler cuando ocurre una vibracion dentro de su alcance. */
    public void hearVibration(Vec3 pos, @Nullable Entity cause) {
        if (cause == this || cause instanceof DinoWardenEntity || cause instanceof Warden) return;
        if (cause instanceof Player p && isValidPrey(p)) {
            if (this.getTarget() == null) {
                this.setTarget(p);
                this.heardPos = null;
                this.playSound(SoundEvents.WARDEN_LISTENING_ANGRY, 2.0F, 0.7F);
            }
            return;
        }
        if (this.getTarget() == null) {
            this.heardPos = pos;
            this.heardTicks = 200;
        }
    }

    @Nullable public Vec3 getHeardPos() { return this.heardPos; }
    public void clearHeardPos() { this.heardPos = null; this.heardTicks = 0; }

    // ------------------------------------------------------------------ nado
    /** Nada de verdad cuando el agua le cubre la mayor parte del cuerpo. */
    public boolean isSwimmingMode() {
        return this.isInWater() && this.getFluidHeight(FluidTags.WATER) > 1.2D;
    }

    @Override
    protected void customServerAiStep() {
        super.customServerAiStep();
        boolean swim = this.isSwimmingMode();
        PathNavigation want = swim ? this.waterNavigation : this.groundNavigation;
        if (this.navigation != want) {
            this.navigation.stop();
            this.navigation = want;
        }
        LivingEntity target = this.getTarget();
        if (swim && target != null && this.navigation.isDone() && getAction() == ACT_NONE) {
            // objetivo fuera del agua: nada directo hacia el
            this.moveControl.setWantedPosition(target.getX(), target.getY(), target.getZ(), 1.2D);
        }
    }

    @Override
    public void travel(Vec3 input) {
        if (this.isControlledByLocalInstance() && this.isSwimmingMode()) {
            this.moveRelative(0.01F, input);
            this.move(MoverType.SELF, this.getDeltaMovement());
            Vec3 dm = this.getDeltaMovement().scale(0.9D);
            if (this.getTarget() == null) {      // sin objetivo: se mantiene a media agua, asomando la cabeza
                double depth = this.getFluidHeight(FluidTags.WATER);
                if (depth > 2.3D) dm = dm.add(0.0D, 0.012D, 0.0D);
                else if (depth < 1.7D) dm = dm.add(0.0D, -0.01D, 0.0D);
            }
            this.setDeltaMovement(dm);
        } else {
            super.travel(input);
        }
    }

    @Override
    public boolean isPushedByFluid() { return !this.isSwimmingMode(); }

    /** Control de movimiento: en aguas hondas se desliza en 3D hacia el punto deseado; en tierra se comporta normal. */
    private static class DinoMoveControl extends MoveControl {
        private final DinoWardenEntity dino;

        DinoMoveControl(DinoWardenEntity dino) {
            super(dino);
            this.dino = dino;
        }

        @Override
        public void tick() {
            if (!this.dino.isSwimmingMode()) {
                super.tick();
                return;
            }
            if (this.operation != Operation.MOVE_TO) {
                this.dino.setSpeed(0.0F);
                return;
            }
            this.operation = Operation.WAIT;
            double dx = this.wantedX - this.dino.getX();
            double dy = this.wantedY - this.dino.getY();
            double dz = this.wantedZ - this.dino.getZ();
            double dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
            if (dist < 0.3D) {
                this.dino.setSpeed(0.0F);
                return;
            }
            float yaw = (float) (Mth.atan2(dz, dx) * (180.0D / Math.PI)) - 90.0F;
            this.dino.setYRot(this.rotlerp(this.dino.getYRot(), yaw, 12.0F));
            this.dino.yBodyRot = this.dino.getYRot();
            this.dino.yHeadRot = this.dino.getYRot();

            float speed = (float) (this.speedModifier * this.dino.getAttributeValue(Attributes.MOVEMENT_SPEED));
            this.dino.setSpeed(Mth.lerp(0.125F, this.dino.getSpeed(), speed));
            double accel = this.dino.getSpeed() * 0.09D;
            this.dino.setDeltaMovement(this.dino.getDeltaMovement().add(dx / dist * accel, dy / dist * accel, dz / dist * accel));
        }
    }

    // ------------------------------------------------------------------ sonic boom
    private boolean canBoomHit(LivingEntity e) {
        return e != this
                && e.isAlive()
                && !(e instanceof Warden)
                && !(e instanceof DinoWardenEntity)
                && EntitySelector.NO_CREATIVE_OR_SPECTATOR.test(e);
    }

    private void fireSonicBoom(@Nullable LivingEntity target) {
        if (!(this.level() instanceof ServerLevel server)) return;

        Vec3 fwd = Vec3.directionFromRotation(0.0F, this.yBodyRot);
        Vec3 from = this.position().add(fwd.x * 2.4D, 2.9D, fwd.z * 2.4D);
        Vec3 dir = (target != null)
                ? target.getEyePosition().subtract(from).normalize()
                : this.getViewVector(1.0F).normalize();

        Vec3 end = from.add(dir.scale(BOOM_RANGE));
        BlockHitResult hit = server.clip(new ClipContext(from, end, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, this));
        double length = hit.getType() == HitResult.Type.MISS ? BOOM_RANGE : hit.getLocation().distanceTo(from);

        for (int i = 1; i <= Mth.floor(length); i++) {
            Vec3 p = from.add(dir.scale(i));
            server.sendParticles(ParticleTypes.SONIC_BOOM, p.x, p.y, p.z, 1, 0.0D, 0.0D, 0.0D, 0.0D);
        }
        this.playSound(SoundEvents.WARDEN_SONIC_BOOM, 4.0F, 0.85F);

        AABB box = new AABB(from, from.add(dir.scale(length))).inflate(2.0D);
        for (LivingEntity e : server.getEntitiesOfClass(LivingEntity.class, box, this::canBoomHit)) {
            Vec3 center = e.getBoundingBox().getCenter();
            double along = Mth.clamp(center.subtract(from).dot(dir), 0.0D, length);
            Vec3 closest = from.add(dir.scale(along));
            if (closest.distanceTo(center) > 1.8D + e.getBbWidth() * 0.5D) continue;

            if (e.hurt(server.damageSources().sonicBoom(this), BOOM_DAMAGE)) {
                double res = 1.0D - e.getAttributeValue(Attributes.KNOCKBACK_RESISTANCE);
                e.push(dir.x * 2.5D * res, dir.y * 0.5D * res, dir.z * 2.5D * res);
                e.hurtMarked = true;
            }
        }
    }

    // ------------------------------------------------------------------ dano / agua / hitbox
    @Override
    public boolean hurt(DamageSource source, float amount) {
        // El Warden (y otros Dino Warden) no pueden danarlo
        if (source.getEntity() instanceof Warden || source.getEntity() instanceof DinoWardenEntity) return false;
        return super.hurt(source, amount);
    }

    @Override
    public boolean canBreatheUnderwater() { return true; }

    @Override
    protected float getStandingEyeHeight(Pose pose, EntityDimensions dimensions) { return 2.75F; }

    @Override
    public boolean removeWhenFarAway(double distanceToClosestPlayer) { return false; }

    @Override
    public void addAdditionalSaveData(CompoundTag tag) {
        super.addAdditionalSaveData(tag);
        tag.putInt("RoarCooldown", this.roarCooldown);
    }

    @Override
    public void readAdditionalSaveData(CompoundTag tag) {
        super.readAdditionalSaveData(tag);
        if (tag.contains("RoarCooldown")) this.roarCooldown = tag.getInt("RoarCooldown");
    }

    // ------------------------------------------------------------------ sonidos
    @Override protected SoundEvent getAmbientSound() { return ModSounds.AMBIENT.get(); }
    @Override protected SoundEvent getHurtSound(DamageSource source) { return ModSounds.HURT.get(); }
    @Override protected SoundEvent getDeathSound() { return ModSounds.DEATH.get(); }
    @Override public int getAmbientSoundInterval() { return 200; }

    @Override
    protected void playStepSound(BlockPos pos, BlockState state) {
        // El sonido, el polvo y el temblor de camara los dispara la animacion en cada pisada (StepShake).
        // Solo se usa el paso vanilla como respaldo cuando no hay animacion de caminar/correr.
    }

    // ------------------------------------------------------------------ GeckoLib
    @Override
    public void registerControllers(AnimatableManager.ControllerRegistrar controllers) {
        AnimationController<DinoWardenEntity> main = new AnimationController<>(this, "main", 4, this::predicate);
        // Keyframes "sound_effects" del animation.json: pisadas sincronizadas (solo se ejecuta en el cliente)
        main.setSoundKeyframeHandler(event -> {
            if (event.getAnimatable().level().isClientSide) {
                com.dinowarden.client.StepShake.onKeyframe(event.getAnimatable(), event.getKeyframeData().getSound());
            }
        });
        controllers.add(main);
    }

    private PlayState predicate(AnimationState<DinoWardenEntity> state) {
        switch (getAction()) {
            case ACT_ROAR:   return state.setAndContinue(ANIM_ROAR);
            case ACT_BITE:   return state.setAndContinue(ANIM_BITE);
            case ACT_BELLOW: return state.setAndContinue(ANIM_BELLOW);
            default: break;
        }
        if (this.isSwimmingMode()) return state.setAndContinue(ANIM_SWIM);
        if (state.isMoving()) return state.setAndContinue(this.isAggressive() ? ANIM_RUN : ANIM_WALK);
        return state.setAndContinue(ANIM_IDLE);
    }

    @Override
    public AnimatableInstanceCache getAnimatableInstanceCache() { return this.cache; }
}
