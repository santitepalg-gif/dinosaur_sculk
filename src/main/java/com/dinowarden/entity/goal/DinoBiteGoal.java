package com.dinowarden.entity.goal;

import com.dinowarden.entity.DinoWardenEntity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.goal.MeleeAttackGoal;

/** Persigue y muerde: dispara la animacion "bite" y el dano se aplica en el tick BITE_HIT_TICK. */
public class DinoBiteGoal extends MeleeAttackGoal {
    private final DinoWardenEntity dino;

    public DinoBiteGoal(DinoWardenEntity dino, double speed, boolean followEvenIfNotSeen) {
        super(dino, speed, followEvenIfNotSeen);
        this.dino = dino;
    }

    @Override
    protected void checkAndPerformAttack(LivingEntity target, double distToTargetSqr) {
        if (distToTargetSqr <= this.getAttackReachSqr(target)
                && this.getTicksUntilNextAttack() <= 0
                && dino.getAction() == DinoWardenEntity.ACT_NONE) {
            this.resetAttackCooldown();
            dino.beginBite();
        }
    }
}
