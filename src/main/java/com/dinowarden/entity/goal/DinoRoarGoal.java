package com.dinowarden.entity.goal;

import com.dinowarden.entity.DinoWardenEntity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.goal.Goal;

import java.util.EnumSet;

/** Rugido con sonic boom: se activa contra un objetivo a media distancia con linea de vision. */
public class DinoRoarGoal extends Goal {
    private final DinoWardenEntity dino;

    public DinoRoarGoal(DinoWardenEntity dino) {
        this.dino = dino;
        this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
    }

    @Override
    public boolean canUse() {
        LivingEntity target = dino.getTarget();
        if (target == null || !target.isAlive() || !dino.canStartRoar()) return false;
        double d = dino.distanceToSqr(target);
        return d > 6.0D * 6.0D && d < 26.0D * 26.0D
                && dino.hasLineOfSight(target)
                && dino.getRandom().nextInt(20) == 0;
    }

    @Override
    public boolean canContinueToUse() {
        return dino.getAction() == DinoWardenEntity.ACT_ROAR;
    }

    @Override
    public void start() {
        dino.getNavigation().stop();
        dino.beginRoar();
    }

    @Override
    public boolean requiresUpdateEveryTick() { return true; }
}
