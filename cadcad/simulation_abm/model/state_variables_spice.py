"""
Model initial state.
"""

# Dependencies

import random
import uuid
import logging
log = logging.getLogger('simstate')

from enforce_typing import enforce_types # type: ignore[import]
from typing import Set

from .parts.agents import MinterAgents
from .parts.agents.BaseAgent import BaseAgent
from .parts.agents.AgentDict import AgentDict
from .parts.agents.GrantGivingAgent import GrantGivingAgent
from .parts.agents.GrantTakingAgent import GrantTakingAgent
from .parts.agents.MarketplacesAgent import MarketplacesAgent
from .parts.agents.DataecosystemAgent import DataecosystemAgent
from .parts.agents.OCEANBurnerAgent import OCEANBurnerAgent
from .parts.agents.StakerspeculatorAgent import StakerspeculatorAgent

from .parts.agents.RouterAgent import RouterAgent
from .parts.agents.EWPublisherAgent import EWPublisherAgent

from cadcad.stats.Kpis import Kpis
from cadcad.engine import SimStrategy
from .parts.util import mathutil, valuation
from .parts.util.mathutil import Range
from .parts.util.constants import *

import numpy as np
from typing import Tuple, List, Dict
from itertools import cycle
from enum import Enum


### World size
N = 200
M = 20
INITIAL_CROWD = 1

### Initial agent count
PERSON_COUNT = 300
ATTRACTION_COUNT = 10
PROPOSAL_COUNT = 10

MAX_ATTRACTION_CAPACITY = 5
MAX_TIMESTEPS = 20
MAX_DURATION = 5

## yet to be implemented
agent_probabilities = [0.7,0.75,0.8,0.85,0.9,0.95]

ss = SimStrategy()

#main
tick = 0

#used to manage names
_next_free_marketplace_number = 0

#used to add agents
_marketplace_tick_previous_add = 0

#as ecosystem improves, these parameters may change / improve
_marketplace_percent_toll_to_ocean = 0.002 #magic number

initial_kpis = {
    '_percent_burn': 0.05, 
    '_total_OCEAN_minted': 0.0,
    '_total_OCEAN_burned': 0.0,   
    '_total_OCEAN_burned_USD': 0.0,  
    '_speculation_valuation': 5e6,  
    '_percent_increase_speculation_valuation_per_s': 0.10 / S_PER_YEAR,  
    }


# init agents
initial_agents = AgentDict()

#Instantiate and connnect agent instances. "Wire up the circuit"
new_agents: Set[BaseAgent] = set()

#FIXME: replace MarketplacesAgent with DataecosystemAgent, when ready
new_agents.add(MarketplacesAgent(
    name = "marketplaces1", USD=0.0, OCEAN=0.0,
    toll_agent_name = "opc_address",
    n_marketplaces = float(ss.init_n_marketplaces),
    revenue_per_marketplace_per_s = 2e3 / S_PER_MONTH, #magic number
    time_step = 0,
    ))


new_agents.add(DataecosystemAgent(
    name = "dataecosystem1", USD=0.0, OCEAN=0.0
))

new_agents.add(RouterAgent(
    name = "opc_address", USD=0.0, OCEAN=0.0,
    receiving_agents = {"ocean_dao" : self.percentToOceanDao,
                        "opc_burner" : self.percentToBurn}))

new_agents.add(OCEANBurnerAgent(
    name = "opc_burner", USD=0.0, OCEAN=0.0))

#func = MinterAgents.ExpFunc(H=4.0)
func = MinterAgents.RampedExpFunc(H=4.0,                                 #magic number
                                    T0=0.5, T1=1.0, T2=1.4, T3=3.0,        #""
                                    M1=0.10, M2=0.25, M3=0.50)             #""
new_agents.add(MinterAgents.OCEANFuncMinterAgent(
    name = "ocean_51",
    receiving_agent_name = "ocean_dao",
    total_OCEAN_to_mint = UNMINTED_OCEAN_SUPPLY,
    s_between_mints = S_PER_DAY,
    func = func))

new_agents.add(GrantGivingAgent(
    name = "opf_treasury_for_ocean_dao",
    USD = 0.0, OCEAN = OPF_TREASURY_OCEAN_FOR_OCEAN_DAO,                 #magic number
    receiving_agent_name = "ocean_dao",
    s_between_grants = S_PER_MONTH, n_actions = 12 * 3))                 #""

new_agents.add(GrantGivingAgent(
    name = "opf_treasury_for_opf_mgmt",
    USD = OPF_TREASURY_USD, OCEAN = OPF_TREASURY_OCEAN_FOR_OPF_MGMT,     #magic number
    receiving_agent_name = "opf_mgmt",
    s_between_grants = S_PER_MONTH, n_actions = 12 * 3))                 #""

new_agents.add(GrantGivingAgent(
    name = "bdb_treasury",
    USD = BDB_TREASURY_USD, OCEAN = BDB_TREASURY_OCEAN,                  #magic number
    receiving_agent_name = "bdb_mgmt",
    s_between_grants = S_PER_MONTH, n_actions = 17))                     #""

new_agents.add(RouterAgent(
    name = "ocean_dao",
    receiving_agents = {"opc_workers" : funcOne},
    USD=0.0, OCEAN=0.0))

new_agents.add(RouterAgent(
    name = "opf_mgmt",
    receiving_agents = {"opc_workers" : funcOne},
    USD=0.0, OCEAN=0.0))
                
new_agents.add(RouterAgent(
    name = "bdb_mgmt",
    receiving_agents = {"bdb_workers" : funcOne},
    USD=0.0, OCEAN=0.0))

new_agents.add(GrantTakingAgent(
    name = "opc_workers", USD=0.0, OCEAN=0.0))

new_agents.add(GrantTakingAgent(
    name = "bdb_workers", USD=0.0, OCEAN=0.0))

for agent in new_agents:
    initial_agents[agent.name] = agent

genesis_states = {
    'agents': initial_agents,
    'stats': initial_kpis,
    '_next_free_marketplace_number': 0,
    '_marketplace_tick_previous_add': 0,
    '_marketplace_percent_toll_to_ocean': 0.002
}