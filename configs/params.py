# Parâmetros para construção da matriz de demanda (modelo gravitacional)
GAMMA = 0.01
T = 100000

# Parâmetros do modelo de custo de coleta
RHO_COL = 0       # ρ^col: pacotes coletados por parada
Q_COL = 20100        # Q^col: capacidade do veículo de coleta, em pacotes 
BETA_COL = 5.15    # β^col: coeficiente de aproximação contínua
C_COL = 1.80       # c^col: custo operacional por km do veículo de coleta, em R$/km

# Parâmetros do modelo de custo de entrega
RHO_ENT = 0        # ρ^ENT: pacotes entregues por parada
Q_ENT = 20100        # Q^ENT: capacidade do veículo de entrega, em pacotes 
BETA_ENT = 5.15    # β^ENT: coeficiente de aproximação contínua
C_ENT = 1.80       # c^ENT: custo operacional por km do veículo de entrega, em R$/km

# Parâmetros do modelo de custo entre hubs
Q_HUB = 50000                 # Q^HUB: capacidade do veículo entre hubs, em pacotes
CKM_HUB = 7.010                # ckm^hub: custo operacional por km do veículo de transporte entre hubs, em R$/km
C_HUB = CKM_HUB / Q_HUB        # c^hub: custo operacional por km do veículo de transporte entre hubs, em R$/km * pacote


#0,90 → malha euclidiana (rodovias relativamente diretas)
#1,15 → malha tipo grade/Manhattan
#0,712–0,80 → piso teórico assintótico (malha viária super otimizada)

#       MAX "Demanda_Municipio_Intermediaria": 20062.29332935487,
#       MAX "Demanda_Municipio_Imediata": 19941.4059491877