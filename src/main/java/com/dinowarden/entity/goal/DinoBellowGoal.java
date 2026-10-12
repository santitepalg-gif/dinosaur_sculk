package com.dinowarden.entity.goal;

import com.dinowarden.entity.DinoWardenEntity;
import net.minecraft.world.entity.ai.goal.Goal;

import java.util.EnumSet;

/** Bramido estilo cocodrilo: solo en el agua y sin objetivo. */
public class DinoBellowGoal extends Goal {
    private final DinoWardenEntity dino;

    public DinoBellowGoal(DinoWardenEntity dino) {
        this.dino = dino;
        // sin Flag.JUMP para no pelear con FloatGoal (que lo mantiene a flote)
        this.setFlags(EnumSet.of(Flag.MOVE, Flag.LOOK));
    }

    @Override
    public boolean canUse() {
        return dino.getTarget() == null
                && dino.canStartBellow()
                && dino.getRandom().nextInt(80) == 0;
    }

    @Override
    public boolean canContinueToUse() {
        return dino.getAction() == DinoWardenEntity.ACT_BELLOW;
    }

    @Override
    public void start() {
        dino.getNavigation().stop();
        dino.beginBellow();
    }
}
