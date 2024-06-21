use std::{cmp, vec};


fn main() {
    let res = State {
        turn_count: 3
        , priority: Player::BMC
        , turn: Player::BMC
        , op_health: 23
        , bmc_health: 17
        , changeling: 0
        , changeling_tapped: 0
        , changeling_entered: 0
        , treasure: 2 // simulates the existence of peat bog while not having to specifically model it
        , cat: 2
        , cat_tapped: 1
        , ocelot_alive: 1
        , ocelot_tapped: 1
        , city_blessing: false 
        , legal_actions: vec![Action::MakeChangeling, Action::MakeTreasure, Action::MakeBoth],
    }.solve().to_string();

    println!("{}", res);
}

#[derive(Debug, Clone)]
struct State {
    turn_count: u32
    , priority: Player
    , turn: Player
    , op_health: i32
    , bmc_health: i32
    , changeling: u32
    , changeling_tapped: u32
    , changeling_entered: u32
    , treasure: u32
    , cat: u32
    , cat_tapped: u32
    , ocelot_alive: u32
    , ocelot_tapped: u32
    , city_blessing: bool
    , legal_actions: Vec<Action>
}

#[derive(Debug, Clone, Copy)]
enum Player {
    OP, BMC
}

impl Player {
    fn opponent(&self) -> Player {
        match self {
            Player::OP => Player::BMC,
            Player::BMC => Player::OP,
        }
    }

    fn equal(&self, other: Player) -> bool {
        match self {
            Player::OP => match other {
                Player::OP => true,
                Player::BMC => false,
            },
            Player::BMC => match other {
                Player::OP => false,
                Player::BMC => true,
            },
        }
    }

    fn to_string(&self) -> String {
        match self {
            Player::OP => "OP".to_string(),
            Player::BMC => "BMC".to_string(),
        }
    }
}

#[derive(Debug, Clone, Copy)]
enum Action {
    MakeChangeling, MakeTreasure, MakeBoth, AutoBlock,
    Pass, Attack, Block, Vault,
}

fn make_changeling( state: &State ) -> State {
    let mut ret = state.clone();
    ret.bmc_health = state.bmc_health - 3;
    ret.changeling = state.changeling + 1;
    ret.changeling_entered = 1;
    if state.changeling > 0 {
        ret.legal_actions = vec![Action::Attack, Action::Pass];
    } else {
        ret.legal_actions = vec![Action::Pass];
    }
    ret
}

fn make_treasure( state: &State ) -> State {
    let mut ret = state.clone();
    ret.bmc_health = state.bmc_health - 1;
    ret.treasure = state.treasure + 1;
    if state.changeling > 0 {
        ret.legal_actions = vec![Action::Attack, Action::Pass];
    } else {
        ret.legal_actions = vec![Action::Pass];
    }
    ret
}

fn make_both( state: &State ) -> State {
    let mut ret = state.clone();
    ret.bmc_health = state.bmc_health - 4;
    ret.changeling = state.changeling + 1;
    ret.changeling_entered = state.changeling_entered + 1;
    ret.treasure = state.treasure + 1;
    if state.changeling > 0 {
        ret.legal_actions = vec![Action::Attack, Action::Pass];
    } else {
        ret.legal_actions = vec![Action::Pass];
    }
    ret
}

fn vault( state: &State ) -> State {
    let mut ret = state.clone();
    ret.treasure -= 4u32;

    match state.turn {
        Player::OP => {
            let blockers = state.changeling - state.changeling_tapped;
            ret.bmc_health = state.bmc_health.checked_add_unsigned( 3 * blockers ).unwrap();
            ret.priority = Player::BMC;
            ret.legal_actions = vec![Action::AutoBlock];

            ret
        },
        Player::BMC => {
            ret.bmc_health = state.bmc_health.checked_add_unsigned( 3 * state.changeling_tapped ).unwrap();
            ret.priority = Player::OP;
            ret.legal_actions = vec![Action::Block];
            ret
            
        },
    }
}

fn pass( state: &State ) -> State {
   let mut ret = state.clone();

   match state.priority {
    Player::OP => {
        if state.ocelot_alive == 1  {
            ret.cat = state.cat + 1;
            if ret.cat >= 7 {
                ret.city_blessing = true;
            }

            if ret.city_blessing {
                ret.cat += 1;
            }
        }
        ret.changeling_tapped = 0;
        ret.priority = Player::BMC;
        ret.turn = Player::BMC;
        ret.legal_actions = vec![Action::MakeChangeling, Action::MakeTreasure, Action::MakeBoth];

        ret
    },
    Player::BMC => {
        ret.changeling_entered = 0;
        ret.cat_tapped = 0;
        ret.ocelot_tapped = 0;
        ret.op_health = state.op_health + 1;
        ret.priority = Player::OP;
        ret.turn_count = state.turn_count + 1;
        ret.turn = Player::OP;
        if state.cat >= state.changeling - state.changeling_tapped {
            ret.legal_actions = vec![Action::Attack, Action::Pass];
        } else {
            ret.legal_actions = vec![Action::Pass];
        }

        ret
    },
   }
}

fn attacks( state: &State ) -> Vec<State> {
   let mut ret: Vec<State> = vec![];

   match state.priority {
    Player::OP => {
        let min_attackers = 1 + state.changeling - state.changeling_tapped;
        for attackers in min_attackers..state.cat {
            let mut attack_no_ocelot = state.clone();
            attack_no_ocelot.cat_tapped = attackers;
            attack_no_ocelot.priority = Player::BMC;
            if state.treasure >= 4 {    
                attack_no_ocelot.legal_actions = vec![Action::AutoBlock, Action::Vault];
            } else {
                attack_no_ocelot.legal_actions = vec![Action::AutoBlock];
            }
            
            ret.push(attack_no_ocelot);

            if state.ocelot_alive == 1 {
                let mut attack_with_ocelot = state.clone();
                attack_with_ocelot.ocelot_tapped = 1;
                attack_with_ocelot.cat_tapped = attackers - 1;
                attack_with_ocelot.priority = Player::BMC;
                if state.treasure >= 4 {    
                    attack_with_ocelot.legal_actions = vec![Action::AutoBlock, Action::Vault];
                } else {
                    attack_with_ocelot.legal_actions = vec![Action::AutoBlock];
                }
                ret.push(attack_with_ocelot);
            }
            
        };
        if state.ocelot_alive == 1 {
            let mut all_out_attack = state.clone();
            all_out_attack.ocelot_tapped = 1;
            all_out_attack.cat_tapped = state.cat;
            all_out_attack.priority = Player::BMC;
            if state.treasure >= 4 {    
                all_out_attack.legal_actions = vec![Action::AutoBlock, Action::Vault];
            } else {
                all_out_attack.legal_actions = vec![Action::AutoBlock];
            }
            ret.push(all_out_attack);
        }

        ret
    },
    Player::BMC => {
        let mut ret: Vec<State> = vec![];
        let max_attackers = state.changeling - state.changeling_entered;
        for attackers in 1..max_attackers {
            let mut attack = state.clone();
            attack.changeling_tapped = attackers;
            attack.priority = Player::OP;
            attack.legal_actions = vec![Action::Block];

            ret.push( attack );

            if state.treasure >= 4 { 
                let mut attack_vault = state.clone();
                attack_vault.changeling_tapped = attackers;
                attack_vault.legal_actions = vec![Action::Vault];

                ret.push( attack_vault );
            }
        }
        ret
    },
   }
}

fn block( state: &State ) -> State {
   let mut ret = state.clone();

   match state.priority {
    Player::OP => {
        panic!("block is always a multi-option case for OP player, use blocks")
    },
    Player::BMC => {
        let mut blockers_to_apply =  state.changeling - state.changeling_tapped; 
        let damage: u32 = state.cat_tapped + state.ocelot_tapped - blockers_to_apply;
        ret.bmc_health = state.bmc_health.checked_sub_unsigned(damage).unwrap();

        if state.ocelot_tapped == 1u32 {
            ret.op_health = state.op_health + 1;
            if blockers_to_apply > 0 {
                ret.ocelot_alive = 0;
                blockers_to_apply -= 1;
            }
        }
        ret.cat = state.cat - blockers_to_apply; 
        ret.cat_tapped = state.cat_tapped - blockers_to_apply;
        ret.priority = Player::OP;
        ret.legal_actions = vec![Action::Pass];

        ret
    },
   }
}

fn blocks( state: &State) -> Vec<State> {
    let mut ret: Vec<State> = vec![];

    match state.priority {
        Player::OP => {
            ret.push( no_blocks( &(state.clone()) ) );
            // ASSUMPTION: not bothering to calc scenarios where the ocelot blocks yet, but I know it should be relevant
            // ASSUMPTION: also not yet exploring the combination of trade and chump

            // case trade // ASSUMPTION: if trading is optimal, trading to the maximum amount is optimal (might be wrong)
            let max_blocker_groups = ( state.cat - state.cat_tapped ) / 2;
            let max_blocks = cmp::min( max_blocker_groups, state.changeling_tapped);

            let mut trade = state.clone();
            trade.changeling = state.changeling - max_blocks;
            trade.changeling_tapped = state.changeling_tapped - max_blocks;
            trade.cat = state.cat - ( max_blocks * 2 );
            trade.op_health = state.op_health.checked_sub_unsigned( 3 * trade.changeling_tapped ).unwrap();
            trade.priority = Player::BMC;
            trade.legal_actions = vec![Action::Pass];

            ret.push( trade );

            // case chump

            let max_chumpers = state.cat - state.cat_tapped;
            let max_chumps = cmp::min( max_chumpers, state.changeling_tapped );
            if max_chumps > 0 { 
                for chumps in 1..max_chumps {
                    let unblocked =  state.changeling_tapped - chumps;
                    let mut chump = state.clone();
                    chump.cat = state.cat - chumps;
                    chump.op_health = state.op_health.checked_sub_unsigned( 3 * unblocked ).unwrap();
                    chump.priority = Player::BMC;
                    chump.legal_actions = vec![Action::Pass];

                    ret.push( chump );

                }
            }

            ret
        },
        Player::BMC => {
            panic!("blocks are deterministic for BMC player, use block")
        },
    }

}

fn no_blocks( state: &State ) -> State {
    let mut ret = state.clone();
    
    match state.priority {
        Player::OP => {
            ret.op_health = state.op_health.checked_sub( (3 * state.changeling_tapped).try_into().unwrap() ).unwrap();
            ret.priority = Player::BMC;
            ret.legal_actions = vec![Action::Pass];
            
            ret
        },
        Player::BMC => {
           panic!("the block process is always deterministically better for BMC player") 
        },
    }
}

impl State {
    fn solve( &self ) -> Player {
       //self.print();

        if self.op_health <= 0 {
            //println!("BMC wins");
            return Player::BMC
        }

        if self.bmc_health <= 0 {
            //println!("OP wins");
            return Player::OP
        }

        // turns out I need a stop condition in case i go down the "always pass" route
        if self.ocelot_alive == 0 && self.changeling > self.cat {
            return Player::BMC
        }

        if self.city_blessing {
            return Player::OP;
        }

        if self.turn_count > 17 {
            return Player::BMC
        }


        <Vec<Action> as Clone>::clone(&self.legal_actions).into_iter()
            .fold( self.priority.opponent(), |winner_in_current_line, action| {
                if winner_in_current_line.equal( self.priority ) {
                    return self.priority
                }
                return match action {
                    Action::MakeChangeling => make_changeling(self).solve(),
                    Action::MakeTreasure => make_treasure(self).solve(),
                    Action::MakeBoth => make_both(self).solve(),
                    Action::Pass => pass(self).solve(),
                    Action::Attack => attacks( self ).into_iter()
                        .fold( self.priority.opponent(),|winner_in_current_line, new_line_of_play| {
                            if winner_in_current_line.equal( self.priority ) {
                                return self.priority
                            }
                            return new_line_of_play.solve()

                        }),
                    Action::AutoBlock => block(self).solve(),
                    Action::Block => blocks(self).into_iter()
                        .fold( self.priority.opponent(),|winner_in_current_line, new_line_of_play| {
                            if winner_in_current_line.equal( self.priority ) {
                                return self.priority
                            }
                            return new_line_of_play.solve()

                        }),
                    Action::Vault => vault(self).solve()
                }
            } 
        )

    }

    fn print(&self) {
        print!("{}{}: {}-{}; {} changelings, {} treasures, {} cats, {} ocelot "
            , self.turn_count
            , self.turn.to_string()
            , self.op_health
            , self.bmc_health
            , self.changeling
            , self.treasure
            , self.cat
            , self.ocelot_alive
        )
    }
}