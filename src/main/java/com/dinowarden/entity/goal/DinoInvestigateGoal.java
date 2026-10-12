package com.dinowarden.entity.goal;

import com.dinowarden.entity.DinoWardenEntity;
import net.minecraft.world.entity.ai.goal.Goal;
import net.minecraft.world.phys.Vec3;

import java.util.EnumSet;

/** Va hacia el lugar de donde vino un sonido (pasos, bloques, explosiones...) cuando aun no tiene objetivo. */
public class DinoInvestigateGoal extends Goal {
    private final DinoWardenEntity dino;
    private int giveUp;

    public DinoInvestigateGoal(DinoWardenEntity dino) {
        this.dino = dino;
        this.setFlags(EnumSet.of(Flag.MOVE));
    }

    @Override
    public boolean canUse() {
        return dino.getTarget() == null && dino.getHeardPos() != null && dino.getAction() == DinoWardenEntity.ACT_NONE;
    }

    @Override
    public boolean canContinueToUse() {
        return dino.getTarget() == null && dino.getHeardPos() != null
                && dino.getAction() == DinoWardenEntity.ACT_NONE
                && this.giveUp > 0 && !dino.getNavigation().isDone();
    }

    @Override
    public void start() {
        Vec3 p = dino.getHeardPos();
        this.giveUp = 200;
        if (p == null || !dino.getNavigation().moveTo(p.x, p.y, p.z, 1.0D)) dino.clearHeardPos();
    }

    @Override
    public void tick() { this.giveUp--; }

    @Override
    public void stop() {
        dino.clearHeardPos();
        dino.getNavigation().stop();
    }
}
